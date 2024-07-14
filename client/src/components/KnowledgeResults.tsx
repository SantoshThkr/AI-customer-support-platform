import { Link } from 'react-router-dom'
import type { KnowledgeSearchResult } from '../types/knowledge'

// The section heading is already shown next to the title.
const withoutHeading = (text: string) => text.replace(/^#{1,6} .*\n+/, '')

export default function KnowledgeResults({ results, compact = false }: { results: KnowledgeSearchResult[]; compact?: boolean }) {
  return (
    <ul className="space-y-3">
      {results.map((result) => (
        <li key={result.chunk_id} className="rounded-md border border-slate-200 p-3">
          <Link to={`/knowledge/${result.document_id}`} className="text-sm font-medium text-indigo-700 hover:underline">
            {result.document_title}
          </Link>
          {result.section && <span className="text-xs text-slate-500"> · {result.section}</span>}
          <p className={`mt-1 whitespace-pre-wrap text-sm text-slate-600 ${compact ? 'line-clamp-4' : ''}`}>
            {withoutHeading(result.chunk_text)}
          </p>
        </li>
      ))}
    </ul>
  )
}
