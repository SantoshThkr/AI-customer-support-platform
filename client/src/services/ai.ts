import api from './api'
import type { AIStatus, TicketAnalysis } from '../types/ai'

export async function getAIStatus() {
  const { data } = await api.get<AIStatus>('/ai/status')
  return data
}

export async function analyzeTicket(ticketId: number) {
  const { data } = await api.post<TicketAnalysis>(`/ai/tickets/${ticketId}/analyze`)
  return data
}

export async function summarizeTicket(ticketId: number) {
  const { data } = await api.post<{ summary: string }>(`/ai/tickets/${ticketId}/summarize`)
  return data.summary
}
