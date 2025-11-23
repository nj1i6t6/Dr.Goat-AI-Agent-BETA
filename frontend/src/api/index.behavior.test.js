import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from './index'

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

const mockOk = (data) => ({ data })
const mockErr = (status = 500, data = { error: 'boom' }) => {
  const error = new Error('axios error')
  error.response = { status, data }
  return error
}

describe('api behavior', () => {
  let axiosInstance
  beforeEach(async () => {
    // fresh import to reinitialize axios.create
    const axiosMod = await import('axios')
    axiosInstance = axiosMod.default.create()
    axiosInstance.get.mockReset()
    axiosInstance.post.mockReset()
    axiosInstance.put.mockReset()
    axiosInstance.delete.mockReset()
  })

  it('getAllSheep success', async () => {
    const axiosMod = await import('axios')
    // Our axios is fully mocked, so interceptors won't unwrap .data.
    // Return the payload directly to match api.getAllSheep() expectations in this mock setup.
    axiosMod.default.create().get.mockResolvedValueOnce([{ EarNum: 'A1' }])
    const res = await api.getAllSheep()
    expect(res[0].EarNum).toBe('A1')
  })

  it('getAllSheep error calls errorHandler and rethrows', async () => {
    const axiosMod = await import('axios')
    axiosMod.default.create().get.mockRejectedValueOnce(mockErr(404, { error: 'not found' }))
    const onErr = vi.fn()
    await expect(api.getAllSheep(onErr)).rejects.toBeTruthy()
    expect(onErr).toHaveBeenCalled()
  })

  it('getSheepPrediction adds header and passes targetDays', async () => {
    const axiosMod = await import('axios')
    axiosMod.default.create().get.mockResolvedValueOnce(mockOk({ ok: true }))
    await api.getSheepPrediction('E001', 14, 'k')
    const call = axiosMod.default.create().get.mock.calls[0]
    expect(call[0]).toContain('/api/prediction/goats/E001/prediction?target_days=14')
    expect(call[1]).toMatchObject({ headers: { 'X-Api-Key': 'k' } })
  })

  it('chatWithAgent without image uses JSON payload', async () => {
    const axiosMod = await import('axios')
    axiosMod.default.create().post.mockResolvedValueOnce(mockOk({ message: 'ok' }))
    await api.chatWithAgent('k', 'hi', 'sid', 'E001', null)
    const call = axiosMod.default.create().post.mock.calls[0]
    expect(call[0]).toBe('/api/agent/chat')
    expect(call[1]).toMatchObject({ api_key: 'k', message: 'hi', session_id: 'sid', ear_num_context: 'E001' })
  })
})
