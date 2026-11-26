export type Role = 'admin' | 'manager' | 'user'
export type UserStatus = 'active' | 'pending_verification' | 'suspended' | 'deactivated'

export interface User {
  id: string
  email: string
  full_name: string
  national_id: string | null
  phone: string | null
  address: string | null
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
  national_id: string
  phone: string
  address: string
  password: string
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

export type ComplaintStatus = 'submitted' | 'in_review' | 'answered'
export type ComplaintCategory =
  | 'noise'
  | 'cleanliness'
  | 'safety'
  | 'staff'
  | 'facilities'
  | 'other'

export interface ComplaintSummary {
  id: string
  subject: string
  category: ComplaintCategory
  status: ComplaintStatus
  resident_name: string
  created_at: string
  updated_at: string
}

export interface ComplaintResponseRecord {
  id: string
  body: string
  responder_name: string
  created_at: string
}

export interface ComplaintDetail extends ComplaintSummary {
  description: string
  response: ComplaintResponseRecord | null
}

export interface ComplaintPage {
  items: ComplaintSummary[]
  meta: { page: number; per_page: number; total: number }
}

export type RequestStatus = 'submitted' | 'under_review' | 'approved' | 'rejected' | 'withdrawn'
export type ReviewAction = Extract<RequestStatus, 'under_review' | 'approved' | 'rejected'>
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

export interface RequestSummary extends AccommodationRequest {
  applicant_name: string
}

export interface RequestQueuePage {
  items: RequestSummary[]
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
