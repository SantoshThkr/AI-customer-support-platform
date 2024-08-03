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

export interface AISource {
  document_id: number
  document_title: string
  section: string | null
}

export interface CopilotTurn {
  role: 'user' | 'assistant'
  content: string
}
