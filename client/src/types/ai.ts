import type { Sentiment, TicketPriority } from './ticket'

export interface AIStatus {
  available: boolean
  reason: string | null
}

export interface TicketAnalysis {
  category: string
  priority: TicketPriority
  sentiment: Sentiment
  summary: string
}

export interface SystemSettings {
  ai_enabled: boolean
  auto_analyze_tickets: boolean
}
