import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import BarList from '../../components/BarList'
import DailyColumns from '../../components/DailyColumns'
import Spinner from '../../components/Spinner'
import StatCard from '../../components/StatCard'
import { useCategories } from '../../hooks/useCategories'
import { getAnalytics } from '../../services/admin'
import type { Analytics } from '../../types/analytics'
import { getErrorMessage } from '../../utils/errors'
import { humanize } from '../../utils/format'

function formatHours(hours: number | null) {
  if (hours === null) return '—'
  if (hours < 1) return `${Math.round(hours * 60)} min`
  if (hours < 48) return `${hours.toFixed(1)} h`
  return `${(hours / 24).toFixed(1)} days`
}

export default function AnalyticsPage() {
  const { labelFor } = useCategories()
  const [data, setData] = useState<Analytics | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch((err) => setError(getErrorMessage(err, 'Could not load analytics')))
  }, [])

  if (error) return <Alert>{error}</Alert>
  if (!data) return <Spinner label="Loading analytics…" />

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Analytics</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total tickets" value={data.total_tickets.toLocaleString()} />
        <StatCard label="Open tickets" value={data.open_tickets.toLocaleString()} to="/dashboard?queue=open" />
        <StatCard label="Resolved tickets" value={data.resolved_tickets.toLocaleString()} />
        <StatCard
          label="Average resolution time"
          value={formatHours(data.average_resolution_hours)}
          hint="From creation to resolved/closed"
        />
      </div>

      <section className="card p-4">
        <h2 className="mb-4 text-sm font-semibold">Tickets created, last 14 days</h2>
        <DailyColumns days={data.created_last_14_days} />
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-4">
          <h2 className="mb-4 text-sm font-semibold">Tickets by category</h2>
          <BarList rows={data.by_category.map((row) => ({ label: labelFor(row.category), value: row.count }))} />
        </section>
        <section className="card p-4">
          <h2 className="mb-4 text-sm font-semibold">Tickets by priority</h2>
          <BarList rows={data.by_priority.map((row) => ({ label: humanize(row.priority), value: row.count }))} />
        </section>
      </div>
    </div>
  )
}
