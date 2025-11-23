import { vi, describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock localStorage first
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// Mock errorHandler 避免循環依賴
vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

// Mock API
vi.mock('../api', () => ({
  default: {
    getAgentTip: vi.fn(),
    getAgentStatus: vi.fn()
  }
}))

// Import after mocking
import { useSettingsStore, FONT_SCALE } from './settings'
import api from '../api'

describe('settings Store', () => {
  // 1. 建立可重用的輔助函式
  const setupLocalStorageMocks = ({ apiKey = '', fontScale = FONT_SCALE.DEFAULT } = {}) => {
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'geminiApiKey') return apiKey;
      if (key === 'uiFontScale') return fontScale;
      return '';
    });
  };

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    if (typeof document !== 'undefined') {
      document.documentElement.dataset.fontScale = FONT_SCALE.DEFAULT
    }
    // 2. 在 beforeEach 中設定預設的 mock 狀態
    setupLocalStorageMocks();
    api.getAgentStatus.mockResolvedValue({ rag_enabled: false, message: '', detail: null })
  })

  describe('初始狀態', () => {
    it('應該有正確的初始狀態', () => {
      const store = useSettingsStore()

      expect(store.apiKey).toBe('')
      expect(store.agentTip).toEqual({
        html: '',
        loading: false,
        loaded: false
      })
      expect(store.ragStatus).toEqual({
        available: null,
        message: '',
        detail: null
      })
      expect(store.hasApiKey).toBe(false)
    })

    it('應該從 localStorage 載入已儲存的 API Key', () => {
      const savedApiKey = 'saved-api-key-123'
      // 3. 在需要特定狀態的測試中呼叫輔助函式
      setupLocalStorageMocks({ apiKey: savedApiKey });
      
      const store = useSettingsStore()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('geminiApiKey')
      expect(store.apiKey).toBe(savedApiKey)
      expect(store.hasApiKey).toBe(true)
    })
  })

  describe('Actions', () => {
    describe('setApiKey', () => {
      it('應該設定並儲存 API Key', () => {
        const store = useSettingsStore()
        const testApiKey = 'test-api-key-123'

        store.setApiKey(testApiKey)

        expect(store.apiKey).toBe(testApiKey)
        expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', testApiKey)
      })

      it('應該處理空的 API Key', () => {
        const store = useSettingsStore()

        store.setApiKey('')

        expect(store.apiKey).toBe('')
        expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', '')
      })
    })

    describe('clearApiKey', () => {
      it('應該清除 API Key', () => {
        setupLocalStorageMocks({ apiKey: 'existing-key' });
        const store = useSettingsStore()
        
        expect(store.apiKey).toBe('existing-key')

        store.clearApiKey()

        expect(store.apiKey).toBe('')
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('geminiApiKey')
      })
    })

    describe('fetchAndSetAgentTip', () => {
      it('應該成功獲取 Agent 提示', async () => {
        const mockTip = '<p>今日提示：注意山羊的營養平衡</p>'
        setupLocalStorageMocks({ apiKey: 'valid-api-key' });

        const store = useSettingsStore()
        api.getAgentStatus.mockResolvedValue({ rag_enabled: true, message: 'RAG Ready', detail: 'vectors.parquet' })
        api.getAgentTip.mockResolvedValue({ tip_html: mockTip })

        await store.fetchAndSetAgentTip()

        expect(store.agentTip.loading).toBe(false)
        expect(store.agentTip.html).toBe(mockTip)
        expect(store.agentTip.loaded).toBe(true)
        expect(api.getAgentTip).toHaveBeenCalledWith('valid-api-key')
        expect(api.getAgentStatus).toHaveBeenCalledWith('valid-api-key')
        expect(store.ragStatus).toEqual({ available: true, message: 'RAG Ready', detail: 'vectors.parquet' })
      })

      it('應該處理獲取提示失敗', async () => {
        setupLocalStorageMocks({ apiKey: 'invalid-key' });

        const store = useSettingsStore()
        api.getAgentStatus.mockRejectedValue({ error: '狀態失敗' })
        api.getAgentTip.mockRejectedValue({ error: 'API 錯誤' })

        await store.fetchAndSetAgentTip()

        expect(store.agentTip.loading).toBe(false)
        expect(store.agentTip.html).toContain('無法獲取提示: API 錯誤')
        expect(store.agentTip.loaded).toBe(true)
        expect(store.ragStatus.available).toBe(false)
        expect(store.ragStatus.message).toContain('無法取得 RAG 狀態')
      })

      it('loading 狀態應該正確切換', async () => {
        setupLocalStorageMocks({ apiKey: 'test-key' });
        const store = useSettingsStore()

        let resolvePromise
        const mockPromise = new Promise(resolve => {
          resolvePromise = resolve
        })
        api.getAgentTip.mockReturnValue(mockPromise)

        const fetchPromise = store.fetchAndSetAgentTip()
        expect(store.agentTip.loading).toBe(true)

        resolvePromise({ tip_html: '測試提示' })
        await fetchPromise
        expect(store.agentTip.loading).toBe(false)
      })

      it('應該處理沒有 API Key 的情況', async () => {
        // 使用 beforeEach 的預設 mock (apiKey: '') 即可
        const store = useSettingsStore()

        await store.fetchAndSetAgentTip()

        expect(store.agentTip.html).toBe('請先在「系統設定」中設定有效的API金鑰以獲取提示。')
        expect(api.getAgentTip).not.toHaveBeenCalled()
      })

      it('應該避免重複獲取（已載入）', async () => {
        setupLocalStorageMocks({ apiKey: 'test-key' });
        
        const store = useSettingsStore()
        api.getAgentTip.mockResolvedValue({ tip_html: '初次提示' })

        await store.fetchAndSetAgentTip()
        expect(api.getAgentTip).toHaveBeenCalledTimes(1)

        await store.fetchAndSetAgentTip()
        expect(api.getAgentTip).toHaveBeenCalledTimes(1)
      })

      it('應該避免重複獲取（載入中）', async () => {
        setupLocalStorageMocks({ apiKey: 'test-key' });
        
        const store = useSettingsStore()

        let resolveFirst
        api.getAgentTip.mockImplementation(() => new Promise(resolve => {
          resolveFirst = resolve
        }))

        const promise1 = store.fetchAndSetAgentTip()
        const promise2 = store.fetchAndSetAgentTip()

        await Promise.resolve()
        resolveFirst({ tip_html: '提示內容' })
        await Promise.all([promise1, promise2])

        expect(api.getAgentTip).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('字體大小設定', () => {
    it('初始化時會從 localStorage 載入字級偏好並套用', () => {
      setupLocalStorageMocks({ fontScale: FONT_SCALE.LARGE });

      const store = useSettingsStore()

      expect(store.fontScale).toBe(FONT_SCALE.LARGE)
      expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.LARGE)
    })

    it('setFontScale 會更新狀態、儲存並套用到文件', () => {
      const store = useSettingsStore()

      store.setFontScale(FONT_SCALE.LARGE)

      expect(store.fontScale).toBe(FONT_SCALE.LARGE)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('uiFontScale', FONT_SCALE.LARGE)
      expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.LARGE)

      store.setFontScale(FONT_SCALE.DEFAULT)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('uiFontScale', FONT_SCALE.DEFAULT)
      expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.DEFAULT)
    })

    it('setFontScale 支援超大字級', () => {
      const store = useSettingsStore()

      store.setFontScale(FONT_SCALE.EXTRA_LARGE)

      expect(store.fontScale).toBe(FONT_SCALE.EXTRA_LARGE)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('uiFontScale', FONT_SCALE.EXTRA_LARGE)
      expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.EXTRA_LARGE)
    })

    it('setFontScale 遇到無效值會回退到預設字級', () => {
      const store = useSettingsStore()

      store.setFontScale('huge')

      expect(store.fontScale).toBe(FONT_SCALE.DEFAULT)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('uiFontScale', FONT_SCALE.DEFAULT)
      expect(document.documentElement.dataset.fontScale).toBe(FONT_SCALE.DEFAULT)
    })
  })

  describe('Computed Properties', () => {
    it('hasApiKey 應該根據 apiKey 正確計算', () => {
      const store = useSettingsStore()
      
      expect(store.hasApiKey).toBe(false)
      
      store.setApiKey('test-key')
      expect(store.hasApiKey).toBe(true)
      
      store.clearApiKey()
      expect(store.hasApiKey).toBe(false)
    })
  })

  describe('localStorage 整合', () => {
    it('應該在初始化時從 localStorage 載入 API Key', () => {
      setupLocalStorageMocks({ apiKey: 'stored-key' });

      const store = useSettingsStore()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('geminiApiKey')
      expect(store.apiKey).toBe('stored-key')
    })

    it('應該處理 localStorage 不可用的情況', () => {
      const originalLocalStorage = global.localStorage
      global.localStorage = null
      
      expect(() => {
        useSettingsStore()
      }).toThrow()

      global.localStorage = originalLocalStorage
    })

    it('應該處理 localStorage 拋出異常的情況', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })
      
      expect(() => {
        useSettingsStore()
      }).toThrow()
    })
  })

  describe('邊界條件處理', () => {
    it('應該處理網路錯誤', async () => {
      setupLocalStorageMocks({ apiKey: 'test-key' });
      const store = useSettingsStore()
      
      api.getAgentTip.mockRejectedValue({ message: 'Network Error' })

      await store.fetchAndSetAgentTip()

      expect(store.agentTip.html).toContain('無法獲取提示: Network Error')
      expect(store.agentTip.loaded).toBe(true)
    })

    it('應該處理未知錯誤', async () => {
      setupLocalStorageMocks({ apiKey: 'test-key' });
      const store = useSettingsStore()
      
      api.getAgentTip.mockRejectedValue({})

      await store.fetchAndSetAgentTip()

      expect(store.agentTip.html).toContain('無法獲取提示:')
      expect(store.agentTip.loaded).toBe(true)
    })

    it('應該處理非常長的 API Key', () => {
      const longApiKey = 'a'.repeat(1000)
      const store = useSettingsStore()

      store.setApiKey(longApiKey)

      expect(store.apiKey).toBe(longApiKey)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', longApiKey)
    })

    it('應該處理特殊字符的 API Key', () => {
      const specialApiKey = 'test-key-123!@#$%^&*()_+{}|:"<>?[]\\;\',./'
      const store = useSettingsStore()

      store.setApiKey(specialApiKey)

      expect(store.apiKey).toBe(specialApiKey)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', specialApiKey)
    })

    it('應該處理並發的 fetchAndSetAgentTip 請求', async () => {
      setupLocalStorageMocks({ apiKey: 'test-key' });
      const store = useSettingsStore()
      
      api.getAgentTip.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ tip_html: '並發測試提示' }), 50))
      )

      const promises = Array(3).fill().map(() => store.fetchAndSetAgentTip())
      await Promise.all(promises)

      expect(api.getAgentTip).toHaveBeenCalledTimes(1)
      expect(store.agentTip.html).toBe('並發測試提示')
    })

    it('應該正確處理 null 和 undefined 的 API Key', () => {
      const store = useSettingsStore()

      store.setApiKey(null)
      expect(store.apiKey).toBe(null)
      expect(store.hasApiKey).toBe(false)

      store.setApiKey(undefined)
      expect(store.apiKey).toBe(undefined)
      expect(store.hasApiKey).toBe(false)
    })
  })

  describe('狀態重置', () => {
    it('應該能夠重置 agentTip 狀態', async () => {
      setupLocalStorageMocks({ apiKey: 'test-key' });
      const store = useSettingsStore()
      
      api.getAgentTip.mockResolvedValue({ tip_html: '初始提示' })
      await store.fetchAndSetAgentTip()
      
      expect(store.agentTip.loaded).toBe(true)
      expect(store.agentTip.html).toBe('初始提示')

      store.agentTip.loaded = false
      store.agentTip.html = ''

      expect(store.agentTip.loaded).toBe(false)
      expect(store.agentTip.html).toBe('')
    })

    it('應該在 API Key 改變時能夠重新獲取提示', async () => {
      setupLocalStorageMocks({ apiKey: 'old-key' });
      const store = useSettingsStore()
      
      api.getAgentTip.mockResolvedValue({ tip_html: '舊提示' })
      await store.fetchAndSetAgentTip()
      expect(store.agentTip.html).toBe('舊提示')

      store.setApiKey('new-key')
      store.agentTip.loaded = false

      api.getAgentTip.mockResolvedValue({ tip_html: '新提示' })
      await store.fetchAndSetAgentTip()
      
      expect(store.agentTip.html).toBe('新提示')
      expect(api.getAgentTip).toHaveBeenLastCalledWith('new-key')
    })
  })
})
