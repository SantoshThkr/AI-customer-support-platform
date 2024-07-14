import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import KnowledgeResults from '../components/KnowledgeResults'
import Spinner from '../components/Spinner'
import { useAuth } from '../context/AuthContext'
import { createArticle, deleteDocument, listDocuments, searchKnowledge, uploadDocument } from '../services/knowledge'
import type { KnowledgeDocument, KnowledgeSearchResponse } from '../types/knowledge'
import { getErrorMessage } from '../utils/errors'
import { formatDate, humanize } from '../utils/format'

export default function KnowledgePage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'
  const [documents, setDocuments] = useState<KnowledgeDocument[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = () =>
    listDocuments()
      .then(setDocuments)
      .catch((err) => setError(getErrorMessage(err, 'Could not load documents')))

  useEffect(() => {
    load()
  }, [])

  const remove = async (document: KnowledgeDocument) => {
    if (!window.confirm(`Delete "${document.title}"? This cannot be undone.`)) return
    try {
      await deleteDocument(document.id)
      setDocuments((current) => current?.filter((item) => item.id !== document.id) ?? null)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Knowledge base</h1>
      <SearchSection />
      {isAdmin && <AddDocument onAdded={load} />}

      <section className="space-y-3">
        <h2 className="font-semibold">Documents</h2>
        {error && <Alert>{error}</Alert>}
        {!documents && !error && <Spinner />}
        {documents && documents.length === 0 && (
          <EmptyState title="No documents yet">
            {isAdmin ? 'Upload guides and FAQs so agents can find answers quickly.' : 'Ask an admin to add support articles.'}
          </EmptyState>
        )}
        {documents && documents.length > 0 && (
          <div className="card overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-2">Title</th>
                  <th className="hidden px-4 py-2 sm:table-cell">Type</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="hidden px-4 py-2 md:table-cell">Chunks</th>
                  <th className="hidden px-4 py-2 md:table-cell">Added</th>
                  {isAdmin && <th className="px-4 py-2" />}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((document) => (
                  <tr key={document.id}>
                    <td className="px-4 py-2">
                      <Link to={`/knowledge/${document.id}`} className="font-medium hover:text-indigo-700">
                        {document.title}
                      </Link>
                      {document.filename && <div className="text-xs text-slate-500">{document.filename}</div>}
                    </td>
                    <td className="hidden px-4 py-2 text-slate-600 sm:table-cell">{document.file_type}</td>
                    <td className="px-4 py-2">
                      <span title={document.error_message ?? undefined}>{humanize(document.status)}</span>
                    </td>
                    <td className="hidden px-4 py-2 text-slate-600 md:table-cell">{document.chunk_count}</td>
                    <td className="hidden px-4 py-2 text-slate-600 md:table-cell">{formatDate(document.created_at)}</td>
                    {isAdmin && (
                      <td className="px-4 py-2 text-right">
                        <button type="button" className="text-sm text-red-600 hover:underline" onClick={() => remove(document)}>
                          Delete
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

function SearchSection() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<KnowledgeSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (query.trim().length < 2) return
    setLoading(true)
    setError(null)
    try {
      setResponse(await searchKnowledge(query.trim(), 8))
    } catch (err) {
      setError(getErrorMessage(err, 'Search failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card space-y-3 p-4">
      <form onSubmit={submit} className="flex gap-2">
        <input
          type="search"
          className="input"
          aria-label="Search the knowledge base"
          placeholder="Ask a question, e.g. how long is a password reset link valid?"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>
      {error && <Alert>{error}</Alert>}
      {response && (
        <>
          <p className="text-xs text-slate-500">
            {response.results.length} result{response.results.length === 1 ? '' : 's'} ·{' '}
            {response.mode === 'semantic' ? 'semantic search' : 'keyword search'}
          </p>
          {response.results.length > 0 ? (
            <KnowledgeResults results={response.results} />
          ) : (
            <p className="text-sm text-slate-500">Nothing matched. Try different words.</p>
          )}
        </>
      )}
    </section>
  )
}

function AddDocument({ onAdded }: { onAdded: () => void }) {
  const [mode, setMode] = useState<'upload' | 'write'>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileInputKey, setFileInputKey] = useState(0)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    if (mode === 'upload' && !file) return setError('Choose a file to upload')
    if (mode === 'write' && (!title.trim() || !content.trim())) return setError('Title and content are required')

    setSaving(true)
    try {
      if (mode === 'upload' && file) {
        await uploadDocument(file, title.trim() || undefined)
      } else {
        await createArticle(title.trim(), content)
      }
      setFile(null)
      setTitle('')
      setContent('')
      setFileInputKey((key) => key + 1)
      onAdded()
    } catch (err) {
      setError(getErrorMessage(err, 'Could not add the document'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="card space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">Add a document</h2>
        <div className="flex gap-1 text-sm">
          {(['upload', 'write'] as const).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setMode(value)}
              className={`rounded-md px-3 py-1 ${mode === value ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              {value === 'upload' ? 'Upload file' : 'Write article'}
            </button>
          ))}
        </div>
      </div>
      <form onSubmit={submit} className="space-y-3">
        {error && <Alert>{error}</Alert>}
        <div>
          <label htmlFor="doc-title" className="label">
            Title {mode === 'upload' && <span className="font-normal text-slate-400">(optional, defaults to file name)</span>}
          </label>
          <input id="doc-title" className="input" value={title} onChange={(event) => setTitle(event.target.value)} />
        </div>
        {mode === 'upload' ? (
          <div>
            <label htmlFor="doc-file" className="label">
              File (.txt, .md or .pdf, up to 5 MB)
            </label>
            <input
              key={fileInputKey}
              id="doc-file"
              type="file"
              accept=".txt,.md,.markdown,.pdf"
              className="block text-sm"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
        ) : (
          <div>
            <label htmlFor="doc-content" className="label">
              Content (Markdown)
            </label>
            <textarea id="doc-content" rows={8} className="input font-mono" value={content} onChange={(event) => setContent(event.target.value)} />
          </div>
        )}
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? 'Saving…' : 'Add document'}
        </button>
      </form>
    </section>
  )
}
