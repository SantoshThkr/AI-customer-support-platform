import type { TicketPriority, TicketStatus } from './ticket'

export type AIOperation = 'CLASSIFICATION' | 'SUMMARY' | 'SUGGESTED_RESPONSE' | 'COPILOT' | 'EMBEDDING'

export interface Analytics {
  total_tickets: number
  open_tickets: number
  resolved_tickets: number
  average_resolution_hours: number | null
  by_status: Record<TicketStatus, number>
  by_category: { category: string | null; count: number }[]
  by_priority: { priority: TicketPriority; count: number }[]
  created_last_14_days: { date: string; count: number }[]
  ai_requests_last_30_days: number
}

export interface UsageTotals {
  requests: number
  input_tokens: number
  output_tokens: number
}

export interface AIUsageReport {
  days: number
  totals: UsageTotals
  requests_without_token_counts: number
  by_operation: (UsageTotals & { operation: AIOperation })[]
  by_model: (UsageTotals & { model: string })[]
  by_day: { date: string; count: number }[]
  top_users: { user_id: number | null; name: string; requests: number }[]
  recent: {
    id: number
    operation: AIOperation
    model: string
    input_tokens: number | null
    output_tokens: number | null
    user_name: string | null
    ticket_id: number | null
    created_at: string
  }[]
}
