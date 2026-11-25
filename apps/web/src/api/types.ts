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

export type TicketStatus = 'open' | 'under_review' | 'resolved'
export type TicketCategory =
  | 'general'
  | 'plumbing'
  | 'electrical'
  | 'furniture'
  | 'heating'
  | 'cleaning'

export interface TicketSummary {
  id: string
  subject: string
  category: TicketCategory
  status: TicketStatus
  reporter_name: string
  created_at: string
  updated_at: string
}

export interface TicketMessage {
  id: string
  author_name: string
  author_role: Role
  body: string
  created_at: string
}

export interface TicketDetail extends TicketSummary {
  description: string
  messages: TicketMessage[]
}

export interface TicketPage {
  items: TicketSummary[]
  meta: { page: number; per_page: number; total: number }
}

export type RequestStatus = 'submitted' | 'withdrawn'
export type RoomType = 'single' | 'double' | 'triple' | 'quad'

export interface AccommodationRequest {
  id: string
  dormitory_name: string
  room_type: RoomType
  desired_move_in: string
  duration_months: number
  note: string | null
  status: RequestStatus
  created_at: string
  updated_at: string
}

export interface RequestPage {
  items: AccommodationRequest[]
  meta: { page: number; per_page: number; total: number }
}

export interface RequestCreatePayload {
  dormitory_name: string
  room_type: RoomType
  desired_move_in: string
  duration_months: number
  note?: string | null
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
