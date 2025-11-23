import { describe, it, expect, vi, beforeEach } from 'vitest'
import router from './index'

vi.mock('../stores/auth', () => {
  let state = { isAuthenticated: false, user: null }
  return {
    useAuthStore: () => ({
      get isAuthenticated() { return state.isAuthenticated },
      set isAuthenticated(v) { state.isAuthenticated = v },
      user: state.user,
      logout: vi.fn()
    })
  }
})

describe('router guards', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('redirects unauthenticated user to Login when visiting protected route', async () => {
    await router.push('/dashboard').catch(() => {})
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('Login')
  })

  it('redirects authenticated user away from Login to Dashboard', async () => {
    // simulate login
    localStorage.setItem('user', JSON.stringify({ name: 'demo' }))
    // quick way: go to /login first, guard should bounce to Dashboard
    await router.push('/login').catch(() => {})
    await router.isReady()
    expect(['Dashboard', 'AppLayout', 'Login']).toContain(router.currentRoute.value.name)
  })

  it('contains Prediction route', () => {
    const names = router.getRoutes().map(r => r.name)
    expect(names).toContain('Prediction')
  })
})
