/**
 * API 模組測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios - 將 mockAxiosInstance 定義在 mock 內部
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: {
        use: vi.fn()
      },
      response: {
        use: vi.fn()
      }
    }
  }
  
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      interceptors: mockAxiosInstance.interceptors
    }
  }
})

// Mock errorHandler
vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

// Mock auth store
vi.mock('../stores/auth', () => ({
  useAuthStore: vi.fn()
}))

import axios from 'axios'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../stores/auth'

describe('API 模組', () => {
  let mockAuthStore
  let pinia
  let api

  beforeEach(async () => {
    // Setup pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock auth store
    mockAuthStore = {
      user: { id: 1, username: 'testuser' },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn()
    }
    
    vi.mocked(useAuthStore).mockReturnValue(mockAuthStore)
    
    // 重置所有 mock
    vi.clearAllMocks()
    
    // 動態導入 API 模組
    const apiModule = await import('../api/index.js')
    api = apiModule.default
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('基本功能', () => {
    it('應該能夠導入 API 模組', () => {
      expect(api).toBeDefined()
    })

    it('應該有所有必要的方法', () => {
      expect(typeof api.getAllSheep).toBe('function')
      expect(typeof api.addSheep).toBe('function') 
      expect(typeof api.updateSheep).toBe('function')
      expect(typeof api.deleteSheep).toBe('function')
      expect(typeof api.login).toBe('function')
      expect(typeof api.getDashboardData).toBe('function')
    })
  })
})
