import api from './api'
import type { Category } from '../types/ticket'

export interface CategoryInput {
  code?: string
  name?: string
  description?: string | null
  is_active?: boolean
}

export async function listCategories(includeInactive = false) {
  const { data } = await api.get<Category[]>('/categories', {
    params: includeInactive ? { include_inactive: true } : undefined,
  })
  return data
}

export async function createCategory(input: CategoryInput) {
  const { data } = await api.post<Category>('/categories', input)
  return data
}

export async function updateCategory(id: number, input: CategoryInput) {
  const { data } = await api.patch<Category>(`/categories/${id}`, input)
  return data
}
