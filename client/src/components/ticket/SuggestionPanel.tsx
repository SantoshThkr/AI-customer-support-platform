import { useState } from 'react'
import { suggestResponse } from '../../services/ai'
import type { Suggestion } from '../../types/ai'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'
import SourceList from './SourceList'

interface Props {
  ticketId: number
  onUse: (text: string) => void
}

export default function SuggestionPanel({ ticketId, onUse }: Props) {
  const [instructions, setInstructions] = useState('')
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async () => {
    setLoading(true)
    setError(null)
    setSuggestion(null)
    try {
      setSuggestion(await suggestResponse(ticketId, instructions.trim()))
    } catch (err) {
      setError(getErrorMessage(err, 'Could not generate a suggestion'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card space-y-3 border-indigo-100 p-4" aria-label="AI suggested reply">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="input min-w-0 flex-1"
          placeholder="Optional: guidance for the draft (e.g. mention the refund timeline)"
          aria-label="Guidance for the suggested reply"
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
        />
        <button type="button" className="btn-secondary" onClick={generate} disabled={loading}>
          {loading ? 'Generating…' : suggestion ? 'Regenerate' : 'Suggest reply'}
        </button>
      </div>
      {error && <Alert>{error}</Alert>}
      {suggestion && (
        <div className="space-y-2">
          <div className="whitespace-pre-wrap rounded-md bg-indigo-50/60 p-3 text-sm leading-relaxed" data-testid="suggestion">
            {suggestion.suggestion}
          </div>
          <SourceList sources={suggestion.sources} />
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                onUse(suggestion.suggestion)
                setSuggestion(null)
              }}
            >
              Use suggestion
            </button>
            <button type="button" className="btn-secondary" onClick={() => setSuggestion(null)}>
              Discard
            </button>
            <span className="text-xs text-slate-500">You can edit it in the reply box before sending.</span>
          </div>
        </div>
      )}
    </section>
  )
}
