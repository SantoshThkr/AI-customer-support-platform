import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { searchKnowledge } from '../../services/knowledge'
import type { KnowledgeSearchResponse } from '../../types/knowledge'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'
import KnowledgeResults from '../KnowledgeResults'

export default function KnowledgePanel({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = useState(initialQuery)
  const [response, setResponse] = useState<KnowledgeSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async (text: string) => {
    if (text.trim().length < 2) return
    setLoading(true)
    setError(null)
    try {
      setResponse(await searchKnowledge(text.trim(), 3))
    } catch (err) {
      setError(getErrorMessage(err, 'Search failed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    search(initialQuery)
  }, [initialQuery])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    search(query)
  }

  return (
    <div className="space-y-3">
      <form onSubmit={submit} className="flex gap-2">
        <input
          type="search"
          className="input"
          aria-label="Search knowledge base"
          placeholder="Search articles…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit" className="btn-secondary" disabled={loading}>
          Search
        </button>
      </form>
      {error && <Alert>{error}</Alert>}
      {loading && <p className="text-sm text-slate-500">Searching…</p>}
      {!loading && response && response.results.length === 0 && (
        <p className="text-sm text-slate-500">No matching articles.</p>
      )}
      {!loading && response && response.results.length > 0 && <KnowledgeResults results={response.results} compact />}
    </div>
  )
}
