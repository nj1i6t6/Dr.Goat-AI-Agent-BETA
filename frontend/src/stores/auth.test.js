import { vi, describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.localStorage = localStorageMock

const routerMock = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn()
}))

vi.mock('../router', () => ({
  default: routerMock
}))

// Mock errorHandler 避免循環依賴
vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

vi.mock('../api', () => ({
  default: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn()
  }
}))

import { useAuthStore } from './auth'
import router from '../router'
import api from '../api'

describe('auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  it('應該有正確的初始狀態', () => {
    const store = useAuthStore()

    expect(store.user).toBe(null)
    expect(store.isAuthenticated).toBe(false)
    expect(store.username).toBe('訪客')
  })

  it('初始化時會從 localStorage 讀取用戶資訊', () => {
    const mockUser = { username: 'existing-user' }
    localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(mockUser))

    const store = useAuthStore()

    expect(store.user).toEqual(mockUser)
    expect(store.isAuthenticated).toBe(true)
    expect(store.username).toBe('existing-user')
  })

  it('localStorage 解析失敗時會清除資料並回退為未登入', () => {
    localStorageMock.getItem.mockReturnValueOnce('not-json')
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    const store = useAuthStore()

    expect(store.user).toBe(null)
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('user')
    expect(warnSpy).toHaveBeenCalled()

    warnSpy.mockRestore()
  })

  it('成功登入後會更新狀態並導向儀表板', async () => {
    const loginData = { email: 'test@example.com', password: 'password123' }
    const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' }

    api.login.mockResolvedValue({ success: true, user: mockUser })

    const store = useAuthStore()
    await store.login(loginData)

    expect(store.user).toEqual(mockUser)
    expect(store.isAuthenticated).toBe(true)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser))
    expect(router.push).toHaveBeenCalledWith({ name: 'Dashboard' })
  })

  it('登入失敗時會拋出錯誤並維持未登入狀態', async () => {
    const error = new Error('login failed')
    api.login.mockRejectedValueOnce(error)

    const store = useAuthStore()

    await expect(store.login({})).rejects.toThrow('login failed')
    expect(store.user).toBe(null)
    expect(localStorageMock.setItem).not.toHaveBeenCalled()
    expect(router.push).not.toHaveBeenCalled()
  })

  it('成功註冊後會更新狀態並導向儀表板', async () => {
    const creds = { email: 'new@example.com', password: 'pw' }
    const mockUser = { id: 2, username: 'newbie' }

    api.register.mockResolvedValue({ success: true, user: mockUser })

    const store = useAuthStore()
    await store.register(creds)

    expect(store.user).toEqual(mockUser)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser))
    expect(router.push).toHaveBeenCalledWith({ name: 'Dashboard' })
  })

  it('註冊失敗時會拋出錯誤且不上傳狀態', async () => {
    const error = new Error('register failed')
    api.register.mockRejectedValueOnce(error)

    const store = useAuthStore()

    await expect(store.register({})).rejects.toThrow('register failed')
    expect(store.user).toBe(null)
    expect(localStorageMock.setItem).not.toHaveBeenCalled()
    expect(router.push).not.toHaveBeenCalled()
  })

  it('logout 會呼叫 API 並清除狀態與導向登入頁', async () => {
    api.logout.mockResolvedValue()

    const store = useAuthStore()
    store.user = { username: 'test' }
    localStorageMock.getItem.mockReturnValue(JSON.stringify(store.user))

    await store.logout()

    expect(api.logout).toHaveBeenCalledTimes(1)
    expect(store.user).toBe(null)
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('user')
    expect(router.replace).toHaveBeenCalledWith({ name: 'Login' })
  })

  it('logout 即使 API 失敗也會完成清理並導向登入頁', async () => {
    api.logout.mockRejectedValueOnce(new Error('network error'))

    const store = useAuthStore()
    store.user = { username: 'test' }

    await store.logout()

    expect(store.user).toBe(null)
    expect(router.replace).toHaveBeenCalledWith({ name: 'Login' })
  })

  it('logout 會忽略重複呼叫以避免併發', async () => {
    let resolveLogout
    api.logout.mockReturnValue(new Promise(resolve => { resolveLogout = resolve }))

    const store = useAuthStore()
    store.user = { username: 'test' }

    const firstCall = store.logout()
    const secondCall = store.logout()

    await Promise.resolve()
    expect(api.logout).toHaveBeenCalledTimes(1)

    resolveLogout()
    await firstCall
    await secondCall
  })
})
