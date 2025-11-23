import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTraceabilityStore } from '@/stores/traceability'

vi.mock('@/api', () => ({
  default: {
    getTraceabilityBatches: vi.fn(),
    getTraceabilityBatch: vi.fn(),
    createTraceabilityBatch: vi.fn(),
    updateTraceabilityBatch: vi.fn(),
    deleteTraceabilityBatch: vi.fn(),
    replaceBatchSheepLinks: vi.fn(),
    addProcessingStep: vi.fn(),
    updateProcessingStep: vi.fn(),
    deleteProcessingStep: vi.fn()
  }
}))

import api from '@/api'

describe('traceability store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should have correct initial state', () => {
    const store = useTraceabilityStore()
    expect(store.batches).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.selectedBatch).toBeNull()
  })

  it('fetchBatches should populate list', async () => {
    const store = useTraceabilityStore()
    const mockData = [{ id: 1, batch_number: 'B001', product_name: '羊乳' }]
    api.getTraceabilityBatches.mockResolvedValue(mockData)

    await store.fetchBatches(true)

    expect(store.isLoading).toBe(false)
    expect(api.getTraceabilityBatches).toHaveBeenCalledWith(true)
    expect(store.batches).toEqual(mockData)
  })

  it('fetchBatches should skip when already loading', async () => {
    const store = useTraceabilityStore()
    store.isLoading = true

    await store.fetchBatches()

    expect(api.getTraceabilityBatches).not.toHaveBeenCalled()
  })

  it('sortedBatches returns descending by created_at', () => {
    const store = useTraceabilityStore()
    store.batches = [
      { id: 1, created_at: '2024-01-01T00:00:00Z' },
      { id: 2, created_at: '2024-04-01T00:00:00Z' },
      { id: 3, created_at: '2023-12-01T00:00:00Z' }
    ]

    const ids = store.sortedBatches.map(b => b.id)
    expect(ids).toEqual([2, 1, 3])
  })

  it('fetchBatch updates selected batch and list', async () => {
    const store = useTraceabilityStore()
    store.batches = [{ id: 1, batch_number: 'OLD' }]

    const fetched = { id: 1, batch_number: 'UPDATED' }
    api.getTraceabilityBatch.mockResolvedValue(fetched)

    const result = await store.fetchBatch(1)

    expect(result).toEqual(fetched)
    expect(store.selectedBatch).toEqual(fetched)
    expect(store.batches[0]).toEqual(fetched)
  })

  it('fetchBatch inserts when batch not found', async () => {
    const store = useTraceabilityStore()
    store.batches = [{ id: 1, batch_number: 'EXISTING' }]

    const fetched = { id: 2, batch_number: 'NEW' }
    api.getTraceabilityBatch.mockResolvedValue(fetched)

    await store.fetchBatch(2)

    expect(store.batches[0]).toEqual(fetched)
    expect(store.selectedBatch).toEqual(fetched)
  })

  it('createBatch should prepend newly created batch', async () => {
    const store = useTraceabilityStore()
    const created = { id: 5, batch_number: 'B005', product_name: '乳酪' }
    api.createTraceabilityBatch.mockResolvedValue(created)

    await store.createBatch({ batch_number: 'B005', product_name: '乳酪' })

    expect(api.createTraceabilityBatch).toHaveBeenCalledTimes(1)
    expect(store.batches[0]).toEqual(created)
  })

  it('replaceSheepLinks should update selected batch', async () => {
    const store = useTraceabilityStore()
    const existing = { id: 2, batch_number: 'B002', sheep_links: [] }
    store.batches = [existing]
    store.selectedBatch = existing

    const updated = { id: 2, batch_number: 'B002', sheep_links: [{ sheep_id: 1 }] }
    api.replaceBatchSheepLinks.mockResolvedValue(updated)

    await store.replaceSheepLinks(2, [{ sheep_id: 1 }])

    expect(api.replaceBatchSheepLinks).toHaveBeenCalledWith(2, [{ sheep_id: 1 }])
    expect(store.selectedBatch.sheep_links).toHaveLength(1)
    expect(store.batches[0].sheep_links).toHaveLength(1)
  })

  it('updateBatch should merge data and update selected batch', async () => {
    const store = useTraceabilityStore()
    const existing = { id: 3, batch_number: 'B003', steps: [] }
    store.batches = [existing]
    store.selectedBatch = existing

    const updated = { id: 3, batch_number: 'B003-UPDATED', steps: [] }
    api.updateTraceabilityBatch.mockResolvedValue(updated)

    const result = await store.updateBatch(3, { product_name: '新名稱' })

    expect(result).toEqual(updated)
    expect(store.batches[0].batch_number).toBe('B003-UPDATED')
    expect(store.selectedBatch.batch_number).toBe('B003-UPDATED')
  })

  it('deleteBatch removes batch and clears selection', async () => {
    const store = useTraceabilityStore()
    store.batches = [{ id: 4 }, { id: 5 }]
    store.selectedBatch = { id: 5 }

    await store.deleteBatch(5)

    expect(api.deleteTraceabilityBatch).toHaveBeenCalledWith(5)
    expect(store.batches).toEqual([{ id: 4 }])
    expect(store.selectedBatch).toBeNull()
  })

  it('addProcessingStep appends new step when batch selected', async () => {
    const store = useTraceabilityStore()
    store.selectedBatch = { id: 7, steps: [] }

    const newStep = { id: 99, title: '包裝', sequence_order: 1 }
    api.addProcessingStep.mockResolvedValue(newStep)

    const result = await store.addProcessingStep(7, newStep)

    expect(result).toEqual(newStep)
    expect(store.selectedBatch.steps).toContainEqual(newStep)
  })

  it('updateProcessingStep replaces step when found', async () => {
    const store = useTraceabilityStore()
    store.selectedBatch = {
      id: 8,
      steps: [{ id: 1, title: '擠乳' }, { id: 2, title: '冷藏' }]
    }

    const updatedStep = { id: 2, title: '低溫冷藏' }
    api.updateProcessingStep.mockResolvedValue(updatedStep)

    const result = await store.updateProcessingStep(2, { title: '低溫冷藏' })

    expect(result).toEqual(updatedStep)
    expect(store.selectedBatch.steps[1]).toEqual(updatedStep)
  })

  it('deleteProcessingStep removes step from selected batch', async () => {
    const store = useTraceabilityStore()
    store.selectedBatch = {
      id: 9,
      steps: [{ id: 1 }, { id: 2 }]
    }

    await store.deleteProcessingStep(1)

    expect(api.deleteProcessingStep).toHaveBeenCalledWith(1)
    expect(store.selectedBatch.steps).toEqual([{ id: 2 }])
  })
})
