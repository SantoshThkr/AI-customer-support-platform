import api from './api'
import type { Analytics } from '../types/analytics'

export async function getAnalytics() {
  const { data } = await api.get<Analytics>('/admin/analytics')
  return data
}
