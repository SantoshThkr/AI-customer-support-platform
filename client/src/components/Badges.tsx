import type { Sentiment, TicketPriority, TicketStatus } from '../types/ticket'
import { humanize } from '../utils/format'

const STATUS_STYLES: Record<TicketStatus, string> = {
  OPEN: 'bg-sky-100 text-sky-800',
  IN_PROGRESS: 'bg-amber-100 text-amber-800',
  WAITING_FOR_CUSTOMER: 'bg-violet-100 text-violet-800',
  RESOLVED: 'bg-emerald-100 text-emerald-800',
  CLOSED: 'bg-slate-200 text-slate-700',
}

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  LOW: 'bg-slate-100 text-slate-700',
  MEDIUM: 'bg-blue-50 text-blue-700',
  HIGH: 'bg-orange-100 text-orange-800',
  URGENT: 'bg-red-100 text-red-800',
}

const SENTIMENT_STYLES: Record<Sentiment, string> = {
  POSITIVE: 'bg-emerald-50 text-emerald-700',
  NEUTRAL: 'bg-slate-100 text-slate-700',
  NEGATIVE: 'bg-rose-100 text-rose-800',
}

const base = 'inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium'

export function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`${base} ${STATUS_STYLES[status]}`}>{humanize(status)}</span>
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return <span className={`${base} ${PRIORITY_STYLES[priority]}`}>{humanize(priority)}</span>
}

export function SentimentBadge({ sentiment }: { sentiment: Sentiment }) {
  return <span className={`${base} ${SENTIMENT_STYLES[sentiment]}`}>{humanize(sentiment)}</span>
}
