import { describe, it, expect, vi } from 'vitest'
import {
  formatValidationErrors,
  showFormattedError,
  extractFieldErrors,
  isValidationError,
  createFieldValidator,
  showSuccessMessage,
  handleNetworkError,
  handleApiError
} from './errorHandler'

describe('errorHandler functions coverage', () => {
  it('formatValidationErrors handles invalid input and details mapping', () => {
    expect(formatValidationErrors(null)).toEqual({ general: '發生未知錯誤', fields: {} })

    const resp = {
      error: '校驗失敗',
      details: [
        { loc: ['body', 'EarNum'], msg: 'Field required' },
        { loc: ['body', 'Age_Months'], msg: 'value is not a valid integer' },
        { loc: ['body', 'unknown'], msg: 'weird' }
      ]
    }
    const out = formatValidationErrors(resp)
    expect(out.general).toBe('校驗失敗')
    expect(out.fields.EarNum).toContain('耳號')
    expect(out.fields.Age_Months).toContain('整數')
    expect(out.fields.unknown).toBe('weird')
  })

  it('showFormattedError calls message handler', () => {
    const mh = vi.fn()
    const formatted = showFormattedError({ error: 'x' }, mh)
    expect(mh).toHaveBeenCalledWith('x')
    expect(formatted.general).toBe('x')
  })

  it('extractFieldErrors and isValidationError detect correctly', () => {
    const resp = { field_errors: { EarNum: '錯' } }
    expect(extractFieldErrors(resp)).toEqual({ EarNum: '錯' })
    expect(isValidationError(resp)).toBeTruthy()
    expect(isValidationError({ details: [] })).toBeTruthy()
    expect(isValidationError({})).toBeFalsy()
  })

  it('createFieldValidator returns callback errors', () => {
    const validator = createFieldValidator({ EarNum: '錯' })
    const cb = vi.fn()
    validator({ field: 'EarNum' }, '', cb)
    expect(cb).toHaveBeenCalled()
  })

  it('showSuccessMessage passes structured message', () => {
    const mh = vi.fn()
    showSuccessMessage('OK', mh)
    expect(mh).toHaveBeenCalledWith({ message: 'OK', type: 'success' })
  })

  it('handleNetworkError covers no response and status map', () => {
    expect(handleNetworkError(new Error('x'))).toContain('網路連接失敗')
    expect(handleNetworkError({ response: { status: 404 } })).toBe('請求的資源不存在')
    expect(handleNetworkError({ response: { status: 418 } })).toContain('418')
  })

  it('handleApiError for validation error, generic error, and network fallback', () => {
    const mh = vi.fn()

    // validation branch
    const vErr = {
      response: { data: { error: '校驗失敗', field_errors: { EarNum: '必填' }, details: [] } }
    }
    let out = handleApiError(vErr, mh)
    expect(out).toMatchObject({ message: '校驗失敗', fields: { EarNum: '必填' } })

    // generic message branch
    const gErr = { response: { data: { error: '出錯了' } } }
    out = handleApiError(gErr, mh)
    expect(out.message).toBe('出錯了')

    // network fallback
    const nErr = new Error('net')
    out = handleApiError(nErr, mh)
    expect(out.message).toContain('網路')

    expect(mh).toHaveBeenCalled()
  })
})
