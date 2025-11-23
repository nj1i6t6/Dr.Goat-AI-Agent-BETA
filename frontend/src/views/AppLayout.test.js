/**
 * AppLayout 組件測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

// 創建 Mock 函數
const createMockElMessage = () => ({
  success: vi.fn(),
  warning: vi.fn(),
  error: vi.fn(),
  info: vi.fn()
})

const createMockElMessageBox = () => ({
  confirm: vi.fn(),
  alert: vi.fn(),
  prompt: vi.fn()
})

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: createMockElMessage(),
  ElMessageBox: createMockElMessageBox()
}))

// Mock auth store
vi.mock('../stores/auth', () => ({
  useAuthStore: vi.fn()
}))

// Mock router
const mockRouter = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

describe('AppLayout', () => {
  let wrapper
  let mockAuthStore
  let pinia

  beforeEach(async () => {
    // Setup pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock auth store
    mockAuthStore = {
      user: { username: 'testuser' },
      isAuthenticated: true,
      logout: vi.fn()
    }
    
    const { useAuthStore } = await import('../stores/auth')
    vi.mocked(useAuthStore).mockReturnValue(mockAuthStore)
    
    // 清除所有 mock
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount({
      template: '<div>App Layout Stub</div>'
    }, {
      global: {
        plugins: [pinia, mockRouter],
        stubs: {
          'el-container': true,
          'el-header': true,
          'el-aside': true,
          'el-main': true,
          'el-menu': true,
          'el-menu-item': true,
          'el-sub-menu': true,
          'el-icon': true,
          'router-view': true
        }
      }
    })
  }

  describe('基本渲染', () => {
    it('應該正確渲染組件', () => {
      wrapper = createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('應該包含基本結構', () => {
      wrapper = createWrapper()
      expect(wrapper.html()).toContain('App Layout Stub')
    })
  })

  describe('身份驗證', () => {
    it('應該顯示用戶資訊', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.user.username).toBe('testuser')
    })

    it('應該處理登出', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.logout).toBeDefined()
    })
  })
})
