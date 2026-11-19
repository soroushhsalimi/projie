import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().trim().min(1, 'validation.required').email('validation.email'),
  password: z.string().min(1, 'validation.required'),
})

export type LoginForm = z.infer<typeof loginSchema>

export const registerSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(1, 'validation.required')
      .min(3, 'validation.fullName')
      .max(120, 'validation.fullName'),
    email: z.string().trim().min(1, 'validation.required').email('validation.email'),
    phone: z
      .string()
      .trim()
      .refine(
        (value) => value.length === 0 || /^\+?[\d\s-]{7,20}$/.test(value),
        'validation.phone',
      ),
    password: z
      .string()
      .min(10, 'validation.passwordLength')
      .max(128, 'validation.passwordMax'),
    confirmPassword: z.string().min(1, 'validation.required'),
    acceptTerms: z.boolean().refine((value) => value, 'validation.termsRequired'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'validation.passwordMismatch',
  })

export type RegisterForm = z.infer<typeof registerSchema>

export function fieldErrors(error: z.ZodError): Record<string, string> {
  const result: Record<string, string> = {}
  for (const issue of error.issues) {
    const key = issue.path[0]
    if (typeof key === 'string' && !result[key]) result[key] = issue.message
  }
  return result
}

export type PasswordStrength = 'weak' | 'medium' | 'strong'

export function passwordStrength(password: string): PasswordStrength {
  if (password.length < 10) return 'weak'
  let classes = 0
  if (/[a-z]/.test(password)) classes += 1
  if (/[A-Z]/.test(password)) classes += 1
  if (/\d/.test(password)) classes += 1
  if (/[^A-Za-z0-9]/.test(password)) classes += 1
  if (password.length >= 16 && classes >= 2) return 'strong'
  if (password.length >= 12 && classes >= 2) return 'strong'
  if (classes >= 2) return 'medium'
  return 'weak'
}
