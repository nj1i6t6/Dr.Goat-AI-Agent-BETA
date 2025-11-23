/**
 * Chat Store 測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useChatStore } from './chat'
import api from '../api'

// Mock errorHandler 避免循環依賴
vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

// Mock API
vi.mock('../api', () => ({
  default: {
    chatWithAgent: vi.fn()
  }
}))

describe('Chat Store', () => {
  let chatStore
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    chatStore = useChatStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('初始狀態', () => {
    it('應該有正確的初始狀態', () => {
      expect(chatStore.sessionId).toBeDefined()
      expect(chatStore.sessionId).toMatch(/^session_\d+$/)
      expect(chatStore.messages).toHaveLength(1)
      expect(chatStore.messages[0]).toEqual({
        role: 'model',
        content: '<p>您好，我是領頭羊博士，請問有什麼可以為您服務的嗎？</p>'
      })
      expect(chatStore.isLoading).toBe(false)
      expect(chatStore.error).toBe('')
    })

    it('應該生成唯一的 session ID', () => {
      const store1 = useChatStore()
      const store2 = useChatStore()
      
      // 因為使用了單例模式，應該是同一個實例
      expect(store1.sessionId).toBe(store2.sessionId)
    })
  })

  describe('sendMessage action', () => {
    const mockApiKey = 'test-api-key'
    const mockUserMessage = '你好'
    const mockEarNumContext = 'SH001'

    it('應該成功發送訊息並接收回覆', async () => {
      const mockResponse = {
        reply_html: '<p>很高興為您服務！</p>'
      }
      api.chatWithAgent.mockResolvedValue(mockResponse)

      await chatStore.sendMessage(mockApiKey, mockUserMessage, mockEarNumContext)

      expect(api.chatWithAgent).toHaveBeenCalledWith(
        mockApiKey,
        mockUserMessage,
        chatStore.sessionId,
        mockEarNumContext,
        null
      )
      
      expect(chatStore.messages).toHaveLength(3) // 初始訊息 + 用戶訊息 + AI回覆
      expect(chatStore.messages[1]).toEqual({
        role: 'user',
        content: mockUserMessage
      })
      expect(chatStore.messages[2]).toEqual({
        role: 'model',
        content: mockResponse.reply_html
      })
      
      expect(chatStore.isLoading).toBe(false)
      expect(chatStore.error).toBe('')
    })

    it('應該處理 API 錯誤', async () => {
      const mockError = { error: 'API 連接失敗' }
      api.chatWithAgent.mockRejectedValue(mockError)

      await chatStore.sendMessage(mockApiKey, mockUserMessage, mockEarNumContext)

      expect(chatStore.messages).toHaveLength(3)
      expect(chatStore.messages[1]).toEqual({
        role: 'user',
        content: mockUserMessage
      })
      expect(chatStore.messages[2]).toEqual({
        role: 'model',
        content: '<p style="color:red;">助理回覆錯誤: API 連接失敗</p>'
      })
      
      expect(chatStore.error).toBe('API 連接失敗')
      expect(chatStore.isLoading).toBe(false)
    })

    it('應該處理一般 Error 對象', async () => {
      const mockError = new Error('網絡錯誤')
      api.chatWithAgent.mockRejectedValue(mockError)

      await chatStore.sendMessage(mockApiKey, mockUserMessage, mockEarNumContext)

      expect(chatStore.error).toBe('網絡錯誤')
      expect(chatStore.messages[2].content).toContain('網絡錯誤')
    })

    it('應該處理未知錯誤', async () => {
      const mockError = 'unknown error'
      api.chatWithAgent.mockRejectedValue(mockError)

      await chatStore.sendMessage(mockApiKey, mockUserMessage, mockEarNumContext)

      expect(chatStore.error).toBe('AI 助理回覆時發生未知錯誤')
      expect(chatStore.messages[2].content).toContain('AI 助理回覆時發生未知錯誤')
    })

    it('應該在發送期間設置載入狀態', async () => {
      let loadingDuringCall = false
      
      api.chatWithAgent.mockImplementation(() => {
        loadingDuringCall = chatStore.isLoading
        return Promise.resolve({ reply_html: '<p>回覆</p>' })
      })

      await chatStore.sendMessage(mockApiKey, mockUserMessage, mockEarNumContext)

      expect(loadingDuringCall).toBe(true)
      expect(chatStore.isLoading).toBe(false)
    })

    it('應該支持沒有耳號上下文的聊天', async () => {
      const mockResponse = { reply_html: '<p>一般回覆</p>' }
      api.chatWithAgent.mockResolvedValue(mockResponse)

      await chatStore.sendMessage(mockApiKey, mockUserMessage, '')

      expect(api.chatWithAgent).toHaveBeenCalledWith(
        mockApiKey,
        mockUserMessage,
        chatStore.sessionId,
        '',
        null
      )
    })

    it('應該支持多輪對話', async () => {
      // 第一輪對話
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>第一個回覆</p>' })
      await chatStore.sendMessage(mockApiKey, '第一個問題', '')

      // 第二輪對話
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>第二個回覆</p>' })
      await chatStore.sendMessage(mockApiKey, '第二個問題', '')

      expect(chatStore.messages).toHaveLength(5) // 初始 + 問題1 + 回覆1 + 問題2 + 回覆2
      expect(chatStore.messages[3].content).toBe('第二個問題')
      expect(chatStore.messages[4].content).toBe('<p>第二個回覆</p>')
    })
  })

  describe('clearChat action', () => {
    beforeEach(async () => {
      // 添加一些測試訊息
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>測試回覆</p>' })
      await chatStore.sendMessage('test-key', '測試訊息', '')
    })

    it('應該清空聊天記錄並重置狀態', async () => {
      const originalSessionId = chatStore.sessionId
      
      expect(chatStore.messages).toHaveLength(3) // 初始 + 用戶 + AI

      // 等待一毫秒確保時間戳不同
      await new Promise(resolve => setTimeout(resolve, 1))
      chatStore.clearChat()

      expect(chatStore.messages).toHaveLength(1)
      expect(chatStore.messages[0]).toEqual({
        role: 'model',
        content: '<p>您好，我是領頭羊博士，請問有什麼可以為您服務的嗎？</p>'
      })
      expect(chatStore.sessionId).not.toBe(originalSessionId)
      expect(chatStore.sessionId).toMatch(/^session_\d+$/)
      expect(chatStore.isLoading).toBe(false)
      expect(chatStore.error).toBe('')
    })

    it('應該生成新的 session ID', async () => {
      const originalSessionId = chatStore.sessionId
      
      // 等待更長些以確保時間戳不同（避免毫秒碰撞）
      await new Promise(resolve => setTimeout(resolve, 10))
      
      chatStore.clearChat()
      
      expect(chatStore.sessionId).not.toBe(originalSessionId)
      expect(chatStore.sessionId).toMatch(/^session_\d+$/)
    })

    it('應該在清除錯誤狀態後清空對話', () => {
      // 模擬一個錯誤狀態
      chatStore.error = '測試錯誤'
      chatStore.isLoading = true

      chatStore.clearChat()

      expect(chatStore.error).toBe('')
      expect(chatStore.isLoading).toBe(false)
    })
  })

  describe('響應式狀態', () => {
    it('messages 陣列應該是響應式的', async () => {
      const initialLength = chatStore.messages.length
      
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>測試</p>' })
      await chatStore.sendMessage('key', 'message', '')
      
      expect(chatStore.messages.length).toBe(initialLength + 2)
    })

    it('應該保持 messages 的響應性', () => {
      const messages = chatStore.messages
      
      // 直接操作 messages 陣列
      messages.push({ role: 'user', content: '直接添加的訊息' })
      
      expect(chatStore.messages).toHaveLength(2)
      expect(chatStore.messages[1].content).toBe('直接添加的訊息')
    })
  })

  describe('邊界條件處理', () => {
    it('應該處理空的用戶訊息', async () => {
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>回覆</p>' })
      
  await chatStore.sendMessage('key', '', '')
      
      expect(chatStore.messages[1].content).toBe('')
      expect(api.chatWithAgent).toHaveBeenCalledWith(
        'key',
        '請幫我分析這張山羊照片',
        chatStore.sessionId,
        '',
        null
      )
    })

    it('應該處理 null 的 API 回覆', async () => {
      api.chatWithAgent.mockResolvedValue({ reply_html: null })
      
      await chatStore.sendMessage('key', 'test', '')
      
      expect(chatStore.messages[2].content).toBe(null)
    })

    it('應該處理缺少 reply_html 的響應', async () => {
      api.chatWithAgent.mockResolvedValue({})
      
      await chatStore.sendMessage('key', 'test', '')
      
      expect(chatStore.messages[2].content).toBeUndefined()
    })

    it('應該處理並發的發送請求', async () => {
      api.chatWithAgent.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ reply_html: '<p>延遲回覆</p>' }), 100))
      )

      // 同時發送兩個請求
      const promise1 = chatStore.sendMessage('key', '訊息1', '')
      const promise2 = chatStore.sendMessage('key', '訊息2', '')

      await Promise.all([promise1, promise2])

      expect(chatStore.messages).toHaveLength(5) // 初始 + 2對話
      expect(chatStore.isLoading).toBe(false)
    })

    it('應該處理極長的訊息', async () => {
      const longMessage = 'a'.repeat(10000)
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>長訊息回覆</p>' })
      
      await chatStore.sendMessage('key', longMessage, '')
      
      expect(chatStore.messages[1].content).toBe(longMessage)
      expect(chatStore.messages[2].content).toBe('<p>長訊息回覆</p>')
    })

    it('應該處理特殊字符', async () => {
      const specialMessage = '🐑📊💡<script>alert("test")</script>'
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>特殊字符回覆</p>' })
      
      await chatStore.sendMessage('key', specialMessage, '')
      
      expect(chatStore.messages[1].content).toBe(specialMessage)
    })
  })

  describe('錯誤恢復', () => {
    it('應該在錯誤後仍能正常發送訊息', async () => {
      // 第一次請求失敗
      api.chatWithAgent.mockRejectedValueOnce(new Error('第一次失敗'))
      await chatStore.sendMessage('key', '第一個訊息', '')
      
      expect(chatStore.error).toBe('第一次失敗')
      
      // 第二次請求成功
      api.chatWithAgent.mockResolvedValue({ reply_html: '<p>成功回覆</p>' })
      await chatStore.sendMessage('key', '第二個訊息', '')
      
      expect(chatStore.error).toBe('')
      expect(chatStore.messages).toHaveLength(5)
      expect(chatStore.messages[4].content).toBe('<p>成功回覆</p>')
    })
  })
})
