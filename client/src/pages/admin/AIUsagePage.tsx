import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import DailyColumns from '../../components/DailyColumns'
import EmptyState from '../../components/EmptyState'
import Spinner from '../../components/Spinner'
import StatCard from '../../components/StatCard'
import { getAIUsage } from '../../services/admin'
import type { AIUsageReport } from '../../types/analytics'
import { getErrorMessage } from '../../utils/errors'
import { formatDateTime, humanize } from '../../utils/format'

const PERIODS = [7, 30, 90]

function tokens(value: number | null) {
  return value === null ? '—' : value.toLocaleString()
}

export default function AIUsagePage() {
  const [days, setDays] = useState(30)
  const [report, setReport] = useState<AIUsageReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setError(null)
    getAIUsage(days)
      .then(setReport)
      .catch((err) => setError(getErrorMessage(err, 'Could not load AI usage')))
  }, [days])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">AI usage</h1>
        <div className="flex gap-1 text-sm" role="group" aria-label="Period">
          {PERIODS.map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={days === value}
              onClick={() => setDays(value)}
              className={`rounded-md px-3 py-1 ${days === value ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
            >
              {value} days
            </button>
          ))}
        </div>
      </div>

      {error && <Alert>{error}</Alert>}
      {!report && !error && <Spinner />}
      {report && report.totals.requests === 0 && report.recent.length === 0 && (
        <EmptyState title="No AI requests yet">Usage appears here once agents start using AI features.</EmptyState>
      )}
      {report && (report.totals.requests > 0 || report.recent.length > 0) && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Requests" value={report.totals.requests.toLocaleString()} />
            <StatCard label="Input tokens" value={report.totals.input_tokens.toLocaleString()} />
            <StatCard label="Output tokens" value={report.totals.output_tokens.toLocaleString()} />
          </div>
          {report.requests_without_token_counts > 0 && (
            <Alert kind="info">
              {report.requests_without_token_counts} request(s) did not report token counts (for example streams that
              were stopped early) and are not included in the token totals.
            </Alert>
          )}

          <section className="card p-4">
            <h2 className="mb-4 text-sm font-semibold">Requests per day</h2>
            <DailyColumns days={report.by_day} unit="request" />
          </section>

          <div className="grid gap-4 lg:grid-cols-2">
            <UsageTable
              title="By operation"
              rows={report.by_operation.map((row) => ({ ...row, label: humanize(row.operation) }))}
            />
            <UsageTable title="By model" rows={report.by_model.map((row) => ({ ...row, label: row.model }))} />
          </div>

          <section className="card p-4">
            <h2 className="mb-3 text-sm font-semibold">Most active users</h2>
            <ul className="divide-y divide-slate-100 text-sm">
              {report.top_users.map((user) => (
                <li key={user.user_id ?? 'system'} className="flex justify-between py-1.5">
                  <span>{user.name}</span>
                  <span className="tabular-nums text-slate-600">{user.requests}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="card overflow-x-auto">
            <h2 className="px-4 pt-4 text-sm font-semibold">Recent requests</h2>
            <table className="mt-2 min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-2">When</th>
                  <th className="px-4 py-2">Operation</th>
                  <th className="hidden px-4 py-2 md:table-cell">User</th>
                  <th className="hidden px-4 py-2 md:table-cell">Ticket</th>
                  <th className="px-4 py-2 text-right">In</th>
                  <th className="px-4 py-2 text-right">Out</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.recent.map((row) => (
                  <tr key={row.id}>
                    <td className="whitespace-nowrap px-4 py-2 text-slate-600">{formatDateTime(row.created_at)}</td>
                    <td className="px-4 py-2">{humanize(row.operation)}</td>
                    <td className="hidden px-4 py-2 text-slate-600 md:table-cell">{row.user_name ?? 'System'}</td>
                    <td className="hidden px-4 py-2 md:table-cell">
                      {row.ticket_id ? (
                        <Link to={`/tickets/${row.ticket_id}`} className="text-indigo-600 hover:underline">
                          #{row.ticket_id}
                        </Link>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-2 text-right tabular-nums">{tokens(row.input_tokens)}</td>
                    <td className="px-4 py-2 text-right tabular-nums">{tokens(row.output_tokens)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  )
}

function UsageTable({
  title,
  rows,
}: {
  title: string
  rows: { label: string; requests: number; input_tokens: number; output_tokens: number }[]
}) {
  return (
    <section className="card overflow-x-auto">
      <h2 className="px-4 pt-4 text-sm font-semibold">{title}</h2>
      <table className="mt-2 min-w-full text-sm">
        <thead className="text-left text-xs font-semibold uppercase text-slate-500">
          <tr>
            <th className="px-4 py-2" />
            <th className="px-4 py-2 text-right">Requests</th>
            <th className="px-4 py-2 text-right">Input</th>
            <th className="px-4 py-2 text-right">Output</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={row.label}>
              <td className="px-4 py-2">{row.label}</td>
              <td className="px-4 py-2 text-right tabular-nums">{row.requests.toLocaleString()}</td>
              <td className="px-4 py-2 text-right tabular-nums">{row.input_tokens.toLocaleString()}</td>
              <td className="px-4 py-2 text-right tabular-nums">{row.output_tokens.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
