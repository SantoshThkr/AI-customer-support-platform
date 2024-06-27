import type { UserBrief } from './user'

export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'WAITING_FOR_CUSTOMER' | 'RESOLVED' | 'CLOSED'
export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT'
export type Sentiment = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'

export const TICKET_STATUSES: TicketStatus[] = ['OPEN', 'IN_PROGRESS', 'WAITING_FOR_CUSTOMER', 'RESOLVED', 'CLOSED']
export const TICKET_PRIORITIES: TicketPriority[] = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']

export interface Ticket {
  id: number
  subject: string
  description: string
  category: string | null
  priority: TicketPriority
  status: TicketStatus
  ai_summary: string | null
  ai_sentiment: Sentiment | null
  customer: UserBrief
  assigned_agent: UserBrief | null
  created_at: string
  updated_at: string
  resolved_at: string | null
}

export type TicketEventType =
  | 'TICKET_CREATED'
  | 'TICKET_ASSIGNED'
  | 'STATUS_CHANGED'
  | 'PRIORITY_CHANGED'
  | 'CATEGORY_CHANGED'
  | 'MESSAGE_ADDED'
  | 'AI_ANALYSIS_COMPLETED'
  | 'TICKET_RESOLVED'

export interface TicketEvent {
  id: number
  event_type: TicketEventType
  user: UserBrief | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface Category {
  id: number
  code: string
  name: string
  description: string | null
  is_active: boolean
}

export interface TicketFilters {
  search?: string
  status?: TicketStatus[]
  priority?: TicketPriority[]
  category?: string
  assigned_agent?: string
  customer_id?: number
  sort?: 'created_at' | 'updated_at' | 'priority' | 'status'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface TicketMessage {
  id: number
  ticket_id: number
  sender: UserBrief
  message: string
  is_internal: boolean
  created_at: string
}

export interface TicketStats {
  by_status: Record<TicketStatus, number>
  assigned_to_me: number
  unassigned: number
  urgent: number
}
