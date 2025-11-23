import { describe, it, expect } from 'vitest'
import { formatDateForInput } from './index'

describe('utils/formatDateForInput', () => {
  it('returns empty for invalid inputs', () => {
    expect(formatDateForInput(null)).toBe('')
    expect(formatDateForInput('invalid-date')).toBe('')
    expect(formatDateForInput('2023-13-01')).toBe('')
    expect(formatDateForInput('2023-02-30')).toBe('')
    expect(formatDateForInput('1899-12-31')).toBe('')
    expect(formatDateForInput('2100-01-01')).toBe('')
  })

  it('normalizes date separators and returns yyyy-mm-dd', () => {
    expect(formatDateForInput('2023/7/9')).toBe('2023-07-09')
    expect(formatDateForInput('2023-07-09 12:00:00')).toBe('2023-07-09')
  })
})
