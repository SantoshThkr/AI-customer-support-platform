import { useEffect, useState } from 'react'
import { listAgents } from '../services/users'
import type { UserBrief } from '../types/user'

export function useAgents(enabled = true) {
  const [agents, setAgents] = useState<UserBrief[]>([])

  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    listAgents()
      .then((data) => !cancelled && setAgents(data))
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [enabled])

  return agents
}
