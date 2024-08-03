import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { streamCopilot } from '../../services/ai'
import type { AISource, CopilotTurn } from '../../types/ai'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'
import SourceList from './SourceList'

interface Turn extends CopilotTurn {
  sources?: AISource[]
}

const MAX_HISTORY = 6

export default function CopilotPanel({ ticketId }: { ticketId: number }) {
  const [turns, setTurns] = useState<Turn[]>([])
  const [question, setQuestion] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const updateAnswer = (change: (turn: Turn) => Turn) =>
    setTurns((current) => [...current.slice(0, -1), change(current[current.length - 1])])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const text = question.trim()
    if (!text || streaming) return

    // Only completed exchanges are sent back as history.
    const history = turns
      .filter((turn) => turn.content)
      .slice(-MAX_HISTORY)
      .map(({ role, content }) => ({ role, content }))
    setTurns((current) => [...current, { role: 'user', content: text }, { role: 'assistant', content: '' }])
    setQuestion('')
    setError(null)
    setStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller
    try {
      await streamCopilot(ticketId, text, history, {
        onSources: (sources) => updateAnswer((turn) => ({ ...turn, sources })),
        onText: (chunk) => updateAnswer((turn) => ({ ...turn, content: turn.content + chunk })),
        signal: controller.signal,
      })
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(getErrorMessage(err, 'The assistant could not answer'))
        setTurns((current) => (current[current.length - 1]?.content ? current : current.slice(0, -1)))
      }
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="space-y-3">
      {turns.length === 0 && (
        <p className="text-sm text-slate-500">
          Ask about this ticket, e.g. “What should I tell this customer?” The assistant only sees this ticket, this
          customer's history and the knowledge base.
        </p>
      )}
      <ol className="max-h-96 space-y-2 overflow-y-auto" aria-live="polite">
        {turns.map((turn, index) => (
          <li
            key={index}
            className={`rounded-md p-2 text-sm ${turn.role === 'user' ? 'ml-6 bg-slate-100' : 'mr-2 bg-indigo-50/70'}`}
          >
            <p className="whitespace-pre-wrap">
              {turn.content || (streaming && index === turns.length - 1 ? <span className="text-slate-500">Thinking…</span> : null)}
            </p>
            {turn.sources && turn.content && <SourceList sources={turn.sources} />}
          </li>
        ))}
      </ol>
      {error && <Alert>{error}</Alert>}
      <form onSubmit={submit} className="flex gap-2">
        <input
          className="input"
          placeholder="Ask the assistant…"
          aria-label="Ask the AI assistant"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <button type="submit" className="btn-secondary" disabled={streaming || !question.trim()}>
          Ask
        </button>
      </form>
    </div>
  )
}
