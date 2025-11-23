// 全局測試設置文件
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock Vue Router 完全避免循環依賴
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    createRouter: vi.fn(() => ({
      push: vi.fn().mockResolvedValue(),
      replace: vi.fn().mockResolvedValue(),
      go: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      beforeEach: vi.fn(),
      currentRoute: {
        value: {
          path: '/',
          name: 'Dashboard',
          params: {},
          query: {},
          meta: {}
        }
      }
    })),
    createWebHistory: vi.fn(),
    useRouter: vi.fn(() => ({
      push: vi.fn().mockResolvedValue(),
      replace: vi.fn().mockResolvedValue(),
      go: vi.fn(),
      back: vi.fn(),
      forward: vi.fn()
    })),
    useRoute: vi.fn(() => ({
      path: '/',
      name: 'Dashboard',
      params: {},
      query: {},
      meta: {}
    }))
  }
})

// Mock Pinia Store 避免循環依賴
vi.mock('pinia', async () => {
  const actual = await vi.importActual('pinia')
  return {
    ...actual,
    defineStore: vi.fn((id, setup) => {
      // 為每個 store 創建一個模擬版本
      return vi.fn(() => {
        if (typeof setup === 'function') {
          return setup()
        }
        return setup
      })
    }),
    createPinia: vi.fn(() => ({})),
    setActivePinia: vi.fn()
  }
})

// Mock Auth Store 避免循環依賴
vi.mock('../stores/auth', () => ({
  useAuthStore: vi.fn(() => ({
    user: { value: null },
    isAuthenticated: { value: false },
    username: { value: '訪客' },
    login: vi.fn().mockResolvedValue({ success: true }),
    register: vi.fn().mockResolvedValue({ success: true }),
    logout: vi.fn().mockResolvedValue()
  }))
}))

// Configure Element Plus components globally
config.global.components = {
  'el-button': { template: '<button><slot /></button>' },
  'el-input': { 
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-form': { 
    template: '<form><slot /></form>',
    methods: {
      validate: vi.fn().mockResolvedValue(true),
      validateField: vi.fn(),
      resetFields: vi.fn(),
      clearValidation: vi.fn()
    }
  },
  'el-form-item': { template: '<div><slot /></div>' },
  'el-select': { 
    template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-option': { template: '<option><slot /></option>' },
  'el-card': { template: '<div class="el-card"><slot /></div>' },
  'el-table': { template: '<table><slot /></table>' },
  'el-table-column': { template: '<td><slot /></td>' },
  'el-dialog': { 
    template: '<div v-if="modelValue" class="el-dialog"><slot /></div>',
    props: ['modelValue']
  },
  'el-tabs': { template: '<div class="el-tabs"><slot /></div>' },
  'el-tab-pane': { template: '<div class="el-tab-pane"><slot /></div>' },
  'el-icon': { template: '<i class="el-icon"><slot /></i>' },
  'el-upload': { template: '<div class="el-upload"><slot /></div>' },
  'el-steps': { template: '<div class="el-steps"><slot /></div>' },
  'el-step': { template: '<div class="el-step"><slot /></div>' },
  'el-divider': { template: '<hr class="el-divider" />' },
  'el-tag': { template: '<span class="el-tag"><slot /></span>' },
  'el-tooltip': { template: '<div><slot /></div>' },
  'el-popover': { template: '<div><slot /></div>' },
  'el-checkbox': {
    template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-date-picker': {
    template: '<input type="date" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-radio': {
    template: '<input type="radio" :checked="modelValue === value" @change="$emit(\'update:modelValue\', value)" />',
    props: ['modelValue', 'value'],
    emits: ['update:modelValue']
  },
  'el-radio-group': {
    template: '<div class="el-radio-group"><slot /></div>',
    props: ['modelValue'],
    emits: ['update:modelValue']
  },
  'el-switch': {
    template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
    props: ['modelValue'],
    emits: ['update:modelValue']
  }
}

// Configure global directives
config.global.directives = {
  loading: {
    mounted: vi.fn(),
    updated: vi.fn(),
    unmounted: vi.fn()
  }
}

// Mock Element Plus 全局組件和指令
global.Element = {
  prototype: {
    $message: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    }
  }
}

// Mock Element Plus message service
global.ElMessage = {
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn()
}

// Mock DOM APIs
global.URL = {
  createObjectURL: vi.fn(() => 'mocked-url'),
  revokeObjectURL: vi.fn()
}

global.document = {
  ...global.document,
  createElement: vi.fn(() => ({
    href: '',
    download: '',
    click: vi.fn()
  }))
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))
