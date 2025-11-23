import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// 完全隔離的設置，避免所有可能的循環依賴

// Mock 所有 Vue 生態系統組件
vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    currentRoute: { value: { path: '/', name: 'test' } }
  })),
  createWebHistory: vi.fn(),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn()
  })),
  useRoute: vi.fn(() => ({
    path: '/',
    name: 'test',
    params: {},
    query: {}
  }))
}))

vi.mock('pinia', () => ({
  createPinia: vi.fn(() => ({})),
  setActivePinia: vi.fn(),
  defineStore: vi.fn(() => vi.fn(() => ({
    user: { value: null },
    isAuthenticated: { value: false },
    login: vi.fn(),
    logout: vi.fn()
  })))
}))

// Mock Element Plus 完全避免依賴
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

// Mock Element Plus Icons
vi.mock('@element-plus/icons-vue', () => ({}))

// Mock 全局 DOM API
global.URL = {
  createObjectURL: vi.fn(() => 'mock-url'),
  revokeObjectURL: vi.fn()
}

global.Blob = vi.fn()

global.localStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

// 配置 Vue Test Utils 全域設置
config.global.stubs = {
  'router-link': { template: '<a><slot /></a>' },
  'router-view': { template: '<div><slot /></div>' },
  'transition': { template: '<div><slot /></div>' },
  'teleport': { template: '<div><slot /></div>' },
  // Element Plus 組件
  'el-button': { template: '<button><slot /></button>' },
  'el-input': { template: '<input />' },
  'el-form': { template: '<form><slot /></form>' },
  'el-form-item': { template: '<div><slot /></div>' },
  'el-card': { template: '<div><slot /></div>' },
  'el-upload': { template: '<div><slot /></div>' },
  'el-table': { template: '<table><slot /></table>' },
  'el-table-column': { template: '<td><slot /></td>' },
  'el-dialog': { template: '<div><slot /></div>' },
  'el-tabs': { template: '<div><slot /></div>' },
  'el-tab-pane': { template: '<div><slot /></div>' },
  'el-icon': { template: '<i><slot /></i>' },
  'el-divider': { template: '<hr />' },
  'el-tag': { template: '<span><slot /></span>' },
  'el-alert': { template: '<div><slot /></div>' }
}
