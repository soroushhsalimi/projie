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
  national_id: '0012345679',
  phone: '09121234567',
  address: 'تهران، خیابان آزادی، پلاک ۱۲',
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

  it('requires a mobile number', () => {
    const missing = registerSchema.safeParse({ ...validRegistration, phone: '' })
    const landline = registerSchema.safeParse({ ...validRegistration, phone: '02112345678' })

    expect(missing.success).toBe(false)
    if (!missing.success) {
      expect(fieldErrors(missing.error).phone).toBe('validation.required')
    }
    expect(landline.success).toBe(false)
    if (!landline.success) {
      expect(fieldErrors(landline.error).phone).toBe('validation.phone')
    }
  })

  it('accepts a national ID typed with Persian digits', () => {
    const result = registerSchema.safeParse({ ...validRegistration, national_id: '۰۰۱۲۳۴۵۶۷۹' })

    expect(result.success).toBe(true)
    if (result.success) expect(result.data.national_id).toBe('0012345679')
  })

  it('rejects a national ID that is not ten digits', () => {
    const result = registerSchema.safeParse({ ...validRegistration, national_id: '12345' })

    expect(result.success).toBe(false)
    if (!result.success) {
      expect(fieldErrors(result.error).national_id).toBe('validation.nationalId')
    }
  })

  it('requires a usable home address', () => {
    const short = registerSchema.safeParse({ ...validRegistration, address: 'تهر' })
    const missing = registerSchema.safeParse({ ...validRegistration, address: '  ' })

    expect(short.success).toBe(false)
    if (!short.success) {
      expect(fieldErrors(short.error).address).toBe('validation.address')
    }
    expect(missing.success).toBe(false)
    if (!missing.success) {
      expect(fieldErrors(missing.error).address).toBe('validation.required')
    }
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
