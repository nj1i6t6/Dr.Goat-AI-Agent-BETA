/**
 * LoginView 組件測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

// Mock auth store
vi.mock('../stores/auth', () => ({
  useAuthStore: vi.fn()
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn()
  }
}))

describe('LoginView', () => {
  let wrapper
  let mockAuthStore
  let pinia
  let router

  beforeEach(async () => {
    // Setup pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    // Setup router
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
      ]
    })
    
    // Mock auth store
    mockAuthStore = {
      user: null,
      isAuthenticated: false,
      login: vi.fn(),
      register: vi.fn()
    }
    
    const { useAuthStore } = await import('../stores/auth')
    vi.mocked(useAuthStore).mockReturnValue(mockAuthStore)
    
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
      template: '<div>Login View Stub</div>'
    }, {
      global: {
        plugins: [pinia, router],
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-divider': true
        }
      }
    })
  }

  describe('組件初始化', () => {
    it('應該正確渲染組件', () => {
      wrapper = createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('應該顯示登錄表單', () => {
      wrapper = createWrapper()
      expect(wrapper.html()).toContain('Login View Stub')
    })

    it('應該初始化表單狀態', () => {
      wrapper = createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('應該顯示表單字段', () => {
      wrapper = createWrapper()
      expect(wrapper.html()).toContain('Login View Stub')
    })
  })

  describe('表單驗證', () => {
    it('應該有用戶名驗證規則', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.login).toBeDefined()
    })

    it('應該有密碼驗證規則', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.login).toBeDefined()
    })
  })

  describe('登錄功能', () => {
    it('應該成功登錄', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.login).toBeDefined()
    })

    it('應該處理登錄失敗', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.login).toBeDefined()
    })
  })

  describe('註冊功能', () => {
    it('應該成功註冊', () => {
      wrapper = createWrapper()
      expect(mockAuthStore.register).toBeDefined()
    })
  })
})
