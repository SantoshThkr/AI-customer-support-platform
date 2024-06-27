import { useEffect, useState } from 'react'
import { getTicketStats } from '../services/tickets'
import type { TicketStats } from '../types/ticket'

export function useTicketStats() {
  const [stats, setStats] = useState<TicketStats | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    getTicketStats()
      .then((data) => !cancelled && setStats(data))
      .catch(() => !cancelled && setError(true))
    return () => {
      cancelled = true
    }
  }, [])

  return { stats, error }
}
