/**
 * 簡化的 Utils 模組測試 - 用於隔離問題
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatDateForInput } from './index'

describe('formatDateForInput 測試', () => {
  beforeEach(() => {
    // Mock console.error to avoid noise in tests
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('應該正確格式化有效的日期字符串', () => {
    expect(formatDateForInput('2023-12-25')).toBe('2023-12-25')
  })

  it('應該處理無效的日期', () => {
    expect(formatDateForInput('invalid-date')).toBe('')
    expect(formatDateForInput('2023-13-01')).toBe('')
    expect(formatDateForInput('2023-02-30')).toBe('')
  })

  it('應該處理空值和 null', () => {
    expect(formatDateForInput('')).toBe('')
    expect(formatDateForInput(null)).toBe('')
    expect(formatDateForInput(undefined)).toBe('')
  })

  it('應該處理非字符串輸入', () => {
    expect(formatDateForInput(20231225)).toBe('')
    expect(formatDateForInput({})).toBe('')
    expect(formatDateForInput([])).toBe('')
  })
})
