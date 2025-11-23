import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ConsultationView from './ConsultationView.vue'

vi.mock('../stores/settings', () => ({
  useSettingsStore: () => ({ apiKey: 'k', hasApiKey: true })
}))

const mockSetFormData = vi.fn()
const mockReset = vi.fn()
const mockGetRec = vi.fn()
vi.mock('../stores/consultation', () => ({
  useConsultationStore: () => ({
    form: {
      EarNum: '', Breed: '', Sex: '', BirthDate: '',
      Body_Weight_kg: 0, Age_Months: 0, breed_category: '', status: '',
      status_description: '', target_average_daily_gain_g: 0,
      milk_yield_kg_day: 0, milk_fat_percentage: 0, number_of_fetuses: 1,
      activity_level: '', other_remarks: '', optimization_goal: 'balanced'
    },
    isLoading: false,
    resultHtml: '',
    setFormData: mockSetFormData,
    reset: mockReset,
    getRecommendation: mockGetRec
  })
}))

vi.mock('../api', () => ({
  default: {
    getSheepDetails: vi.fn()
  }
}))

const mockReplace = vi.fn()
let mockQuery = {}
vi.mock('vue-router', () => ({
  useRoute: () => ({ query: mockQuery }),
  useRouter: () => ({ replace: mockReplace })
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() }
}))

describe('ConsultationView behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loadSheepData success formats date and sets form', async () => {
    const api = (await import('../api')).default
    api.getSheepDetails.mockResolvedValue({ EarNum: 'E1', BirthDate: '2024-01-02 00:00:00' })
    const wrapper = mount(ConsultationView)
    wrapper.vm.earNumInput = 'E1'
    await wrapper.vm.loadSheepData()
    expect(mockSetFormData).toHaveBeenCalled()
    const { ElMessage } = await import('element-plus')
    expect(ElMessage.success).toHaveBeenCalled()
  })

  it('loadSheepData error resets but keeps EarNum', async () => {
    const api = (await import('../api')).default
    api.getSheepDetails.mockRejectedValue(new Error('x'))
    const wrapper = mount(ConsultationView)
    wrapper.vm.earNumInput = 'E2'
    await wrapper.vm.loadSheepData()
    expect(mockReset).toHaveBeenCalled()
    expect(wrapper.vm.consultationStore.form.EarNum).toBe('E2')
    const { ElMessage } = await import('element-plus')
    expect(ElMessage.error).toHaveBeenCalled()
  })

  it('handleGetRecommendation validates and calls store', async () => {
    const wrapper = mount(ConsultationView, {
      global: {
        stubs: {
          'el-form': {
            template: '<form><slot /></form>',
            methods: { validate: (fn) => fn(true) }
          }
        }
      }
    })
    // inject fake formRef.validate
    wrapper.vm.formRef = { validate: (fn) => fn(true) }
    await wrapper.vm.handleGetRecommendation()
    expect(mockGetRec).toHaveBeenCalled()
  })

  it('handleResetForm clears input and resets store', async () => {
    const wrapper = mount(ConsultationView)
    wrapper.vm.earNumInput = 'E3'
    wrapper.vm.handleResetForm()
    expect(wrapper.vm.earNumInput).toBe('')
    expect(mockReset).toHaveBeenCalled()
  })

  it('onMounted pre-fills from route query and calls router.replace', async () => {
    mockQuery = { earNum: 'E9' }
    const api = (await import('../api')).default
    api.getSheepDetails.mockResolvedValue({ EarNum: 'E9', BirthDate: '2024-01-02' })
    const wrapper = mount(ConsultationView)
    // 等待掛載後觸發的載入
    await Promise.resolve()
    expect(wrapper.vm.earNumInput).toBe('E9')
    expect(mockReplace).toHaveBeenCalledWith({ query: {} })
    mockQuery = {}
  })

  it('status toggles show/hide production params', async () => {
    const wrapper = mount(ConsultationView)
    wrapper.vm.consultationStore.form.status = 'growing_young'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.isGrowing).toBeTruthy()
    wrapper.vm.consultationStore.form.status = 'lactating_peak'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.isLactating).toBeTruthy()
    wrapper.vm.consultationStore.form.status = 'gestating_late'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.isGestating).toBeTruthy()
    expect(wrapper.vm.showProductionParams).toBeTruthy()
  })

  it('handleGetRecommendation validate returns false shows warning', async () => {
    const { ElMessage } = await import('element-plus')
    const wrapper = mount(ConsultationView)
    // stub validate false
    wrapper.vm.formRef = { validate: (fn) => fn(false) }
    await wrapper.vm.handleGetRecommendation()
    expect(ElMessage.warning).toHaveBeenCalled()
  })

  it('loadSheepData with empty input shows warning and returns early', async () => {
    const { ElMessage } = await import('element-plus')
    const wrapper = mount(ConsultationView)
    wrapper.vm.earNumInput = ''
    await wrapper.vm.loadSheepData()
    expect(ElMessage.warning).toHaveBeenCalled()
  })
})
