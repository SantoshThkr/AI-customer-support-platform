import { useEffect, useRef, useState } from 'react'
import { streamSuggestion } from '../../services/ai'
import type { AISource } from '../../types/ai'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'
import SourceList from './SourceList'

interface Props {
  ticketId: number
  onUse: (text: string) => void
}

export default function SuggestionPanel({ ticketId, onUse }: Props) {
  const [instructions, setInstructions] = useState('')
  const [text, setText] = useState('')
  const [sources, setSources] = useState<AISource[]>([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const generate = async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setText('')
    setSources([])
    setError(null)
    setStreaming(true)
    try {
      await streamSuggestion(ticketId, instructions.trim(), {
        onSources: setSources,
        onText: (chunk) => setText((current) => current + chunk),
        signal: controller.signal,
      })
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(getErrorMessage(err, 'Could not generate a suggestion'))
      }
    } finally {
      if (abortRef.current === controller) setStreaming(false)
    }
  }

  const discard = () => {
    abortRef.current?.abort()
    setText('')
    setSources([])
    setError(null)
    setStreaming(false)
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
        {streaming ? (
          <button type="button" className="btn-secondary" onClick={discard}>
            Stop
          </button>
        ) : (
          <button type="button" className="btn-secondary" onClick={generate}>
            {text ? 'Regenerate' : 'Suggest reply'}
          </button>
        )}
      </div>
      {error && <Alert>{error}</Alert>}
      {(text || streaming) && (
        <div className="space-y-2">
          <div
            className="min-h-[3rem] whitespace-pre-wrap rounded-md bg-indigo-50/60 p-3 text-sm leading-relaxed"
            data-testid="suggestion"
            aria-busy={streaming}
          >
            {text || <span className="text-slate-500">Drafting a reply…</span>}
            {streaming && text && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-indigo-400 align-middle" />}
          </div>
          <SourceList sources={sources} />
          {!streaming && text && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  onUse(text)
                  discard()
                }}
              >
                Use suggestion
              </button>
              <button type="button" className="btn-secondary" onClick={discard}>
                Discard
              </button>
              <span className="text-xs text-slate-500">You can edit it in the reply box before sending.</span>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
