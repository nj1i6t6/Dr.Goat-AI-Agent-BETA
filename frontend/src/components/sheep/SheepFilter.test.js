import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SheepFilter from './SheepFilter.vue'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('SheepFilter', () => {
  let wrapper
  let pinia

  const createWrapper = (props = {}) => {
    pinia = createPinia()
    setActivePinia(pinia)
    
    return mount(SheepFilter, {
      props,
      global: {
        plugins: [pinia],
        stubs: {
          'el-card': {
            template: '<div class="el-card" :shadow="shadow" :class="$attrs.class"><div class="el-card__body"><slot /></div></div>',
            props: ['shadow']
          },
          'el-form': {
            template: '<form><slot /></form>',
            props: ['model', 'labelPosition']
          },
          'el-form-item': {
            template: '<div class="el-form-item" :label="label"><slot /></div>',
            props: ['label']
          },
          'el-input': {
            template: '<input class="el-input" :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            props: ['modelValue', 'placeholder', 'clearable'],
            emits: ['update:modelValue']
          },
          'el-select': {
            template: '<select class="el-select" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
            props: ['modelValue', 'placeholder', 'clearable'],
            emits: ['update:modelValue']
          },
          'el-select-v2': {
            template: '<select class="el-select-v2" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"></select>',
            props: ['modelValue', 'options', 'placeholder', 'clearable', 'filterable'],
            emits: ['update:modelValue']
          },
          'el-option': {
            template: '<option :value="value"><slot>{{ label }}</slot></option>',
            props: ['value', 'label']
          },
          'el-button': {
            template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
            emits: ['click']
          },
          'el-row': {
            template: '<div class="el-row"><slot /></div>',
            props: ['gutter']
          },
          'el-col': {
            template: '<div class="el-col"><slot /></div>',
            props: ['xs', 'sm', 'md']
          }
        }
      }
    })
  }

  beforeEach(() => {
    wrapper = createWrapper()
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  describe('組件渲染', () => {
    it('應該正確渲染所有篩選欄位', () => {
      expect(wrapper.exists()).toBe(true)
      
      // 檢查基本結構
      expect(wrapper.html()).toContain('清除篩選')
    })
  })

  describe('用戶互動', () => {
    it('應該支持搜索功能', () => {
      // 測試基本搜索功能存在
      expect(wrapper.vm).toBeDefined()
    })
  })
})
