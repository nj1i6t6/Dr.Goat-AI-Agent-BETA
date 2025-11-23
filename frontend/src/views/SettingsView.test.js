/**
 * SettingsView 行為測試
 * @vitest-environment happy-dom
 */

import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SettingsView from './SettingsView.vue'
import { useSettingsStore, FONT_SCALE } from '../stores/settings'

const message = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn()
}))

const apiMock = vi.hoisted(() => ({
  getAgentTip: vi.fn(),
  getEventOptions: vi.fn(),
  addEventType: vi.fn(),
  deleteEventType: vi.fn(),
  addEventDescription: vi.fn(),
  deleteEventDescription: vi.fn()
}))

vi.mock('element-plus', () => ({
  ElMessage: message
}))

vi.mock('@element-plus/icons-vue', () => ({
  Setting: { render: () => null },
  Plus: { render: () => null },
  Delete: { render: () => null }
}))

vi.mock('../api', () => ({
  __esModule: true,
  default: apiMock
}))

describe('SettingsView', () => {
  let pinia
  let wrapper

  const mountView = async () => {
    wrapper = mount(SettingsView, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><slot name="header"></slot><slot></slot></div>'
          },
          'el-input': true,
          'el-button': true,
          'el-radio-group': {
            props: ['modelValue'],
            template: '<div class="el-radio-group"><slot></slot></div>'
          },
          'el-radio-button': {
            template: '<button class="el-radio-button"><slot></slot></button>'
          },
          'el-collapse': true,
          'el-collapse-item': true,
          'el-empty': true,
          'el-tag': true,
          'el-popconfirm': {
            template: '<div><slot></slot><slot name="reference"></slot></div>'
          },
          'el-icon': true
        }
      }
    })
    await flushPromises()
    return wrapper
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    Object.values(apiMock).forEach(fn => fn.mockReset())
    Object.values(message).forEach(fn => fn.mockReset())

    localStorage.getItem.mockReset()
    localStorage.setItem.mockReset()
    localStorage.removeItem.mockReset()
    document.documentElement.dataset.fontScale = FONT_SCALE.DEFAULT
    localStorage.getItem.mockImplementation((key) => {
      if (key === 'geminiApiKey') return ''
      if (key === 'uiFontScale') return FONT_SCALE.DEFAULT
      return null
    })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('載入時取得事件選項並初始化狀態', async () => {
    const optionData = [{
      id: 'type-1',
      name: '健康檢查',
      is_default: true,
      descriptions: [{ id: 'desc-1', description: '量體重', is_default: true }]
    }]
    apiMock.getEventOptions.mockResolvedValue(optionData)

    const mounted = await mountView()

    expect(apiMock.getEventOptions).toHaveBeenCalledTimes(1)
    expect(mounted.vm.eventOptions).toEqual(optionData)
    expect(mounted.vm.newDescriptions['type-1']).toBe('')
    expect(mounted.vm.apiKeyStatus.type).toBe('error')
  })

  it('成功測試並儲存 API 金鑰', async () => {
    apiMock.getEventOptions.mockResolvedValue([])
    apiMock.getAgentTip.mockResolvedValue({ tip_html: '<p>hello</p>' })

    const mounted = await mountView()
    const store = useSettingsStore()

    mounted.vm.apiKeyInput = 'valid-key'
    await mounted.vm.handleTestAndSaveApiKey()

    expect(apiMock.getAgentTip).toHaveBeenCalledWith('valid-key')
    expect(store.apiKey).toBe('valid-key')
    expect(mounted.vm.apiKeyStatus.type).toBe('success')
    expect(message.success).toHaveBeenCalledTimes(1)
    expect(localStorage.setItem).toHaveBeenCalledWith('geminiApiKey', 'valid-key')
  })

  it('API 金鑰驗證失敗時會清除狀態', async () => {
    apiMock.getEventOptions.mockResolvedValue([])
    apiMock.getAgentTip.mockRejectedValue(new Error('bad key'))

    const mounted = await mountView()
    const store = useSettingsStore()
    store.setApiKey('old-key')

    mounted.vm.apiKeyInput = 'invalid'
    await mounted.vm.handleTestAndSaveApiKey()

    expect(apiMock.getAgentTip).toHaveBeenCalledWith('invalid')
    expect(store.apiKey).toBe('')
    expect(mounted.vm.apiKeyStatus.type).toBe('error')
    expect(message.error).toHaveBeenCalled()
    expect(localStorage.removeItem).toHaveBeenCalledWith('geminiApiKey')
  })

  it('新增事件類型會刷新列表', async () => {
    apiMock.getEventOptions
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{ id: 'type-2', name: '免疫', is_default: false, descriptions: [] }])
    apiMock.addEventType.mockResolvedValue({ success: true })

    const mounted = await mountView()
    mounted.vm.newEventType = '免疫'
    await mounted.vm.handleAddEventType()

    expect(apiMock.addEventType).toHaveBeenCalledWith('免疫')
    expect(apiMock.getEventOptions).toHaveBeenCalledTimes(2)
    expect(message.success).toHaveBeenCalled()
    expect(mounted.vm.newEventType).toBe('')
  })

  it('新增或刪除事件描述時會同步更新', async () => {
    apiMock.getEventOptions.mockResolvedValue([{ id: 'type-1', name: '健檢', is_default: false, descriptions: [] }])
    apiMock.addEventDescription.mockResolvedValue({})
    apiMock.deleteEventDescription.mockResolvedValue({})

    const mounted = await mountView()
    mounted.vm.newDescriptions['type-1'] = '抽血檢查'
    await mounted.vm.handleAddDescription('type-1')

    expect(apiMock.addEventDescription).toHaveBeenCalledWith('type-1', '抽血檢查')
    expect(mounted.vm.newDescriptions['type-1']).toBe('')
    expect(message.success).toHaveBeenCalledTimes(1)

    await mounted.vm.handleDeleteDescription('desc-1')
    expect(apiMock.deleteEventDescription).toHaveBeenCalledWith('desc-1')
    expect(message.success).toHaveBeenCalledTimes(2)
  })

  it('切換字體大小會更新 store 並套用到文件', async () => {
    apiMock.getEventOptions.mockResolvedValue([])

    const mounted = await mountView()
    const store = useSettingsStore()

    expect(store.fontScale).toBe(FONT_SCALE.DEFAULT)
    expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.DEFAULT)

    mounted.vm.fontScaleValue = FONT_SCALE.LARGE
    await mounted.vm.$nextTick()

    expect(store.fontScale).toBe(FONT_SCALE.LARGE)
    expect(localStorage.setItem).toHaveBeenCalledWith('uiFontScale', FONT_SCALE.LARGE)
    expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.LARGE)

    mounted.vm.fontScaleValue = FONT_SCALE.DEFAULT
    await mounted.vm.$nextTick()

    expect(store.fontScale).toBe(FONT_SCALE.DEFAULT)
    expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.DEFAULT)

    mounted.vm.fontScaleValue = FONT_SCALE.EXTRA_LARGE
    await mounted.vm.$nextTick()

    expect(store.fontScale).toBe(FONT_SCALE.EXTRA_LARGE)
    expect(localStorage.setItem).toHaveBeenCalledWith('uiFontScale', FONT_SCALE.EXTRA_LARGE)
    expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.EXTRA_LARGE)
  })

  it('顯示三種字級預覽', async () => {
    apiMock.getEventOptions.mockResolvedValue([])

    await mountView()

    const previewCards = wrapper.findAll('.preview-card')
    expect(previewCards).toHaveLength(3)
    expect(previewCards[0].text()).toContain('預設字級')
    expect(previewCards[1].text()).toContain('大字級')
    expect(previewCards[2].text()).toContain('超大字級')
  })

  it('刪除自訂事件類型會呼叫 API', async () => {
    apiMock.getEventOptions.mockResolvedValue([])
    apiMock.deleteEventType.mockResolvedValue({})

    const mounted = await mountView()
    await mounted.vm.handleDeleteType('type-42')

    expect(apiMock.deleteEventType).toHaveBeenCalledWith('type-42')
    expect(message.success).toHaveBeenCalled()
  })

  it('表單驗證未通過時顯示警告', async () => {
    apiMock.getEventOptions.mockResolvedValue([{ id: 'type-1', name: '健檢', is_default: false, descriptions: [] }])
    const mounted = await mountView()

    mounted.vm.newEventType = '   '
    await mounted.vm.handleAddEventType()
    expect(message.warning).toHaveBeenCalledWith('請輸入事件類型名稱')

    mounted.vm.newDescriptions['type-1'] = '   '
    await mounted.vm.handleAddDescription('type-1')
    expect(message.warning).toHaveBeenCalledWith('請輸入簡要描述內容')
  })

  it('updateApiKeyStatus 會根據 store 狀態更新訊息', async () => {
    apiMock.getEventOptions.mockResolvedValue([])
    const mounted = await mountView()
    const store = useSettingsStore()

    expect(mounted.vm.apiKeyStatus.type).toBe('error')

    store.setApiKey('persisted')
    mounted.vm.updateApiKeyStatus()

    expect(mounted.vm.apiKeyStatus.type).toBe('success')
    expect(mounted.vm.apiKeyStatus.message).toContain('已載入儲存的 API 金鑰')
  })
})
