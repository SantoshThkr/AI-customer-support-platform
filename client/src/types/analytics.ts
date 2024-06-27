import type { TicketPriority, TicketStatus } from './ticket'

export interface Analytics {
  total_tickets: number
  open_tickets: number
  resolved_tickets: number
  average_resolution_hours: number | null
  by_status: Record<TicketStatus, number>
  by_category: { category: string | null; count: number }[]
  by_priority: { priority: TicketPriority; count: number }[]
  created_last_14_days: { date: string; count: number }[]
}
