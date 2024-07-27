import { Link } from 'react-router-dom'
import type { AISource } from '../../types/ai'

export default function SourceList({ sources }: { sources: AISource[] }) {
  if (sources.length === 0) return null
  // Several chunks can come from the same article; list each article once.
  const unique = sources.filter(
    (source, index) => sources.findIndex((item) => item.document_id === source.document_id) === index,
  )
  return (
    <p className="text-xs text-slate-500">
      Based on:{' '}
      {unique.map((source, index) => (
        <span key={source.document_id}>
          {index > 0 && ', '}
          <Link to={`/knowledge/${source.document_id}`} className="text-indigo-600 hover:underline">
            {source.document_title}
          </Link>
        </span>
      ))}
    </p>
  )
}
