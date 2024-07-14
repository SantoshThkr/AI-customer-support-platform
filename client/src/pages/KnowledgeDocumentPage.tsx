import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import { getDocument } from '../services/knowledge'
import type { KnowledgeDocumentDetail } from '../types/knowledge'
import { getErrorMessage } from '../utils/errors'
import { formatDateTime, humanize } from '../utils/format'

export default function KnowledgeDocumentPage() {
  const documentId = Number(useParams().id)
  const [document, setDocument] = useState<KnowledgeDocumentDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDocument(documentId)
      .then(setDocument)
      .catch((err) => setError(getErrorMessage(err, 'Could not load the document')))
  }, [documentId])

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Link to="/knowledge" className="text-sm text-indigo-600 hover:underline">
        ← Knowledge base
      </Link>
      {error && <Alert>{error}</Alert>}
      {!document && !error && <Spinner />}
      {document && (
        <article className="card p-6">
          <h1 className="text-xl font-semibold">{document.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {document.file_type} · {document.chunk_count} chunks · {humanize(document.status)} · updated{' '}
            {formatDateTime(document.updated_at)}
          </p>
          {document.error_message && (
            <div className="mt-3">
              <Alert kind="info">{document.error_message}</Alert>
            </div>
          )}
          <pre className="mt-6 whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-800">{document.content}</pre>
        </article>
      )}
    </div>
  )
}
