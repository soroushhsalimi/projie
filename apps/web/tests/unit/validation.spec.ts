import { describe, expect, it } from 'vitest'

import {
  fieldErrors,
  loginSchema,
  passwordStrength,
  registerSchema,
} from '@/modules/auth/validation'

const validRegistration = {
  full_name: 'علی رضایی',
  email: 'ali@example.com',
  phone: '',
  password: 'CorrectHorseBatteryStaple',
  confirmPassword: 'CorrectHorseBatteryStaple',
  acceptTerms: true,
}

describe('loginSchema', () => {
  it('accepts a valid email and password', () => {
    expect(loginSchema.safeParse({ email: 'ali@example.com', password: 'x' }).success).toBe(true)
  })

  it('rejects an invalid email', () => {
    const result = loginSchema.safeParse({ email: 'not-an-email', password: 'x' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(fieldErrors(result.error).email).toBe('validation.email')
    }
  })
})

describe('registerSchema', () => {
  it('accepts a strong registration', () => {
    expect(registerSchema.safeParse(validRegistration).success).toBe(true)
  })

  it('rejects a short password', () => {
    const result = registerSchema.safeParse({ ...validRegistration, password: 'short' })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(fieldErrors(result.error).password).toBe('validation.passwordLength')
    }
  })

  it('requires matching passwords', () => {
    const result = registerSchema.safeParse({
      ...validRegistration,
      confirmPassword: 'SomethingElseEntirely',
    })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(fieldErrors(result.error).confirmPassword).toBe('validation.passwordMismatch')
    }
  })

  it('requires accepting the rules', () => {
    const result = registerSchema.safeParse({ ...validRegistration, acceptTerms: false })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(fieldErrors(result.error).acceptTerms).toBe('validation.termsRequired')
    }
  })

  it('accepts an empty optional phone', () => {
    expect(registerSchema.safeParse({ ...validRegistration, phone: '' }).success).toBe(true)
  })
})

describe('passwordStrength', () => {
  it('marks short passwords weak', () => {
    expect(passwordStrength('abc')).toBe('weak')
  })

  it('marks long mixed passwords strong', () => {
    expect(passwordStrength('CorrectHorseBatteryStaple')).toBe('strong')
  })

  it('marks medium passwords', () => {
    expect(passwordStrength('abcdefghij1')).toBe('medium')
  })
})
