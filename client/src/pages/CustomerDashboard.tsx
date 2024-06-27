import { Link } from 'react-router-dom'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import Spinner from '../components/Spinner'
import StatCard from '../components/StatCard'
import TicketTable from '../components/TicketTable'
import { useAuth } from '../context/AuthContext'
import { useTicketList } from '../hooks/useTicketList'
import { useTicketStats } from '../hooks/useTicketStats'

export default function CustomerDashboard() {
  const { user } = useAuth()
  const { stats } = useTicketStats()
  const { data, loading, error } = useTicketList({ page_size: 5, sort: 'updated_at' })

  const count = (...statuses: (keyof NonNullable<typeof stats>['by_status'])[]) =>
    stats ? statuses.reduce((sum, status) => sum + stats.by_status[status], 0) : undefined

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Hi {user?.name.split(' ')[0]}</h1>
          <p className="text-sm text-slate-600">Here's what's happening with your support requests.</p>
        </div>
        <Link to="/tickets/new" className="btn-primary">
          New ticket
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Open tickets" value={count('OPEN', 'IN_PROGRESS')} hint="Being handled by support" />
        <StatCard
          label="Pending tickets"
          value={count('WAITING_FOR_CUSTOMER')}
          hint="Waiting for your reply"
        />
        <StatCard label="Resolved tickets" value={count('RESOLVED', 'CLOSED')} />
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Recent tickets</h2>
          <Link to="/tickets" className="text-sm text-indigo-600 hover:underline">
            View all
          </Link>
        </div>
        {error && <Alert>{error}</Alert>}
        {loading && !data && <Spinner label="Loading tickets…" />}
        {data && data.items.length === 0 && (
          <EmptyState title="You haven't opened any tickets yet">
            Need help? <Link to="/tickets/new" className="text-indigo-600 hover:underline">Create your first ticket</Link>.
          </EmptyState>
        )}
        {data && data.items.length > 0 && <TicketTable tickets={data.items} />}
      </section>
    </div>
  )
}
