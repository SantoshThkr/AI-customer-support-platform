import type { TicketEvent } from '../../types/ticket'
import { formatDateTime, humanize } from '../../utils/format'

function describe(event: TicketEvent) {
  const actor = event.user?.name ?? 'System'
  const meta = event.metadata
  switch (event.event_type) {
    case 'TICKET_CREATED':
      return `${actor} opened the ticket`
    case 'STATUS_CHANGED':
      return `${actor} changed status from ${humanize(String(meta.from))} to ${humanize(String(meta.to))}`
    case 'PRIORITY_CHANGED':
      return `${actor} changed priority from ${humanize(String(meta.from))} to ${humanize(String(meta.to))}`
    case 'CATEGORY_CHANGED':
      return `${actor} set category to ${humanize(String(meta.to))}`
    case 'TICKET_ASSIGNED':
      return meta.agent_name ? `${actor} assigned the ticket to ${meta.agent_name}` : `${actor} unassigned the ticket`
    case 'MESSAGE_ADDED':
      return meta.is_internal ? `${actor} added an internal note` : `${actor} replied`
    case 'AI_ANALYSIS_COMPLETED':
      return 'AI analysis completed'
    case 'TICKET_RESOLVED':
      return 'Ticket marked as resolved'
    default:
      return humanize(event.event_type)
  }
}

export default function TicketHistory({ events }: { events: TicketEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-slate-500">No history yet.</p>
  }
  return (
    <ol className="space-y-2 text-sm">
      {events.map((event) => (
        <li key={event.id} className="flex flex-wrap justify-between gap-x-4 border-l-2 border-slate-200 pl-3">
          <span className="text-slate-700">{describe(event)}</span>
          <time className="text-xs text-slate-400" dateTime={event.created_at}>
            {formatDateTime(event.created_at)}
          </time>
        </li>
      ))}
    </ol>
  )
}
