export type Role = 'admin' | 'manager' | 'user'
export type UserStatus = 'active' | 'pending_verification' | 'suspended' | 'deactivated'

export interface User {
  id: string
  email: string
  full_name: string
  phone: string | null
  role: Role
  status: UserStatus
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  full_name: string
  email: string
  password: string
  phone?: string | null
}

export interface FieldProblem {
  field: string
  message: string
  type: string
}

export interface ProblemDetail {
  type: string
  title: string
  status: number
  code: string
  detail: string
  instance: string
  errors?: FieldProblem[]
}
