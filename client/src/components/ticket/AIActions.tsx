import { useState } from 'react'
import { analyzeTicket, summarizeTicket } from '../../services/ai'
import type { AIStatus } from '../../types/ai'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'

interface Props {
  ticketId: number
  status: AIStatus | null
  onChanged: () => void
}

export default function AIActions({ ticketId, status, onChanged }: Props) {
  const [running, setRunning] = useState<'analyze' | 'summarize' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async (action: 'analyze' | 'summarize') => {
    setRunning(action)
    setError(null)
    try {
      if (action === 'analyze') {
        await analyzeTicket(ticketId)
      } else {
        await summarizeTicket(ticketId)
      }
      onChanged()
    } catch (err) {
      setError(getErrorMessage(err, 'The AI request failed'))
    } finally {
      setRunning(null)
    }
  }

  if (status && !status.available) {
    return <p className="text-sm text-slate-500">AI assistance is unavailable: {status.reason}</p>
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <button type="button" className="btn-secondary" disabled={!status || running !== null} onClick={() => run('analyze')}>
          {running === 'analyze' ? 'Analyzing…' : 'Analyze ticket'}
        </button>
        <button type="button" className="btn-secondary" disabled={!status || running !== null} onClick={() => run('summarize')}>
          {running === 'summarize' ? 'Summarizing…' : 'Summarize'}
        </button>
      </div>
      <p className="text-xs text-slate-500">
        Analysis sets category, priority and sentiment. Summaries include the whole conversation.
      </p>
      {error && <Alert>{error}</Alert>}
    </div>
  )
}
