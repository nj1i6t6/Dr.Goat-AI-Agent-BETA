import { vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'

/**
 * 創建測試路由器
 */
export function createTestRouter(routes = []) {
  const defaultRoutes = [
    { path: '/', name: 'Dashboard', component: { template: '<div>Dashboard</div>' } },
    { path: '/login', name: 'Login', component: { template: '<div>Login</div>' } },
    { path: '/sheep', name: 'Sheep', component: { template: '<div>Sheep</div>' } },
    { path: '/consultation', name: 'Consultation', component: { template: '<div>Consultation</div>' } },
    { path: '/data-management', name: 'DataManagement', component: { template: '<div>DataManagement</div>' } },
    ...routes
  ]
  
  const router = createRouter({
    history: createWebHistory(),
    routes: defaultRoutes
  })
  
  // Mock router methods
  router.push = vi.fn().mockResolvedValue()
  router.replace = vi.fn().mockResolvedValue()
  router.go = vi.fn()
  router.back = vi.fn()
  router.forward = vi.fn()
  
  return router
}

/**
 * 創建測試環境
 */
export function createTestEnvironment(options = {}) {
  const router = createTestRouter(options.routes)
  const pinia = createPinia()
  
  // 設置當前路由
  if (options.currentRoute) {
    router.currentRoute.value = {
      path: '/',
      name: 'Dashboard',
      params: {},
      query: {},
      meta: {},
      ...options.currentRoute
    }
  }
  
  return {
    router,
    pinia,
    global: {
      plugins: [router, pinia],
      stubs: {
        'router-link': { template: '<a href="#"><slot /></a>' },
        'router-view': { template: '<div><slot /></div>' },
        'transition': { template: '<div><slot /></div>' },
        'teleport': { template: '<div><slot /></div>' },
        ...options.stubs
      },
      mocks: {
        $route: router.currentRoute.value,
        $router: router,
        ...options.mocks
      },
      provide: {
        ...options.provide
      },
      ...options.global
    }
  }
}

/**
 * 創建 Element Plus 組件 mock
 */
export function createElementPlusMocks() {
  return {
    'el-button': { 
      template: '<button><slot /></button>',
      props: ['type', 'size', 'disabled', 'loading']
    },
    'el-input': { 
      template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
      props: ['modelValue', 'type', 'placeholder', 'disabled'],
      emits: ['update:modelValue', 'change', 'blur', 'focus']
    },
    'el-form': { 
      template: '<form @submit.prevent><slot /></form>',
      props: ['model', 'rules'],
      methods: {
        validate: vi.fn().mockImplementation((callback) => {
          if (callback) callback(true)
          return Promise.resolve(true)
        }),
        validateField: vi.fn(),
        resetFields: vi.fn(),
        clearValidation: vi.fn()
      }
    },
    'el-form-item': { 
      template: '<div class="el-form-item"><slot /></div>',
      props: ['label', 'prop', 'required']
    },
    'el-select': { 
      template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
      props: ['modelValue', 'placeholder', 'disabled', 'clearable'],
      emits: ['update:modelValue', 'change']
    },
    'el-option': { 
      template: '<option :value="value"><slot>{{ label }}</slot></option>',
      props: ['value', 'label', 'disabled']
    },
    'el-card': { 
      template: '<div class="el-card"><div class="el-card__header" v-if="$slots.header"><slot name="header" /></div><div class="el-card__body"><slot /></div></div>',
      props: ['header', 'shadow']
    },
    'el-table': { 
      template: '<table><slot /></table>',
      props: ['data', 'stripe', 'border']
    },
    'el-table-column': { 
      template: '<td><slot /></td>',
      props: ['label', 'prop', 'width', 'align']
    },
    'el-dialog': { 
      template: '<div v-if="modelValue" class="el-dialog"><slot /></div>',
      props: ['modelValue', 'title', 'width'],
      emits: ['update:modelValue']
    },
    'el-tabs': { 
      template: '<div class="el-tabs"><slot /></div>',
      props: ['modelValue', 'type'],
      emits: ['update:modelValue', 'tab-click']
    },
    'el-tab-pane': { 
      template: '<div class="el-tab-pane"><slot /></div>',
      props: ['label', 'name', 'disabled']
    },
    'el-icon': { 
      template: '<i class="el-icon"><slot /></i>',
      props: ['size', 'color']
    },
    'el-upload': { 
      template: '<div class="el-upload"><slot /></div>',
      props: ['action', 'multiple', 'accept', 'beforeUpload'],
      methods: {
        submit: vi.fn(),
        abort: vi.fn()
      }
    },
    'el-steps': { 
      template: '<div class="el-steps"><slot /></div>',
      props: ['active', 'direction', 'alignCenter']
    },
    'el-step': { 
      template: '<div class="el-step"><slot /></div>',
      props: ['title', 'description', 'icon', 'status']
    },
    'el-divider': { 
      template: '<hr class="el-divider" />',
      props: ['direction']
    },
    'el-tag': { 
      template: '<span class="el-tag"><slot /></span>',
      props: ['type', 'size', 'effect', 'closable']
    },
    'el-tooltip': { 
      template: '<div><slot /></div>',
      props: ['content', 'placement', 'disabled']
    },
    'el-popover': { 
      template: '<div><slot /></div>',
      props: ['content', 'trigger', 'placement']
    },
    'el-checkbox': {
      template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
      props: ['modelValue', 'disabled'],
      emits: ['update:modelValue', 'change']
    },
    'el-date-picker': {
      template: '<input type="date" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
      props: ['modelValue', 'type', 'placeholder', 'format'],
      emits: ['update:modelValue', 'change']
    },
    'el-radio': {
      template: '<input type="radio" :checked="modelValue === value" @change="$emit(\'update:modelValue\', value)" />',
      props: ['modelValue', 'value', 'disabled'],
      emits: ['update:modelValue', 'change']
    },
    'el-radio-group': {
      template: '<div class="el-radio-group"><slot /></div>',
      props: ['modelValue', 'disabled'],
      emits: ['update:modelValue', 'change']
    },
    'el-switch': {
      template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
      props: ['modelValue', 'disabled'],
      emits: ['update:modelValue', 'change']
    }
  }
}

/**
 * 掛載組件的輔助函數
 */
export function mountComponent(component, options = {}) {
  const testEnv = createTestEnvironment(options)
  const elementPlusComponents = createElementPlusMocks()
  
  const mountOptions = {
    ...testEnv,
    global: {
      ...testEnv.global,
      stubs: {
        ...elementPlusComponents,
        ...testEnv.global.stubs
      }
    },
    ...options
  }
  
  return mount(component, mountOptions)
}

/**
 * 模擬 API 響應
 */
export function mockApiResponse(data, status = 200) {
  return Promise.resolve({
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {}
  })
}

/**
 * 模擬 API 錯誤
 */
export function mockApiError(message = 'API Error', status = 500) {
  const error = new Error(message)
  error.response = {
    data: { message },
    status,
    statusText: 'Internal Server Error'
  }
  return Promise.reject(error)
}

/**
 * 等待 Vue 響應式更新
 */
export async function nextTick() {
  await new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * 模擬 localStorage
 */
export function mockLocalStorage() {
  const store = {}
  return {
    getItem: vi.fn(key => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn(key => { delete store[key] }),
    clear: vi.fn(() => { Object.keys(store).forEach(key => delete store[key]) })
  }
}
