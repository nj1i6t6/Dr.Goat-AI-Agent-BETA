import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SheepModal from './SheepModal.vue'

// Mock API
vi.mock('../../api', () => ({
  default: {
    getSheepDetails: vi.fn(),
    createSheep: vi.fn(),
    updateSheep: vi.fn()
  }
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

describe('SheepModal', () => {
  let wrapper
  let pinia

  const createWrapper = (props = {}) => {
    pinia = createPinia()
    setActivePinia(pinia)
    
    return mount(SheepModal, {
      props: {
        visible: true,
        earNum: null,
        ...props
      },
      global: {
        plugins: [pinia],
        stubs: {
          'el-dialog': {
            template: '<div class="el-dialog" :modelvalue="modelvalue"><div class="el-dialog__header"><span class="el-dialog__title">{{ title }}</span></div><div class="el-dialog__body"><slot /></div></div>',
            props: ['modelvalue', 'title', 'width', 'beforeClose', 'top', 'class']
          },
          'el-tabs': {
            template: '<div class="el-tabs" :modelvalue="modelvalue"><slot /></div>',
            props: ['modelvalue']
          },
          'el-tab-pane': {
            template: '<div class="el-tab-pane"><div class="el-tab-pane__label">{{ label }}</div><slot /></div>',
            props: ['label', 'name', 'disabled']
          },
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-button': true,
          'BasicInfoTab': {
            template: '<div class="basic-info-tab">基本資料內容</div>'
          },
          'EventsLogTab': {
            template: '<div class="events-log-tab">事件日誌內容</div>'
          },
          'HistoryTab': {
            template: '<div class="history-tab">歷史數據內容</div>'
          }
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    wrapper = createWrapper()
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  describe('組件初始化', () => {
    it('應該正確渲染組件', () => {
      expect(wrapper.exists()).toBe(true)
    })

    it('應該顯示對話框', () => {
      expect(wrapper.html()).toContain('羊隻資料')
    })
  })

  describe('標籤頁管理', () => {
    it('應該渲染基本資料標籤頁', () => {
      expect(wrapper.html()).toContain('基本資料')
    })
  })

  describe('數據處理', () => {
    it('應該處理新增模式', () => {
      const newWrapper = createWrapper({ earNum: null })
      expect(newWrapper.exists()).toBe(true)
    })

    it('應該處理編輯模式', () => {
      const editWrapper = createWrapper({ earNum: 'SH001' })
      expect(editWrapper.exists()).toBe(true)
    })
  })
})
