import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import Pagination from '../components/Pagination'
import Spinner from '../components/Spinner'
import TicketFiltersBar from '../components/TicketFiltersBar'
import TicketTable from '../components/TicketTable'
import { useAgents } from '../hooks/useAgents'
import { useTicketList } from '../hooks/useTicketList'
import { useTicketStats } from '../hooks/useTicketStats'
import type { TicketFilters, TicketStats, TicketStatus } from '../types/ticket'

const ACTIVE: TicketStatus[] = ['OPEN', 'IN_PROGRESS', 'WAITING_FOR_CUSTOMER']

interface Queue {
  key: string
  label: string
  filters: TicketFilters
  count?: (stats: TicketStats) => number
}

const QUEUES: Queue[] = [
  {
    key: 'open',
    label: 'Open tickets',
    filters: { status: ['OPEN', 'IN_PROGRESS'] },
    count: (s) => s.by_status.OPEN + s.by_status.IN_PROGRESS,
  },
  {
    key: 'mine',
    label: 'My tickets',
    filters: { assigned_agent: 'me', status: ACTIVE },
    count: (s) => s.assigned_to_me,
  },
  {
    key: 'urgent',
    label: 'Urgent',
    filters: { priority: ['URGENT'], status: ACTIVE },
    count: (s) => s.urgent,
  },
  {
    key: 'waiting',
    label: 'Waiting for customer',
    filters: { status: ['WAITING_FOR_CUSTOMER'] },
    count: (s) => s.by_status.WAITING_FOR_CUSTOMER,
  },
  { key: 'resolved', label: 'Recently resolved', filters: { status: ['RESOLVED', 'CLOSED'] } },
]

function withoutEmpty(filters: TicketFilters): TicketFilters {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== ''),
  ) as TicketFilters
}

export default function AgentDashboard() {
  const [searchParams, setSearchParams] = useSearchParams()
  const queue = QUEUES.find((item) => item.key === searchParams.get('queue')) ?? QUEUES[0]
  const [filters, setFilters] = useState<TicketFilters>({ page: 1 })
  const [sort, setSort] = useState<TicketFilters['sort']>('updated_at')
  const agents = useAgents()
  const { stats } = useTicketStats()

  const query = useMemo(
    () => ({ ...queue.filters, ...withoutEmpty(filters), sort, order: 'desc' as const }),
    [queue, filters, sort],
  )
  const { data, loading, error } = useTicketList(query)

  const selectQueue = (key: string) => {
    setSearchParams({ queue: key })
    setFilters({ page: 1 })
  }

  const handleFilters = useCallback((next: TicketFilters) => setFilters(next), [])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Support queue</h1>
        {stats && (
          <p className="text-sm text-slate-500">
            {stats.unassigned} unassigned · {stats.assigned_to_me} assigned to you
          </p>
        )}
      </div>

      <div className="-mx-1 flex gap-1 overflow-x-auto border-b border-slate-200" role="tablist">
        {QUEUES.map((item) => {
          const active = item.key === queue.key
          return (
            <button
              key={item.key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => selectQueue(item.key)}
              className={`-mb-px flex items-center gap-2 whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium ${
                active ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              {item.label}
              {stats && item.count && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{item.count(stats)}</span>
              )}
            </button>
          )
        })}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-2">
        <TicketFiltersBar key={queue.key} filters={filters} onChange={handleFilters} staff agents={agents} />
        <select
          className="input w-auto"
          aria-label="Sort by"
          value={sort}
          onChange={(event) => setSort(event.target.value as TicketFilters['sort'])}
        >
          <option value="updated_at">Recently updated</option>
          <option value="created_at">Newest first</option>
          <option value="priority">Highest priority</option>
        </select>
      </div>

      {error && <Alert>{error}</Alert>}
      {loading && !data && <Spinner label="Loading tickets…" />}
      {data && data.items.length === 0 && (
        <EmptyState title="Nothing here">No tickets match this view right now.</EmptyState>
      )}
      {data && data.items.length > 0 && (
        <div className={loading ? 'opacity-60' : undefined}>
          <TicketTable tickets={data.items} showStaffColumns />
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            onChange={(page) => setFilters({ ...filters, page })}
          />
        </div>
      )}
    </div>
  )
}
