import { useState } from 'react'
import { useCategories } from '../../hooks/useCategories'
import { updateTicket } from '../../services/tickets'
import type { UpdateTicketInput } from '../../services/tickets'
import { TICKET_PRIORITIES, TICKET_STATUSES } from '../../types/ticket'
import type { Ticket, TicketPriority, TicketStatus } from '../../types/ticket'
import { getErrorMessage } from '../../utils/errors'
import { humanize } from '../../utils/format'
import Alert from '../Alert'

interface Props {
  ticket: Ticket
  canEdit: boolean
  onUpdated: (ticket: Ticket) => void
}

export default function TicketProperties({ ticket, canEdit, onUpdated }: Props) {
  const { categories } = useCategories()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const save = async (changes: UpdateTicketInput) => {
    setSaving(true)
    setError(null)
    try {
      onUpdated(await updateTicket(ticket.id, changes))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      {error && <Alert>{error}</Alert>}
      <div>
        <label htmlFor="ticket-status" className="label">
          Status
        </label>
        <select
          id="ticket-status"
          className="input"
          value={ticket.status}
          disabled={!canEdit || saving}
          onChange={(event) => save({ status: event.target.value as TicketStatus })}
        >
          {TICKET_STATUSES.map((value) => (
            <option key={value} value={value}>
              {humanize(value)}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="ticket-priority" className="label">
          Priority
        </label>
        <select
          id="ticket-priority"
          className="input"
          value={ticket.priority}
          disabled={!canEdit || saving}
          onChange={(event) => save({ priority: event.target.value as TicketPriority })}
        >
          {TICKET_PRIORITIES.map((value) => (
            <option key={value} value={value}>
              {humanize(value)}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="ticket-category" className="label">
          Category
        </label>
        <select
          id="ticket-category"
          className="input"
          value={ticket.category ?? ''}
          disabled={!canEdit || saving}
          onChange={(event) => event.target.value && save({ category: event.target.value })}
        >
          {!ticket.category && <option value="">Uncategorized</option>}
          {ticket.category && !categories.some((category) => category.code === ticket.category) && (
            <option value={ticket.category}>{ticket.category}</option>
          )}
          {categories.map((category) => (
            <option key={category.code} value={category.code}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
