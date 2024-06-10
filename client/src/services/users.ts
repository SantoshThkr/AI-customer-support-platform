import api from './api'
import type { Page, User, UserBrief, UserRole } from '../types/user'

export interface UserFilters {
  search?: string
  role?: UserRole | ''
  page?: number
}

export interface CreateUserInput {
  name: string
  email: string
  password: string
  role: UserRole
}

export interface UpdateUserInput {
  name?: string
  role?: UserRole
  is_active?: boolean
  password?: string
}

export async function listUsers(filters: UserFilters) {
  const params = { ...filters, role: filters.role || undefined, search: filters.search || undefined }
  const { data } = await api.get<Page<User>>('/users', { params })
  return data
}

export async function listAgents() {
  const { data } = await api.get<UserBrief[]>('/users/agents')
  return data
}

export async function createUser(input: CreateUserInput) {
  const { data } = await api.post<User>('/users', input)
  return data
}

export async function updateUser(id: number, input: UpdateUserInput) {
  const { data } = await api.patch<User>(`/users/${id}`, input)
  return data
}
