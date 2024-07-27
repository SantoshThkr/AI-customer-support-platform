import { useState } from 'react'
import type { FormEvent } from 'react'
import { getErrorMessage } from '../../utils/errors'
import Alert from '../Alert'

interface Props {
  draft: string
  onDraftChange: (value: string) => void
  onSend: (message: string, isInternal: boolean) => Promise<void>
  noteMode: boolean
  onNoteModeChange: (value: boolean) => void
  allowInternal: boolean
  canReply: boolean
  disabledReason?: string
  notice?: string
}

export default function ReplyBox({
  draft,
  onDraftChange,
  onSend,
  noteMode,
  onNoteModeChange,
  allowInternal,
  canReply,
  disabledReason,
  notice,
}: Props) {
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isInternal = allowInternal && (noteMode || !canReply)
  const blocked = !isInternal && !canReply

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!draft.trim() || blocked) return
    setSending(true)
    setError(null)
    try {
      await onSend(draft.trim(), isInternal)
      onDraftChange('')
    } catch (err) {
      setError(getErrorMessage(err, 'Could not send the message'))
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={submit} className={`card space-y-3 p-4 ${isInternal ? 'border-amber-300' : ''}`}>
      {allowInternal && (
        <div className="flex gap-1 text-sm" role="tablist" aria-label="Message type">
          <button
            type="button"
            role="tab"
            aria-selected={!isInternal}
            disabled={!canReply}
            onClick={() => onNoteModeChange(false)}
            className={`rounded-md px-3 py-1.5 ${!isInternal ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'} disabled:opacity-50`}
          >
            Reply to customer
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={isInternal}
            onClick={() => onNoteModeChange(true)}
            className={`rounded-md px-3 py-1.5 ${isInternal ? 'bg-amber-500 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
          >
            Internal note
          </button>
        </div>
      )}
      {error && <Alert>{error}</Alert>}
      {blocked && disabledReason && <Alert kind="info">{disabledReason}</Alert>}
      {notice && !isInternal && <Alert kind="info">{notice}</Alert>}
      <label htmlFor="reply" className="sr-only">
        {isInternal ? 'Internal note' : 'Reply'}
      </label>
      <textarea
        id="reply"
        rows={isInternal ? 4 : 7}
        className="input"
        placeholder={isInternal ? 'Only visible to the support team…' : 'Write your reply…'}
        value={draft}
        disabled={blocked}
        onChange={(event) => onDraftChange(event.target.value)}
      />
      <div className="flex justify-end">
        <button
          type="submit"
          className={isInternal ? 'btn bg-amber-500 text-white hover:bg-amber-600' : 'btn-primary'}
          disabled={sending || blocked || !draft.trim()}
        >
          {sending ? 'Sending…' : isInternal ? 'Add note' : 'Send reply'}
        </button>
      </div>
    </form>
  )
}
