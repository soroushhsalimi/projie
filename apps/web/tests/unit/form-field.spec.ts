import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import { i18n } from '@/app/i18n'
import FormField from '@/modules/auth/components/FormField.vue'

describe('FormField', () => {
  it('binds the label to the input and exposes the error to assistive technology', () => {
    const wrapper = mount(FormField, {
      props: {
        id: 'email',
        label: 'ایمیل',
        modelValue: '',
        error: 'ایمیل معتبر نیست',
        required: true,
      },
      global: { plugins: [i18n] },
    })

    const input = wrapper.get('input')
    expect(input.attributes('id')).toBe('email')
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(input.attributes('aria-describedby')).toBe('email-error')
    expect(wrapper.get('label').attributes('for')).toBe('email')
    expect(wrapper.text()).toContain('ایمیل معتبر نیست')
  })

  it('emits updates through v-model', async () => {
    const wrapper = mount(FormField, {
      props: { id: 'email', label: 'ایمیل', modelValue: '' },
      global: { plugins: [i18n] },
    })

    await wrapper.get('input').setValue('ali@example.com')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['ali@example.com'])
  })
})
