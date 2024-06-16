import { useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import Pagination from '../components/Pagination'
import Spinner from '../components/Spinner'
import TicketFiltersBar from '../components/TicketFiltersBar'
import TicketTable from '../components/TicketTable'
import { useAuth } from '../context/AuthContext'
import { useTicketList } from '../hooks/useTicketList'
import type { TicketFilters } from '../types/ticket'

export default function TicketsPage() {
  const { user } = useAuth()
  const isCustomer = user?.role === 'CUSTOMER'
  const [filters, setFilters] = useState<TicketFilters>({ page: 1 })
  const { data, loading, error } = useTicketList(filters)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">{isCustomer ? 'My tickets' : 'All tickets'}</h1>
        {isCustomer && (
          <Link to="/tickets/new" className="btn-primary">
            New ticket
          </Link>
        )}
      </div>

      <TicketFiltersBar filters={filters} onChange={setFilters} staff={!isCustomer} />

      {error && <Alert>{error}</Alert>}
      {loading && !data && <Spinner label="Loading tickets…" />}
      {data && data.items.length === 0 && (
        <EmptyState title="No tickets found">
          {filters.search || filters.status ? 'Try changing the filters.' : 'Tickets you create will show up here.'}
        </EmptyState>
      )}
      {data && data.items.length > 0 && (
        <div className={loading ? 'opacity-60' : undefined}>
          <TicketTable tickets={data.items} showStaffColumns={!isCustomer} />
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
