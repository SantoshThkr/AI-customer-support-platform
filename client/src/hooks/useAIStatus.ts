import { useEffect, useState } from 'react'
import { getAIStatus } from '../services/ai'
import type { AIStatus } from '../types/ai'

export function useAIStatus(enabled: boolean) {
  const [status, setStatus] = useState<AIStatus | null>(null)

  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    getAIStatus()
      .then((data) => !cancelled && setStatus(data))
      .catch(() => !cancelled && setStatus({ available: false, reason: 'Could not check AI status' }))
    return () => {
      cancelled = true
    }
  }, [enabled])

  return status
}
