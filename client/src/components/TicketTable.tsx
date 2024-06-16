import { Link } from 'react-router-dom'
import { useCategories } from '../hooks/useCategories'
import type { Ticket } from '../types/ticket'
import { timeAgo } from '../utils/format'
import { PriorityBadge, StatusBadge } from './Badges'

export default function TicketTable({ tickets, showStaffColumns = false }: { tickets: Ticket[]; showStaffColumns?: boolean }) {
  const { labelFor } = useCategories()

  return (
    <div className="card overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase text-slate-500">
          <tr>
            <th className="px-4 py-2">Subject</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Priority</th>
            {showStaffColumns && <th className="hidden px-4 py-2 lg:table-cell">Category</th>}
            {showStaffColumns && <th className="hidden px-4 py-2 md:table-cell">Assigned</th>}
            <th className="hidden px-4 py-2 sm:table-cell">Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {tickets.map((ticket) => (
            <tr key={ticket.id} className="hover:bg-slate-50">
              <td className="px-4 py-3">
                <Link to={`/tickets/${ticket.id}`} className="font-medium text-slate-900 hover:text-indigo-700">
                  <span className="mr-1 text-slate-400">#{ticket.id}</span>
                  {ticket.subject}
                </Link>
                {showStaffColumns && <div className="text-xs text-slate-500">{ticket.customer.name}</div>}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={ticket.status} />
              </td>
              <td className="px-4 py-3">
                <PriorityBadge priority={ticket.priority} />
              </td>
              {showStaffColumns && (
                <td className="hidden px-4 py-3 text-slate-600 lg:table-cell">{labelFor(ticket.category)}</td>
              )}
              {showStaffColumns && (
                <td className="hidden px-4 py-3 text-slate-600 md:table-cell">
                  {ticket.assigned_agent?.name ?? <span className="text-slate-400">Unassigned</span>}
                </td>
              )}
              <td className="hidden whitespace-nowrap px-4 py-3 text-slate-500 sm:table-cell" title={ticket.updated_at}>
                {timeAgo(ticket.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
