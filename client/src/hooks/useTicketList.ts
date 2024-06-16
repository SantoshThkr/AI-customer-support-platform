import { useCallback, useEffect, useState } from 'react'
import { listTickets } from '../services/tickets'
import type { Ticket, TicketFilters } from '../types/ticket'
import type { Page } from '../types/user'
import { getErrorMessage } from '../utils/errors'

export function useTicketList(filters: TicketFilters) {
  const [data, setData] = useState<Page<Ticket> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Serialized so callers can pass a new object literal on every render.
  const key = JSON.stringify(filters)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await listTickets(JSON.parse(key) as TicketFilters))
    } catch (err) {
      setError(getErrorMessage(err, 'Could not load tickets'))
    } finally {
      setLoading(false)
    }
  }, [key])

  useEffect(() => {
    load()
  }, [load])

  return { data, loading, error, reload: load }
}
