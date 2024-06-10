import api from './api'
import type { TokenResponse, User } from '../types/user'

export interface RegisterInput {
  name: string
  email: string
  password: string
}

export async function login(email: string, password: string) {
  const { data } = await api.post<TokenResponse>('/auth/login', { email, password })
  return data
}

export async function register(input: RegisterInput) {
  const { data } = await api.post<TokenResponse>('/auth/register', input)
  return data
}

export async function fetchCurrentUser() {
  const { data } = await api.get<User>('/auth/me')
  return data
}
