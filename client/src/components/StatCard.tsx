import { Link } from 'react-router-dom'

interface Props {
  label: string
  value: number | string | null | undefined
  hint?: string
  to?: string
}

export default function StatCard({ label, value, hint, to }: Props) {
  const body = (
    <>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value ?? '—'}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </>
  )
  if (to) {
    return (
      <Link to={to} className="card block p-4 transition-colors hover:border-indigo-300">
        {body}
      </Link>
    )
  }
  return <div className="card p-4">{body}</div>
}
