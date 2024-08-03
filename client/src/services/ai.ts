import api, { API_BASE_URL, tokenStorage } from './api'
import { parseSSE } from '../utils/sse'
import type { AISource, AIStatus, CopilotTurn, TicketAnalysis } from '../types/ai'

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

export interface StreamHandlers {
  onSources?: (sources: AISource[]) => void
  onText: (text: string) => void
  signal?: AbortSignal
}

// Axios can't read a streamed response body in the browser, so streaming uses fetch.
async function streamAI(path: string, body: unknown, { onSources, onText, signal }: StreamHandlers) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${tokenStorage.get() ?? ''}`,
    },
    body: JSON.stringify(body),
    signal,
  })
  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail ?? `Request failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    const parsed = parseSSE(buffer + decoder.decode(value, { stream: true }))
    buffer = parsed.rest
    for (const { event, data } of parsed.events) {
      const payload = data as { sources?: AISource[]; text?: string; detail?: string }
      if (event === 'sources') onSources?.(payload.sources ?? [])
      else if (event === 'delta') onText(payload.text ?? '')
      else if (event === 'error') throw new Error(payload.detail ?? 'The AI response was interrupted')
    }
  }
}

export function streamSuggestion(ticketId: number, instructions: string, handlers: StreamHandlers) {
  return streamAI(`/ai/tickets/${ticketId}/suggest-response/stream`, { instructions: instructions || null }, handlers)
}

export function streamCopilot(ticketId: number, question: string, history: CopilotTurn[], handlers: StreamHandlers) {
  return streamAI(`/ai/tickets/${ticketId}/copilot/stream`, { question, history }, handlers)
}
