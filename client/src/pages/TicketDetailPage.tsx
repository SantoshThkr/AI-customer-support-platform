import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import Alert from '../components/Alert'
import { PriorityBadge, SentimentBadge, StatusBadge } from '../components/Badges'
import Spinner from '../components/Spinner'
import AIActions from '../components/ticket/AIActions'
import AssignControl from '../components/ticket/AssignControl'
import KnowledgePanel from '../components/ticket/KnowledgePanel'
import Conversation from '../components/ticket/Conversation'
import CopilotPanel from '../components/ticket/CopilotPanel'
import ReplyBox from '../components/ticket/ReplyBox'
import SuggestionPanel from '../components/ticket/SuggestionPanel'
import TicketHistory from '../components/ticket/TicketHistory'
import TicketProperties from '../components/ticket/TicketProperties'
import { useAuth } from '../context/AuthContext'
import { useAgents } from '../hooks/useAgents'
import { useAIStatus } from '../hooks/useAIStatus'
import { useCategories } from '../hooks/useCategories'
import { addMessage, getTicket, listMessages, listTicketEvents, updateTicket } from '../services/tickets'
import type { Ticket, TicketEvent, TicketMessage } from '../types/ticket'
import { getErrorMessage } from '../utils/errors'
import { formatDateTime } from '../utils/format'

export default function TicketDetailPage() {
  const ticketId = Number(useParams().id)
  const location = useLocation()
  const { user } = useAuth()
  const { labelFor } = useCategories()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [events, setEvents] = useState<TicketEvent[]>([])
  const [messages, setMessages] = useState<TicketMessage[]>([])
  const [draft, setDraft] = useState('')
  const [noteMode, setNoteMode] = useState(false)
  const [draftFromAI, setDraftFromAI] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const isStaff = user?.role === 'AGENT' || user?.role === 'ADMIN'
  const agents = useAgents(isStaff)
  const aiStatus = useAIStatus(isStaff)
  const justCreated = Boolean((location.state as { created?: boolean } | null)?.created)

  const refreshEvents = useCallback(async () => {
    setEvents(await listTicketEvents(ticketId))
  }, [ticketId])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([getTicket(ticketId), listMessages(ticketId), listTicketEvents(ticketId)])
      .then(([ticketData, messageData, eventData]) => {
        if (cancelled) return
        setTicket(ticketData)
        setMessages(messageData)
        setEvents(eventData)
      })
      .catch((err) => !cancelled && setError(getErrorMessage(err, 'Could not load the ticket')))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [ticketId])

  const handleTicketUpdated = (updated: Ticket) => {
    setTicket(updated)
    refreshEvents().catch(() => undefined)
  }

  const reloadTicket = async () => {
    const [ticketData, eventData] = await Promise.all([getTicket(ticketId), listTicketEvents(ticketId)])
    setTicket(ticketData)
    setEvents(eventData)
  }

  const applySuggestion = (text: string) => {
    setDraft(text)
    setNoteMode(false)
    setDraftFromAI(true)
  }

  const sendMessage = async (text: string, isInternal: boolean) => {
    const message = await addMessage(ticketId, text, isInternal)
    setMessages((current) => [...current, message])
    setDraftFromAI(false)
    // A customer reply can reopen the ticket, so refresh the status and history.
    await reloadTicket()
  }

  const closeTicket = async () => {
    if (!ticket) return
    setActionError(null)
    try {
      handleTicketUpdated(await updateTicket(ticket.id, { status: 'CLOSED' }))
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  if (loading) {
    return <Spinner label="Loading ticket…" />
  }
  if (error || !ticket || !user) {
    return (
      <div className="space-y-4">
        <Alert>{error ?? 'Ticket not found'}</Alert>
        <Link to="/dashboard" className="text-sm text-indigo-600 hover:underline">
          Back to dashboard
        </Link>
      </div>
    )
  }

  const canWorkOn =
    user.role === 'ADMIN' || (user.role === 'AGENT' && (!ticket.assigned_agent || ticket.assigned_agent.id === user.id))
  const isClosed = ticket.status === 'CLOSED'

  return (
    <div className="space-y-4">
      {justCreated && <Alert kind="success">Your ticket has been submitted. We'll get back to you soon.</Alert>}

      <div>
        <Link to={isStaff ? '/dashboard' : '/tickets'} className="text-sm text-indigo-600 hover:underline">
          ← Back to tickets
        </Link>
        <h1 className="mt-2 text-xl font-semibold">
          <span className="mr-2 text-slate-400">#{ticket.id}</span>
          {ticket.subject}
        </h1>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
          <StatusBadge status={ticket.status} />
          <PriorityBadge priority={ticket.priority} />
          {isStaff && <span>{labelFor(ticket.category)}</span>}
          <span>· Opened {formatDateTime(ticket.created_at)}</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          {isStaff && ticket.ai_summary && (
            <section className="card border-indigo-100 bg-indigo-50/40 p-4">
              <div className="mb-1 flex items-center justify-between gap-2">
                <h2 className="text-sm font-semibold text-indigo-900">AI summary</h2>
                {ticket.ai_sentiment && <SentimentBadge sentiment={ticket.ai_sentiment} />}
              </div>
              <p className="text-sm text-slate-700">{ticket.ai_summary}</p>
            </section>
          )}

          <section>
            <h2 className="sr-only">Conversation</h2>
            <Conversation ticket={ticket} messages={messages} />
          </section>

          {isStaff && canWorkOn && aiStatus?.available && (
            <SuggestionPanel ticketId={ticket.id} onUse={applySuggestion} />
          )}

          {isStaff || !isClosed ? (
            <ReplyBox
              draft={draft}
              onDraftChange={(value) => {
                setDraft(value)
                if (!value) setDraftFromAI(false)
              }}
              onSend={sendMessage}
              noteMode={noteMode}
              onNoteModeChange={setNoteMode}
              allowInternal={isStaff}
              canReply={!isStaff || canWorkOn}
              disabledReason="This ticket is assigned to another agent. You can still leave an internal note."
              notice={draftFromAI ? 'This draft was written by AI. Review and edit it before sending.' : undefined}
            />
          ) : (
            <Alert kind="info">This ticket is closed. If you still need help, please open a new ticket.</Alert>
          )}

          <section className="card p-4">
            <h2 className="mb-3 text-sm font-semibold">History</h2>
            <TicketHistory events={events} />
          </section>
        </div>

        <aside className="space-y-4">
          <section className="card space-y-3 p-4">
            <h2 className="text-sm font-semibold">Details</h2>
            {isStaff ? (
              <>
                {!canWorkOn && (
                  <Alert kind="info">Assigned to {ticket.assigned_agent?.name}. Only they or an admin can change it.</Alert>
                )}
                <AssignControl
                  ticket={ticket}
                  currentUser={user}
                  agents={agents}
                  canEdit={canWorkOn}
                  onUpdated={handleTicketUpdated}
                />
                <TicketProperties ticket={ticket} canEdit={canWorkOn} onUpdated={handleTicketUpdated} />
              </>
            ) : (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-500">Status</dt>
                  <dd>
                    <StatusBadge status={ticket.status} />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Assigned to</dt>
                  <dd>{ticket.assigned_agent?.name ?? 'Waiting for an agent'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Last updated</dt>
                  <dd>{formatDateTime(ticket.updated_at)}</dd>
                </div>
                {actionError && <Alert>{actionError}</Alert>}
                {!isClosed && (
                  <button type="button" className="btn-secondary w-full" onClick={closeTicket}>
                    Close ticket
                  </button>
                )}
              </dl>
            )}
          </section>

          {isStaff && (
            <section className="card space-y-3 p-4">
              <h2 className="text-sm font-semibold">AI assistant</h2>
              <AIActions ticketId={ticket.id} status={aiStatus} onChanged={() => reloadTicket().catch(() => undefined)} />
            </section>
          )}

          {isStaff && aiStatus?.available && (
            <section className="card space-y-3 p-4">
              <h2 className="text-sm font-semibold">Ask the assistant</h2>
              <CopilotPanel ticketId={ticket.id} />
            </section>
          )}

          {isStaff && (
            <section className="card space-y-3 p-4">
              <h2 className="text-sm font-semibold">Knowledge base</h2>
              <KnowledgePanel initialQuery={ticket.subject} />
            </section>
          )}
        </aside>
      </div>
    </div>
  )
}
