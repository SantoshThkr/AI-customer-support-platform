export type UserRole = 'CUSTOMER' | 'AGENT' | 'ADMIN'

export interface UserBrief {
  id: number
  name: string
  email: string
  role: UserRole
}

export interface User extends UserBrief {
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}
