// 🎯 統一 Mock 框架 - 消除重複代碼
import { vi } from 'vitest'

// ========== Element Plus Mock ==========
export const mockElementPlus = () => {
  vi.mock('element-plus', () => ({
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue('confirm'),
      alert: vi.fn().mockResolvedValue()
    },
    ElLoading: {
      service: vi.fn(() => ({ close: vi.fn() }))
    }
  }))
}

// ========== Vue Router Mock ==========
export const mockRouter = {
  push: vi.fn().mockResolvedValue(),
  replace: vi.fn().mockResolvedValue(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn()
}

export const mockRoute = {
  path: '/',
  name: 'home',
  params: {},
  query: {},
  meta: {}
}

export const mockVueRouter = () => {
  vi.mock('vue-router', () => ({
    useRouter: () => mockRouter,
    useRoute: () => mockRoute
  }))
}

// ========== Pinia Store Mock ==========
export const mockAuthStore = {
  user: { username: 'testuser', role: 'admin' },
  isAuthenticated: true,
  login: vi.fn().mockResolvedValue(),
  logout: vi.fn(),
  checkAuth: vi.fn().mockResolvedValue(true)
}

export const mockSheepStore = {
  sheep: [],
  totalCount: 0,
  loading: false,
  fetchSheep: vi.fn().mockResolvedValue([]),
  addSheep: vi.fn().mockResolvedValue(),
  updateSheep: vi.fn().mockResolvedValue(),
  deleteSheep: vi.fn().mockResolvedValue()
}

export const mockStores = () => {
  vi.mock('@/stores/auth', () => ({
    useAuthStore: () => mockAuthStore
  }))
  
  vi.mock('@/stores/sheep', () => ({
    useSheepStore: () => mockSheepStore
  }))
}

// ========== API Mock ==========
export const mockAPI = {
  // Auth
  login: vi.fn().mockResolvedValue({ token: 'fake-token' }),
  logout: vi.fn().mockResolvedValue(),
  
  // Sheep
  getSheep: vi.fn().mockResolvedValue([]),
  createSheep: vi.fn().mockResolvedValue({}),
  updateSheep: vi.fn().mockResolvedValue({}),
  deleteSheep: vi.fn().mockResolvedValue(),
  
  // Data
  exportExcel: vi.fn().mockResolvedValue(new Blob()),
  importExcel: vi.fn().mockResolvedValue({ success: true })
}

export const mockAPIs = () => {
  vi.mock('@/api', () => ({ default: mockAPI }))
}

// ========== 完整初始化函數 ==========
export const setupTestMocks = () => {
  mockElementPlus()
  mockVueRouter()
  mockStores()
  mockAPIs()
}

// ========== 測試工具函數 ==========
export const createWrapper = (component, options = {}) => {
  const { mount } = require('@vue/test-utils')
  const { createPinia } = require('pinia')
  
  return mount(component, {
    global: {
      plugins: [createPinia()],
      stubs: {
        'el-button': true,
        'el-form': true,
        'el-form-item': true,
        'el-input': true,
        'el-table': true,
        'el-table-column': true,
        'el-dialog': true,
        'router-link': true,
        'router-view': true
      }
    },
    ...options
  })
}

// ========== 清理函數 ==========
export const resetMocks = () => {
  vi.clearAllMocks()
  Object.values(mockAPI).forEach(mock => mock.mockClear())
  Object.values(mockRouter).forEach(mock => typeof mock === 'function' && mock.mockClear())
}
