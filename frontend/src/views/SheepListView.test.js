/**
 * SheepListView 行為測試
 * @vitest-environment happy-dom
 */

import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SheepListView from './SheepListView.vue'
import { useSheepStore } from '../stores/sheep'

const routerMock = vi.hoisted(() => ({
  push: vi.fn()
}))

const message = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn()
}))

const messageBox = vi.hoisted(() => ({
  confirm: vi.fn()
}))

const apiMock = vi.hoisted(() => ({
  getAllSheep: vi.fn(),
  deleteSheep: vi.fn()
}))

vi.mock('vue-router', () => ({
  useRouter: () => routerMock
}))

vi.mock('element-plus', () => ({
  ElMessage: message,
  ElMessageBox: messageBox
}))

vi.mock('@element-plus/icons-vue', () => ({
  Tickets: { render: () => null },
  Plus: { render: () => null }
}))

vi.mock('../api', () => ({
  __esModule: true,
  default: apiMock
}))

describe('SheepListView', () => {
  let pinia
  let wrapper

  const SAMPLE_SHEEP = [
    {
      id: 1,
      EarNum: 'A100',
      FarmNum: 'F-01',
      Breed: 'Boer',
      Sex: 'F',
      status: 'healthy',
      breed_category: 'meat',
      BirthDate: '2024-01-10'
    },
    {
      id: 2,
      EarNum: 'B200',
      FarmNum: 'F-02',
      Breed: 'Nubian',
      Sex: 'M',
      status: 'quarantine',
      breed_category: 'milk',
      BirthDate: '2023-12-20'
    }
  ]

  const mountView = async () => {
    wrapper = mount(SheepListView, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-card': true,
          'el-button': true
        }
      }
    })
    await flushPromises()
    return wrapper
  }

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)

    Object.values(message).forEach(fn => fn.mockReset())
  messageBox.confirm.mockReset()
  routerMock.push.mockReset()

    apiMock.getAllSheep.mockReset()
    apiMock.deleteSheep.mockReset()

    apiMock.getAllSheep.mockResolvedValue(structuredClone(SAMPLE_SHEEP))
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('掛載時會載入羊隻列表並更新摘要', async () => {
    const mounted = await mountView()
    const store = useSheepStore()

    expect(apiMock.getAllSheep).toHaveBeenCalledTimes(1)
    expect(store.sheepList).toHaveLength(2)
    expect(mounted.vm.filteredSheep).toHaveLength(2)
    expect(mounted.vm.summaryText).toContain('共 2 隻')
  })

  it('applyFilters 會依條件篩選資料', async () => {
    const mounted = await mountView()
    await mounted.vm.applyFilters({
      earNumSearch: 'a1',
      farmNum: 'F-01',
      breed: 'Boer',
      sex: 'F',
      breedCategory: 'meat',
      status: 'healthy',
      startDate: '2024-01-01',
      endDate: '2024-12-31'
    })

    expect(mounted.vm.filteredSheep).toEqual([
      expect.objectContaining({ EarNum: 'A100' })
    ])

    await mounted.vm.applyFilters({ farmNum: 'F-02' })
    expect(mounted.vm.filteredSheep).toEqual([
      expect.objectContaining({ EarNum: 'B200' })
    ])
  })

  it('openModal 與 closeModal 控制彈窗狀態', async () => {
    const mounted = await mountView()

    mounted.vm.openModal('A100')
    expect(mounted.vm.isModalVisible).toBe(true)
    expect(mounted.vm.editingEarNum).toBe('A100')
    expect(mounted.vm.initialTab).toBe('basicInfoTab')

    mounted.vm.closeModal()
    expect(mounted.vm.isModalVisible).toBe(false)
    expect(mounted.vm.editingEarNum).toBeNull()
  })

  it('openModalWithTab 會設定指定分頁', async () => {
    const mounted = await mountView()
    mounted.vm.openModalWithTab('eventsLogTab', 'B200')
    expect(mounted.vm.initialTab).toBe('eventsLogTab')
    expect(mounted.vm.editingEarNum).toBe('B200')
  })

  it('handleDataUpdated 會重新套用篩選條件', async () => {
    const mounted = await mountView()
    mounted.vm.filters = { farmNum: 'F-02' }
    mounted.vm.filteredSheep = []
    await mounted.vm.handleDataUpdated()

    expect(mounted.vm.filteredSheep).toEqual([
      expect.objectContaining({ FarmNum: 'F-02' })
    ])
  })

  it('確認刪除時會呼叫 API 並更新列表', async () => {
    const mounted = await mountView()
    const store = useSheepStore()

    messageBox.confirm.mockResolvedValueOnce()
    apiMock.deleteSheep.mockResolvedValueOnce({ success: true })

    await mounted.vm.handleDelete('A100')

    expect(messageBox.confirm).toHaveBeenCalled()
    expect(apiMock.deleteSheep).toHaveBeenCalledWith('A100')
    expect(store.sheepList.find(s => s.EarNum === 'A100')).toBeUndefined()
    expect(message.success).toHaveBeenCalledWith('刪除成功')
  })

  it('刪除失敗時會顯示錯誤訊息', async () => {
    const mounted = await mountView()

    messageBox.confirm.mockResolvedValueOnce()
    apiMock.deleteSheep.mockRejectedValueOnce({ message: 'failed' })

    await mounted.vm.handleDelete('A100')

    expect(message.error).toHaveBeenCalled()
  })

  it('取消刪除時不會顯示錯誤', async () => {
    const mounted = await mountView()

    messageBox.confirm.mockRejectedValueOnce('cancel')
    await mounted.vm.handleDelete('A100')

    expect(apiMock.deleteSheep).not.toHaveBeenCalled()
    expect(message.error).not.toHaveBeenCalled()
  })

  it('navigateToConsultation 會導向諮詢頁', async () => {
    const mounted = await mountView()
    mounted.vm.navigateToConsultation('B200')
  expect(routerMock.push).toHaveBeenCalledWith({ name: 'Consultation', query: { earNum: 'B200' } })
  })
})
