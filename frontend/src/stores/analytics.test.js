import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const apiMock = vi.hoisted(() => ({
  listCostEntries: vi.fn(),
  listRevenueEntries: vi.fn(),
  createCostEntry: vi.fn(),
  updateCostEntry: vi.fn(),
  deleteCostEntry: vi.fn(),
  createRevenueEntry: vi.fn(),
  updateRevenueEntry: vi.fn(),
  deleteRevenueEntry: vi.fn(),
  runCohortAnalysis: vi.fn(),
  runCostBenefit: vi.fn(),
  generateAnalyticsReport: vi.fn(),
}))

vi.mock('../api', () => ({
  default: apiMock,
}))

import { useAnalyticsStore } from './analytics'

describe('analytics store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    apiMock.listCostEntries.mockResolvedValue({ items: [] })
    apiMock.listRevenueEntries.mockResolvedValue({ items: [] })
    apiMock.createCostEntry.mockResolvedValue({ id: 1, category: 'feed' })
    apiMock.updateCostEntry.mockResolvedValue({ id: 1, category: 'feed' })
    apiMock.createRevenueEntry.mockResolvedValue({ id: 2, category: 'milk' })
    apiMock.updateRevenueEntry.mockResolvedValue({ id: 2, category: 'milk' })
    apiMock.runCohortAnalysis.mockResolvedValue({ metrics: [], items: [] })
    apiMock.runCostBenefit.mockResolvedValue({ summary: {}, items: [], metrics: [] })
    apiMock.generateAnalyticsReport.mockResolvedValue({ report_html: '<p>ok</p>', report_markdown: 'ok' })
  })

  it('loads cost entries and updates state', async () => {
    apiMock.listCostEntries.mockResolvedValueOnce({ total: 1, items: [{ id: 1, category: 'feed' }] })
    const store = useAnalyticsStore()
    await store.loadCostEntries()
    expect(store.costEntries).toHaveLength(1)
    expect(apiMock.listCostEntries).toHaveBeenCalledTimes(1)
  })

  it('throttles repeated cohort calls', async () => {
    const store = useAnalyticsStore()
    apiMock.runCohortAnalysis.mockResolvedValue({ metrics: ['sheep_count'], items: [] })
    const payload = { cohort_by: ['breed'] }
    await store.fetchCohortAnalysis(payload)
    await store.fetchCohortAnalysis(payload)
    expect(apiMock.runCohortAnalysis).toHaveBeenCalledTimes(1)
  })

  it('stores report output', async () => {
    const store = useAnalyticsStore()
    await store.generateReport({ apiKey: 'key', filters: { category: ['feed'] } })
    expect(store.reportState.html).toContain('<p>ok</p>')
    expect(apiMock.generateAnalyticsReport).toHaveBeenCalledWith(
      { filters: { category: ['feed'] } },
      'key',
      expect.any(Function)
    )
  })

  it('optimistically adds cost entry after creation', async () => {
    const store = useAnalyticsStore()
    apiMock.createCostEntry.mockResolvedValueOnce({ id: 10, category: 'hay' })
    await store.saveCostEntry({ category: 'hay' })
    expect(store.costEntries[0]).toMatchObject({ id: 10, category: 'hay' })
    expect(apiMock.listCostEntries).not.toHaveBeenCalled()
  })

  it('updates cost entry in place when editing', async () => {
    const store = useAnalyticsStore()
    store.costEntries = [{ id: 3, category: 'grain' }]
    apiMock.updateCostEntry.mockResolvedValueOnce({ id: 3, category: 'supplement' })
    await store.saveCostEntry({ id: 3, category: 'supplement' })
    expect(store.costEntries[0]).toMatchObject({ id: 3, category: 'supplement' })
  })

  it('optimistically adds revenue entry after creation', async () => {
    const store = useAnalyticsStore()
    apiMock.createRevenueEntry.mockResolvedValueOnce({ id: 20, category: 'cheese' })
    await store.saveRevenueEntry({ category: 'cheese' })
    expect(store.revenueEntries[0]).toMatchObject({ id: 20, category: 'cheese' })
    expect(apiMock.listRevenueEntries).not.toHaveBeenCalled()
  })

  it('updates revenue entry in place when editing', async () => {
    const store = useAnalyticsStore()
    store.revenueEntries = [{ id: 4, category: 'milk' }]
    apiMock.updateRevenueEntry.mockResolvedValueOnce({ id: 4, category: 'yogurt' })
    await store.saveRevenueEntry({ id: 4, category: 'yogurt' })
    expect(store.revenueEntries[0]).toMatchObject({ id: 4, category: 'yogurt' })
  })
})
