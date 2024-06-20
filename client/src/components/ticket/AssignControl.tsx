import { useState } from 'react'
import { assignTicket } from '../../services/tickets'
import type { Ticket } from '../../types/ticket'
import type { User, UserBrief } from '../../types/user'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'

interface Props {
  ticket: Ticket
  currentUser: User
  agents: UserBrief[]
  canEdit: boolean
  onUpdated: (ticket: Ticket) => void
}

export default function AssignControl({ ticket, currentUser, agents, canEdit, onUpdated }: Props) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const assign = async (agentId: number | null) => {
    setSaving(true)
    setError(null)
    try {
      onUpdated(await assignTicket(ticket.id, agentId))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const assignedId = ticket.assigned_agent?.id ?? null

  return (
    <div className="space-y-2">
      <label htmlFor="assignee" className="label">
        Assigned agent
      </label>
      <select
        id="assignee"
        className="input"
        value={assignedId ?? ''}
        disabled={!canEdit || saving}
        onChange={(event) => assign(event.target.value ? Number(event.target.value) : null)}
      >
        <option value="">Unassigned</option>
        {ticket.assigned_agent && !agents.some((agent) => agent.id === assignedId) && (
          <option value={ticket.assigned_agent.id}>{ticket.assigned_agent.name}</option>
        )}
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name}
          </option>
        ))}
      </select>
      {canEdit && assignedId !== currentUser.id && (
        <button type="button" className="btn-secondary w-full" disabled={saving} onClick={() => assign(currentUser.id)}>
          Assign to me
        </button>
      )}
      {error && <Alert>{error}</Alert>}
    </div>
  )
}
