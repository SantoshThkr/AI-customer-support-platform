import { AxiosError } from 'axios'
import type { AxiosResponse } from 'axios'
import type { Ticket, TicketMessage } from '../types/ticket'
import type { Page, User } from '../types/user'

export const customer: User = {
  id: 1,
  name: 'Jane Customer',
  email: 'jane@example.com',
  role: 'CUSTOMER',
  is_active: true,
  created_at: '2024-05-01T10:00:00Z',
}

export const agent: User = {
  id: 2,
  name: 'Alex Agent',
  email: 'alex@example.com',
  role: 'AGENT',
  is_active: true,
  created_at: '2024-05-01T10:00:00Z',
}

export function makeTicket(overrides: Partial<Ticket> = {}): Ticket {
  return {
    id: 7,
    subject: 'Cannot log in',
    description: 'I reset my password but still get an error.',
    category: 'ACCOUNT',
    priority: 'MEDIUM',
    status: 'OPEN',
    ai_summary: null,
    ai_sentiment: null,
    customer: { id: customer.id, name: customer.name, email: customer.email, role: 'CUSTOMER' },
    assigned_agent: null,
    created_at: '2024-06-01T09:00:00Z',
    updated_at: '2024-06-01T09:30:00Z',
    resolved_at: null,
    ...overrides,
  }
}

export function makeMessage(overrides: Partial<TicketMessage> = {}): TicketMessage {
  return {
    id: 100,
    ticket_id: 7,
    sender: { id: agent.id, name: agent.name, email: agent.email, role: 'AGENT' },
    message: 'Could you try a private window?',
    is_internal: false,
    created_at: '2024-06-01T10:00:00Z',
    ...overrides,
  }
}

export function page<T>(items: T[], overrides: Partial<Page<T>> = {}): Page<T> {
  return { items, total: items.length, page: 1, page_size: 20, pages: items.length ? 1 : 0, ...overrides }
}

export function apiError(status: number, detail: unknown) {
  return new AxiosError('Request failed', String(status), undefined, undefined, {
    status,
    data: { detail },
  } as AxiosResponse)
}
