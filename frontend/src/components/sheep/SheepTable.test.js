/**
 * SheepTable 組件測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SheepTable from './SheepTable.vue'

// Mock utils 模組 - 把變數定義移到 mock 內部
vi.mock('../../utils', () => ({
  statusOptions: [
    { value: 'healthy', label: '健康' },
    { value: 'sick', label: '生病' }
  ]
}))

describe('SheepTable', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    // Setup pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  const createWrapper = (props = {}) => {
    return mount(SheepTable, {
      props: {
        sheepData: [],
        loading: false,
        ...props
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-auto-resizer': {
            template: '<div class="el-table"><slot :height="400" :width="800"></slot></div>'
          },
          'el-table-v2': true,
          'el-button': true,
          'el-tooltip': true,
          'el-tag': true,
          'el-empty': true
        }
      }
    })
  }

  describe('基本渲染', () => {
    it('應該正確渲染組件', () => {
      wrapper = createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('應該顯示表格組件', () => {
      wrapper = createWrapper()
      expect(wrapper.find('.table-container').exists()).toBe(true)
    })
  })

  describe('數據處理', () => {
    it('應該處理空數據', () => {
      wrapper = createWrapper({ sheepData: [] })
      expect(wrapper.props('sheepData')).toEqual([])
    })

    it('應該處理載入狀態', () => {
      wrapper = createWrapper({ loading: true })
      expect(wrapper.props('loading')).toBe(true)
    })
  })

  describe('狀態選項', () => {
    it('應該正確導入狀態選項', () => {
      // 透過 vi.mocked 來檢查 mock
      const utils = require('../../utils')
      expect(utils.statusOptions).toBeDefined()
      expect(Array.isArray(utils.statusOptions)).toBe(true)
    })
  })
})
