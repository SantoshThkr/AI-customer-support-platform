import { useState } from 'react'
import type { FormEvent } from 'react'
import { askCopilot } from '../../services/ai'
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const text = question.trim()
    if (!text || loading) return
    const history = turns.slice(-MAX_HISTORY).map(({ role, content }) => ({ role, content }))
    setTurns((current) => [...current, { role: 'user', content: text }])
    setQuestion('')
    setLoading(true)
    setError(null)
    try {
      const answer = await askCopilot(ticketId, text, history)
      setTurns((current) => [...current, { role: 'assistant', content: answer.answer, sources: answer.sources }])
    } catch (err) {
      setError(getErrorMessage(err, 'The assistant could not answer'))
    } finally {
      setLoading(false)
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
            <p className="whitespace-pre-wrap">{turn.content}</p>
            {turn.sources && <SourceList sources={turn.sources} />}
          </li>
        ))}
        {loading && <li className="text-sm text-slate-500">Thinking…</li>}
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
        <button type="submit" className="btn-secondary" disabled={loading || !question.trim()}>
          Ask
        </button>
      </form>
    </div>
  )
}
