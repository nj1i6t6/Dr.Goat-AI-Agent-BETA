/**
 * TraceabilityManagementView 行為測試
 * @vitest-environment happy-dom
 */

import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { computed, ref } from 'vue'
import TraceabilityManagementView from './TraceabilityManagementView.vue'

const message = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn()
}))

const messageBox = vi.hoisted(() => ({
  confirm: vi.fn()
}))

let traceStoreMock
let sheepStoreMock

const createTraceStoreMock = () => {
  const batches = ref([])
  const selectedBatch = ref(null)
  const isLoading = ref(false)
  const isSaving = ref(false)

  return {
    get batches() {
      return batches.value
    },
    set batches(value) {
      batches.value = value
    },
    get sortedBatches() {
      return [...batches.value]
    },
    get selectedBatch() {
      return selectedBatch.value
    },
    set selectedBatch(value) {
      selectedBatch.value = value
    },
    get isLoading() {
      return isLoading.value
    },
    set isLoading(value) {
      isLoading.value = value
    },
    get isSaving() {
      return isSaving.value
    },
    set isSaving(value) {
      isSaving.value = value
    },
    fetchBatches: vi.fn().mockResolvedValue([]),
    fetchBatch: vi.fn().mockResolvedValue(null),
    createBatch: vi.fn(),
    updateBatch: vi.fn(),
    deleteBatch: vi.fn().mockResolvedValue(),
    replaceSheepLinks: vi.fn(),
    addProcessingStep: vi.fn(),
    updateProcessingStep: vi.fn(),
    deleteProcessingStep: vi.fn().mockResolvedValue(),
    __refs: {
      batches,
      selectedBatch,
      isLoading,
      isSaving
    }
  }
}

const createSheepStoreMock = () => {
  const sheepList = ref([])
  return {
    get sortedSheepList() {
      return sheepList.value
    },
    fetchSheepList: vi.fn().mockResolvedValue([]),
    __refs: {
      sheepList
    }
  }
}

vi.mock('element-plus', () => ({
  ElMessage: message,
  ElMessageBox: messageBox
}))

vi.mock('@element-plus/icons-vue', () => ({
  Plus: { render: () => null }
}))

vi.mock('../stores/traceability', () => ({
  useTraceabilityStore: () => traceStoreMock
}))

vi.mock('../stores/sheep', () => ({
  useSheepStore: () => sheepStoreMock
}))

const mountView = async () => {
  const wrapper = mount(TraceabilityManagementView, {
    global: {
      stubs: {
        'el-button': true,
        'el-card': true,
        'el-switch': true,
        'el-table': true,
        'el-table-column': true,
        'el-tag': true,
        'el-empty': true,
        'el-dialog': true,
        'el-form': {
          template: '<form><slot /></form>'
        },
        'el-form-item': {
          template: '<div><slot /></div>'
        },
        'el-input': true,
        'el-date-picker': true,
        'el-drawer': true,
        'el-row': true,
        'el-col': true,
        'el-select': true,
        'el-option': true,
        'el-divider': true,
        'el-alert': true,
        'el-input-number': true,
        SheepFilter: true,
        SheepTable: true,
        SheepModal: true
      }
    }
  })
  await flushPromises()
  return wrapper
}

beforeAll(() => {
  Object.defineProperty(window, 'location', {
    value: { origin: 'https://example.com' },
    configurable: true
  })

  Object.defineProperty(navigator, 'clipboard', {
    value: {
      writeText: vi.fn()
    },
    configurable: true
  })
})

describe('TraceabilityManagementView', () => {
  beforeEach(() => {
    traceStoreMock = createTraceStoreMock()
    sheepStoreMock = createSheepStoreMock()

    Object.values(message).forEach(fn => fn.mockReset())
    messageBox.confirm.mockReset()
    navigator.clipboard.writeText.mockReset()
  })

  it('handles batch lifecycle operations and date helpers', async () => {
    const createdBatch = {
      id: 1,
      batch_number: 'B-001',
      product_name: '鮮羊乳',
      product_type: '乳品',
      production_date: '2024-01-02',
      expiration_date: '2024-01-10',
      description: '風味香醇',
      esg_highlights: '綠能牧場',
      origin_story: '友善放牧',
      is_public: true
    }

    traceStoreMock.createBatch.mockResolvedValue(createdBatch)
    traceStoreMock.fetchBatch.mockResolvedValue(createdBatch)
    traceStoreMock.updateBatch.mockResolvedValue(createdBatch)

    const wrapper = await mountView()
    wrapper.vm.formRef = { validate: cb => cb(true) }

    wrapper.vm.openCreateForm()
    Object.assign(wrapper.vm.formModel, {
      batch_number: 'B-001',
      product_name: '鮮羊乳',
      product_type: '乳品',
      production_date: new Date('2024-01-02'),
      expiration_date: new Date('2024-01-10'),
      description: '風味香醇',
      esg_highlights: '綠能牧場',
      origin_story: '友善放牧',
      is_public: true
    })

  expect(wrapper.vm.formVisible).toBe(true)

    await wrapper.vm.submitForm()
    await flushPromises()

    expect(traceStoreMock.createBatch).toHaveBeenCalledWith(expect.objectContaining({
      batch_number: 'B-001',
      production_date: '2024-01-02',
      expiration_date: '2024-01-10'
    }))
    expect(wrapper.vm.drawerVisible).toBe(true)
    expect(message.success).toHaveBeenCalledWith('批次建立成功')

  traceStoreMock.selectedBatch = createdBatch
  await flushPromises()
    Object.assign(wrapper.vm.detailForm, {
      product_name: '罐裝鮮羊乳',
      product_type: '乳品',
      description: '每日鮮乳',
      esg_highlights: '太陽能',
      origin_story: '家族牧場',
      is_public: false,
      production_date: new Date('2024-02-01'),
      expiration_date: new Date('2024-02-05')
    })

    await wrapper.vm.saveDetails()
    expect(traceStoreMock.updateBatch).toHaveBeenCalledWith(1, expect.objectContaining({
      product_name: '罐裝鮮羊乳',
      production_date: '2024-02-01'
    }))

    messageBox.confirm.mockResolvedValueOnce()
    traceStoreMock.deleteBatch.mockResolvedValueOnce()
    await wrapper.vm.confirmDelete(createdBatch)
    await flushPromises()

    expect(traceStoreMock.deleteBatch).toHaveBeenCalledWith(1)
    expect(message.success).toHaveBeenCalledWith('批次已刪除')

    await wrapper.vm.refreshList()
    expect(traceStoreMock.fetchBatches).toHaveBeenCalled()

    expect(wrapper.vm.formatDate(null)).toBe('—')
  expect(wrapper.vm.formatDate('invalid-date')).toBe('Invalid Date')
    expect(wrapper.vm.formatDate('2024-01-01')).toMatch(/2024/)

    expect(wrapper.vm.formatDateTime(null)).toBe('—')
  expect(wrapper.vm.formatDateTime('invalid')).toBe('Invalid Date')

    expect(wrapper.vm.formatDateISO(null)).toBeNull()
    expect(wrapper.vm.formatDateISO('2024-01-01')).toBe('2024-01-01')
    expect(wrapper.vm.formatDateISO(new Date('2024-01-15'))).toBe('2024-01-15')

    expect(wrapper.vm.formatDateTimeLocal(null)).toBeNull()
    expect(wrapper.vm.formatDateTimeLocal('bad-date')).toBeNull()
    expect(wrapper.vm.formatDateTimeLocal(new Date('2024-01-01T12:34:56Z'))).toMatch(/^2024-/)
  })

  it('manages sheep linking workflow', async () => {
    traceStoreMock.replaceSheepLinks.mockResolvedValue({})

    const wrapper = await mountView()

    traceStoreMock.selectedBatch = {
      id: 5,
      sheep_links: [
        {
          sheep_id: 1,
          role: '主角',
          contribution_type: '乳品',
          quantity: 2,
          quantity_unit: 'L',
          notes: '人氣羊隻'
        }
      ]
    }

    sheepStoreMock.__refs.sheepList.value = [
      { id: 1, EarNum: 'E001', Breed: 'Boer' },
      { id: 2, EarNum: 'E002', Breed: null }
    ]
    await flushPromises()

    await wrapper.vm.openSheepDialog()
    expect(wrapper.vm.sheepDialogVisible).toBe(true)
    expect(wrapper.vm.selectedSheepIds).toEqual([1])

    wrapper.vm.selectedSheepIds = [1, 2]
    await flushPromises()

    expect(wrapper.vm.sheepLinkDraft).toHaveLength(2)
    expect(wrapper.vm.getSheepLabel(2)).toContain('E002')
    expect(wrapper.vm.getSheepLabel(99)).toContain('ID: 99')

    const draft = wrapper.vm.sheepLinkDraft
    draft[1].role = '後盾'
    draft[1].contribution_type = '肉品'
    draft[1].quantity = '3'
    draft[1].quantity_unit = 'kg'
    draft[1].notes = '補位'

    await wrapper.vm.saveSheepLinks()
    expect(traceStoreMock.replaceSheepLinks).toHaveBeenCalledWith(5, expect.arrayContaining([
      expect.objectContaining({ sheep_id: 2, role: '後盾', quantity: 3, quantity_unit: 'kg' })
    ]))
    expect(wrapper.vm.sheepDialogVisible).toBe(false)
    expect(message.success).toHaveBeenCalledWith('羊隻設定已更新')

    traceStoreMock.replaceSheepLinks.mockRejectedValueOnce(new Error('失敗'))
    await wrapper.vm.saveSheepLinks()
  expect(message.error).toHaveBeenCalledWith('失敗')
  })

  it('handles step workflow, clipboard, and formatting utilities', async () => {
    traceStoreMock.addProcessingStep.mockResolvedValue({ id: 2 })
    traceStoreMock.updateProcessingStep.mockResolvedValue({ id: 1 })
    traceStoreMock.deleteProcessingStep.mockResolvedValue()

    const wrapper = await mountView()

    traceStoreMock.selectedBatch = {
      id: 9,
      steps: [
        {
          id: 1,
          title: '檢驗',
          sequence_order: 1,
          started_at: '2024-01-01T01:00:00Z',
          completed_at: '2024-01-01T02:00:00Z'
        }
      ]
    }
  traceStoreMock.fetchBatch.mockImplementation(async () => traceStoreMock.selectedBatch)
    await flushPromises()

    await wrapper.vm.openAddStepDialog()
    expect(wrapper.vm.stepDialogMode).toBe('create')
    wrapper.vm.stepForm.title = '殺菌'
    wrapper.vm.stepForm.sequence_order = 2
    await wrapper.vm.submitStep()
    expect(traceStoreMock.addProcessingStep).toHaveBeenCalledWith(9, expect.objectContaining({
      title: '殺菌'
    }))
    expect(message.success).toHaveBeenCalledWith('步驟已新增')

  await wrapper.vm.openEditStepDialog(traceStoreMock.selectedBatch.steps[0])
    expect(wrapper.vm.stepDialogMode).toBe('edit')
    wrapper.vm.stepForm.title = '品質檢驗'
    await wrapper.vm.submitStep()
    expect(traceStoreMock.updateProcessingStep).toHaveBeenCalledWith(1, expect.objectContaining({
      title: '品質檢驗'
    }))
    expect(message.success).toHaveBeenCalledWith('步驟已更新')

    wrapper.vm.stepDialogMode = 'create'
    wrapper.vm.stepForm.title = ''
    await wrapper.vm.submitStep()
    expect(message.warning).toHaveBeenCalledWith('請輸入步驟名稱')

    messageBox.confirm.mockResolvedValueOnce()
    await wrapper.vm.confirmDeleteStep({ id: 99, title: '包裝' })
    await flushPromises()
    expect(traceStoreMock.deleteProcessingStep).toHaveBeenCalledWith(99)

    navigator.clipboard.writeText.mockResolvedValueOnce()
    await wrapper.vm.copyPublicLink({ batch_number: 'B-777' })
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://example.com/trace/B-777')
    expect(message.success).toHaveBeenCalledWith('公開連結已複製到剪貼簿')

    navigator.clipboard.writeText.mockRejectedValueOnce(new Error('fail'))
    await wrapper.vm.copyPublicLink({ batch_number: 'B-777' })
    expect(message.error).toHaveBeenCalledWith('無法複製連結，請手動複製')

    expect(wrapper.vm.formatStepTime({
      started_at: '2024-01-01T01:00:00Z',
      completed_at: '2024-01-01T02:00:00Z'
    })).toContain('~')

    expect(wrapper.vm.formatStepTime({ started_at: null, completed_at: null })).toBe('—')
  })
})
