import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockUseAuthStore = vi.fn()
vi.mock('../stores/auth', () => ({
  useAuthStore: () => mockUseAuthStore()
}))
import router from './index'

describe('router guard functions coverage', () => {
  beforeEach(() => {
    localStorage.clear()
    mockUseAuthStore.mockReset()
  })

  it('redirects to Login when visiting protected route unauthenticated', async () => {
    mockUseAuthStore.mockReturnValue({ isAuthenticated: false })
    await router.push('/dashboard').catch(() => {})
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('redirects away from Login to Dashboard when authenticated', async () => {
    mockUseAuthStore.mockReturnValue({ isAuthenticated: true })
    await router.push('/login').catch(() => {})
    await router.isReady()
    expect(['Dashboard', 'AppLayout', 'Login']).toContain(router.currentRoute.value.name)
  })

  it('parses valid user JSON from localStorage into store.user', async () => {
    let assignedUser = null
    const state = {
      isAuthenticated: false,
      get user() { return assignedUser },
      set user(v) { assignedUser = v }
    }
    mockUseAuthStore.mockReturnValue(state)
    const parsed = { username: 'u1' }
    const originalGet = localStorage.getItem.bind(localStorage)
    localStorage.getItem = vi.fn((key) => key === 'user' ? JSON.stringify(parsed) : originalGet(key))
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    await router.push('/dashboard').catch(() => {})
    await router.isReady()
    expect(assignedUser).toEqual(parsed)
    expect(warnSpy).not.toHaveBeenCalled()
    warnSpy.mockRestore()
    // restore
    localStorage.getItem = originalGet
  })

  it('removes bad JSON in localStorage and warns, then redirects to Login', async () => {
    let assignedUser = null
    const state = {
      isAuthenticated: false,
      get user() { return assignedUser },
      set user(v) { assignedUser = v }
    }
    mockUseAuthStore.mockReturnValue(state)
    const originalGet = localStorage.getItem.bind(localStorage)
    localStorage.getItem = vi.fn((key) => key === 'user' ? '{bad-json' : originalGet(key))
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const removeSpy = vi.spyOn(localStorage, 'removeItem')
    await router.push('/dashboard').catch(() => {})
    await router.isReady()
    expect(removeSpy).toHaveBeenCalledWith('user')
    expect(warnSpy).toHaveBeenCalled()
    expect(router.currentRoute.value.name).toBe('Login')
    warnSpy.mockRestore()
    localStorage.getItem = originalGet
  })
})
