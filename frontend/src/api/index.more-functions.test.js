import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => {
  const handlers = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
  return {
    default: {
      create: () => ({
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
        withCredentials: true,
        get: handlers.get,
        post: handlers.post,
        put: handlers.put,
        delete: handlers.delete
      })
    }
  }
})

vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn(() => ({ message: 'formatted', fields: { x: 'y' } }))
}))

describe('api all functions smoke (functions coverage)', () => {
  let api, axiosInst

  beforeEach(async () => {
    vi.resetModules()
    const axiosMod = await import('axios')
    axiosInst = axiosMod.default.create()
    axiosInst.get.mockReset()
    axiosInst.post.mockReset()
    axiosInst.put.mockReset()
    axiosInst.delete.mockReset()
    api = (await import('./index.js')).default
  })

  it('auth + sheep CRUD + events/history + dashboard', async () => {
    axiosInst.post.mockResolvedValueOnce({ ok: true }) // login
    axiosInst.post.mockResolvedValueOnce({ ok: true }) // register
    axiosInst.post.mockResolvedValueOnce({ ok: true }) // logout
    axiosInst.get.mockResolvedValueOnce({ ok: true }) // status

    axiosInst.get.mockResolvedValueOnce([]) // getAllSheep
    axiosInst.get.mockResolvedValueOnce({ EarNum: 'E1' }) // getSheepDetails
    axiosInst.post.mockResolvedValueOnce({ id: 1 }) // addSheep
    axiosInst.put.mockResolvedValueOnce({ ok: true }) // updateSheep
    axiosInst.delete.mockResolvedValueOnce({ ok: true }) // deleteSheep

    axiosInst.get.mockResolvedValueOnce([]) // getSheepEvents
    axiosInst.post.mockResolvedValueOnce({}) // addSheepEvent
    axiosInst.put.mockResolvedValueOnce({}) // updateSheepEvent
    axiosInst.delete.mockResolvedValueOnce({}) // deleteSheepEvent

    axiosInst.get.mockResolvedValueOnce([]) // getSheepHistory
    axiosInst.delete.mockResolvedValueOnce({}) // deleteSheepHistory

    axiosInst.get.mockResolvedValueOnce({}) // getDashboardData
    axiosInst.get.mockResolvedValueOnce({}) // getFarmReport

    await api.login({ u: 'a' })
    await api.register({ u: 'b' })
    await api.logout()
    await api.getAuthStatus()

    await api.getAllSheep()
    await api.getSheepDetails('E1')
    await api.addSheep({})
    await api.updateSheep('E1', {})
    await api.deleteSheep('E1')

    await api.getSheepEvents('E1')
    await api.addSheepEvent('E1', {})
    await api.updateSheepEvent(2, {})
    await api.deleteSheepEvent(2)

    await api.getSheepHistory('E1')
    await api.deleteSheepHistory(3)

    await api.getDashboardData()
    await api.getFarmReport()

    expect(axiosInst.get).toHaveBeenCalled()
    expect(axiosInst.post).toHaveBeenCalled()
  })

  it('data management + event options + prediction + agent', async () => {
    axiosInst.get.mockResolvedValueOnce({ data: new Blob() }) // exportExcel (blob path ignored in mock)
    axiosInst.post.mockResolvedValueOnce({ ok: true }) // analyzeExcel
    axiosInst.post.mockResolvedValueOnce({ ok: true }) // processImport default mode
    axiosInst.post.mockResolvedValueOnce({ ok: true }) // processImport mapping mode

    axiosInst.get.mockResolvedValueOnce([]) // getEventOptions
    axiosInst.post.mockResolvedValueOnce({}) // addEventType
    axiosInst.delete.mockResolvedValueOnce({}) // deleteEventType
    axiosInst.post.mockResolvedValueOnce({}) // addEventDescription
    axiosInst.delete.mockResolvedValueOnce({}) // deleteEventDescription

    axiosInst.get.mockResolvedValueOnce({ chart: true }) // getPredictionChartData
    axiosInst.get.mockResolvedValueOnce({ ok: true }) // getSheepPrediction

    axiosInst.get.mockResolvedValueOnce({ tip: 'x' }) // getAgentTip
    axiosInst.post.mockResolvedValueOnce({ rec: 'y' }) // getRecommendation
    axiosInst.post.mockResolvedValueOnce({ reply_html: 'ok' }) // chatWithAgent json

    await api.exportExcel()
    await api.analyzeExcel(new File(["a"], 'a.txt'))
    await api.processImport(new File(["b"], 'b.txt'), true)
    await api.processImport(new File(["c"], 'c.txt'), false, { A: 1 })

    await api.getEventOptions()
    await api.addEventType('type')
    await api.deleteEventType(1)
    await api.addEventDescription(1, 'desc')
    await api.deleteEventDescription(2)

    await api.getPredictionChartData('E1', 7, 'k')
    expect(axiosInst.get).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/prediction/goats/E1/prediction/chart-data'),
      expect.objectContaining({ headers: expect.objectContaining({ 'X-Api-Key': 'k' }) })
    )

    await api.getSheepPrediction('E1', 14, 'k')
    expect(axiosInst.get).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/prediction/goats/E1/prediction'),
      expect.objectContaining({ headers: expect.objectContaining({ 'X-Api-Key': 'k' }) })
    )

    await api.getAgentTip('k')
    expect(axiosInst.get).toHaveBeenLastCalledWith(
      '/api/agent/tip',
      expect.objectContaining({ headers: expect.objectContaining({ 'X-Api-Key': 'k' }) })
    )

    await api.getRecommendation('k', { a: 1 })
    expect(axiosInst.post).toHaveBeenLastCalledWith(
      '/api/agent/recommendation',
      { a: 1 },
      expect.objectContaining({ headers: expect.objectContaining({ 'X-Api-Key': 'k' }) })
    )

    await api.chatWithAgent('k', 'hello', 'sid', 'E1', null)
    expect(axiosInst.post).toHaveBeenLastCalledWith(
      '/api/agent/chat',
      expect.any(FormData),
      expect.objectContaining({ headers: expect.objectContaining({ 'X-Api-Key': 'k' }) })
    )

    expect(axiosInst.post).toHaveBeenCalled()
  })

  it('withErrorHandling calls errorHandler on error', async () => {
    axiosInst.get.mockRejectedValueOnce({ response: { status: 400, data: { error: 'bad' } } })
    const onErr = vi.fn()
    await expect(api.getAllSheep(onErr)).rejects.toBeTruthy()
    expect(onErr).toHaveBeenCalledWith(expect.objectContaining({ message: 'formatted' }))
  })
})
