import type { Ticket, TicketMessage } from '../../types/ticket'
import { formatDateTime } from '../../utils/format'

function bubbleStyle(message: TicketMessage, customerId: number) {
  if (message.is_internal) {
    return { wrapper: 'justify-start', bubble: 'border-amber-200 bg-amber-50', label: 'Internal note' }
  }
  if (message.sender.id === customerId) {
    return { wrapper: 'justify-start', bubble: 'border-slate-200 bg-white', label: 'Customer' }
  }
  return { wrapper: 'justify-end', bubble: 'border-indigo-100 bg-indigo-50', label: 'Support' }
}

export default function Conversation({ ticket, messages }: { ticket: Ticket; messages: TicketMessage[] }) {
  return (
    <ol className="space-y-3" aria-label="Conversation">
      <li className="flex justify-start">
        <article className="w-full rounded-lg border border-slate-200 bg-white p-4 sm:w-11/12">
          <header className="mb-2 flex flex-wrap items-baseline justify-between gap-2 text-xs text-slate-500">
            <span>
              <span className="font-semibold text-slate-800">{ticket.customer.name}</span> · Customer
            </span>
            <time dateTime={ticket.created_at}>{formatDateTime(ticket.created_at)}</time>
          </header>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{ticket.description}</p>
        </article>
      </li>
      {messages.map((message) => {
        const style = bubbleStyle(message, ticket.customer.id)
        return (
          <li key={message.id} className={`flex ${style.wrapper}`} data-testid={message.is_internal ? 'internal-note' : 'message'}>
            <article className={`w-full rounded-lg border p-4 sm:w-11/12 ${style.bubble}`}>
              <header className="mb-2 flex flex-wrap items-baseline justify-between gap-2 text-xs text-slate-500">
                <span>
                  <span className="font-semibold text-slate-800">{message.sender.name}</span> · {style.label}
                </span>
                <time dateTime={message.created_at}>{formatDateTime(message.created_at)}</time>
              </header>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.message}</p>
            </article>
          </li>
        )
      })}
    </ol>
  )
}
