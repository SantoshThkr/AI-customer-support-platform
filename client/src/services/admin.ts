import api from './api'
import type { SystemSettings } from '../types/ai'
import type { Analytics } from '../types/analytics'

export async function getAnalytics() {
  const { data } = await api.get<Analytics>('/admin/analytics')
  return data
}

export async function getSystemSettings() {
  const { data } = await api.get<SystemSettings>('/admin/settings')
  return data
}

export async function updateSystemSettings(changes: Partial<SystemSettings>) {
  const { data } = await api.patch<SystemSettings>('/admin/settings', changes)
  return data
}
