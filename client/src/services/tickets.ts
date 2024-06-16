import api from './api'
import type { Page } from '../types/user'
import type { Ticket, TicketEvent, TicketFilters, TicketPriority, TicketStatus } from '../types/ticket'

export interface CreateTicketInput {
  subject: string
  description: string
}

export interface UpdateTicketInput {
  status?: TicketStatus
  priority?: TicketPriority
  category?: string
}

function toSearchParams(filters: TicketFilters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) {
      value.forEach((item) => params.append(key, String(item)))
    } else {
      params.set(key, String(value))
    }
  })
  return params
}

export async function listTickets(filters: TicketFilters = {}) {
  const { data } = await api.get<Page<Ticket>>('/tickets', { params: toSearchParams(filters) })
  return data
}

export async function getTicket(id: number) {
  const { data } = await api.get<Ticket>(`/tickets/${id}`)
  return data
}

export async function createTicket(input: CreateTicketInput) {
  const { data } = await api.post<Ticket>('/tickets', input)
  return data
}

export async function updateTicket(id: number, input: UpdateTicketInput) {
  const { data } = await api.patch<Ticket>(`/tickets/${id}`, input)
  return data
}

export async function deleteTicket(id: number) {
  await api.delete(`/tickets/${id}`)
}

export async function listTicketEvents(id: number) {
  const { data } = await api.get<TicketEvent[]>(`/tickets/${id}/events`)
  return data
}
