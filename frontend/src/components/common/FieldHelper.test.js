import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FieldHelper from './FieldHelper.vue'

// Mock Element Plus icons
vi.mock('@element-plus/icons-vue', () => ({
  QuestionFilled: { 
    name: 'QuestionFilled',
    template: '<span class="question-icon">?</span>' 
  }
}))

describe('FieldHelper', () => {
  let wrapper

  const createWrapper = (props = {}) => {
    return mount(FieldHelper, {
      props: {
        content: 'Test help text',
        ...props
      },
      global: {
        stubs: {
          'el-tooltip': {
            template: '<div class="el-tooltip"><slot></slot></div>',
            props: ['content', 'placement', 'disabled', 'text']
          },
          'el-icon': {
            template: '<i class="field-helper-icon"><slot></slot></i>'
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

  describe('組件初始化', () => {
    it('應該正確渲染組件', () => {
      expect(wrapper.exists()).toBe(true)
    })

    it('應該包含說明文字', () => {
      expect(wrapper.vm.content).toBe('Test help text')
    })

    it('應該包含問號圖標', () => {
      // 由於使用了 stub，檢查基本結構
      expect(wrapper.html()).toContain('field-helper-icon')
    })
  })

  describe('屬性測試', () => {
    it('應該接受content屬性', () => {
      const customWrapper = createWrapper({ content: 'Custom help text' })
      expect(customWrapper.vm.content).toBe('Custom help text')
      customWrapper.unmount()
    })

    it('應該處理空的content屬性', () => {
      const emptyWrapper = createWrapper({ content: '' })
      expect(emptyWrapper.vm.content).toBe('')
      emptyWrapper.unmount()
    })
  })

  describe('組件結構', () => {
    it('應該有正確的DOM結構', () => {
      expect(wrapper.find('.field-helper-icon').exists()).toBe(true)
    })
  })

  describe('性能考量', () => {
    it('應該是輕量級組件', () => {
      const html = wrapper.html()
      // 調整期望值，因為Element Plus stubs會增加一些HTML
      expect(html.length).toBeLessThan(2000)
    })
  })
})
