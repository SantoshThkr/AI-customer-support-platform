import { useEffect, useState } from 'react'
import { useCategories } from '../hooks/useCategories'
import { TICKET_PRIORITIES, TICKET_STATUSES } from '../types/ticket'
import type { TicketFilters, TicketPriority, TicketStatus } from '../types/ticket'
import type { UserBrief } from '../types/user'
import { humanize } from '../utils/format'

interface Props {
  filters: TicketFilters
  onChange: (filters: TicketFilters) => void
  staff?: boolean
  agents?: UserBrief[]
}

export default function TicketFiltersBar({ filters, onChange, staff = false, agents = [] }: Props) {
  const { categories } = useCategories()
  const [search, setSearch] = useState(filters.search ?? '')

  useEffect(() => {
    if (search === (filters.search ?? '')) return
    const timer = setTimeout(() => onChange({ ...filters, search, page: 1 }), 300)
    return () => clearTimeout(timer)
  }, [search, filters, onChange])

  const update = (changes: Partial<TicketFilters>) => onChange({ ...filters, ...changes, page: 1 })

  return (
    <div className="flex flex-wrap gap-2">
      <input
        type="search"
        className="input w-full sm:w-64"
        placeholder={staff ? 'Search subject, text, customer…' : 'Search your tickets'}
        aria-label="Search tickets"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      <select
        className="input w-auto"
        aria-label="Status"
        value={filters.status?.length === 1 ? filters.status[0] : ''}
        onChange={(event) => update({ status: event.target.value ? [event.target.value as TicketStatus] : undefined })}
      >
        <option value="">Any status</option>
        {TICKET_STATUSES.map((value) => (
          <option key={value} value={value}>
            {humanize(value)}
          </option>
        ))}
      </select>
      {staff && (
        <>
          <select
            className="input w-auto"
            aria-label="Priority"
            value={filters.priority?.[0] ?? ''}
            onChange={(event) =>
              update({ priority: event.target.value ? [event.target.value as TicketPriority] : undefined })
            }
          >
            <option value="">Any priority</option>
            {TICKET_PRIORITIES.map((value) => (
              <option key={value} value={value}>
                {humanize(value)}
              </option>
            ))}
          </select>
          <select
            className="input w-auto"
            aria-label="Category"
            value={filters.category ?? ''}
            onChange={(event) => update({ category: event.target.value || undefined })}
          >
            <option value="">Any category</option>
            {categories.map((category) => (
              <option key={category.code} value={category.code}>
                {category.name}
              </option>
            ))}
          </select>
          <select
            className="input w-auto"
            aria-label="Assigned agent"
            value={filters.assigned_agent ?? ''}
            onChange={(event) => update({ assigned_agent: event.target.value || undefined })}
          >
            <option value="">Anyone</option>
            <option value="me">Assigned to me</option>
            <option value="unassigned">Unassigned</option>
            {agents.map((agent) => (
              <option key={agent.id} value={String(agent.id)}>
                {agent.name}
              </option>
            ))}
          </select>
        </>
      )}
    </div>
  )
}
