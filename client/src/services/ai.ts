import api from './api'
import type { AIStatus, CopilotAnswer, CopilotTurn, Suggestion, TicketAnalysis } from '../types/ai'

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

export async function suggestResponse(ticketId: number, instructions?: string) {
  const { data } = await api.post<Suggestion>(`/ai/tickets/${ticketId}/suggest-response`, {
    instructions: instructions || null,
  })
  return data
}

export async function askCopilot(ticketId: number, question: string, history: CopilotTurn[]) {
  const { data } = await api.post<CopilotAnswer>(`/ai/tickets/${ticketId}/copilot`, { question, history })
  return data
}
