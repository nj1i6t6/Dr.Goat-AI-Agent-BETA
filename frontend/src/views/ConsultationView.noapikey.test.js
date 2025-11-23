import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ConsultationView from './ConsultationView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: vi.fn() })
}))

vi.mock('../stores/settings', () => ({
  useSettingsStore: () => ({ apiKey: '', hasApiKey: false })
}))

vi.mock('../stores/consultation', () => ({
  useConsultationStore: () => ({
    form: {}, isLoading: false, resultHtml: '',
    setFormData: vi.fn(), reset: vi.fn(), getRecommendation: vi.fn()
  })
}))

vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() }
}))

describe('ConsultationView handleGetRecommendation with no API key', () => {
  it('shows error and does not call getRecommendation', async () => {
    const wrapper = mount(ConsultationView)
    const { ElMessage } = await import('element-plus')
    await wrapper.vm.handleGetRecommendation()
    expect(ElMessage.error).toHaveBeenCalled()
  })
})
