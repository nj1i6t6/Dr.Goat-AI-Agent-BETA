/**
 * consultation.js Store 測試
 * 測試營養諮詢功能狀態管理
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConsultationStore } from '@/stores/consultation'

// Mock errorHandler 避免循環依賴
vi.mock('@/utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

// 模擬 API 模組
vi.mock('@/api', () => ({
  default: {
    getRecommendation: vi.fn(),
  },
}))

import api from '@/api'

describe('consultation Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始狀態', () => {
    it('應該有正確的初始狀態', () => {
      const store = useConsultationStore()
      
      expect(store.form).toBeDefined()
      expect(store.form.EarNum).toBe('')
      expect(store.form.Breed).toBe('')
      expect(store.form.breed_category).toBe('Dairy')
      expect(store.form.status).toBe('maintenance')
      expect(store.form.optimization_goal).toBe('balanced')
      expect(store.isLoading).toBe(false)
      expect(store.resultHtml).toBe('')
      expect(store.error).toBe('')
    })
  })

  describe('Actions', () => {
    describe('setFormData', () => {
      it('應該正確設定表單資料', () => {
        const store = useConsultationStore()
        const newData = {
          EarNum: 'G001',
          Breed: 'Alpine',
          Body_Weight_kg: 50,
          Age_Months: 24
        }

        store.setFormData(newData)

        expect(store.form.EarNum).toBe('G001')
        expect(store.form.Breed).toBe('Alpine')
        expect(store.form.Body_Weight_kg).toBe(50)
        expect(store.form.Age_Months).toBe(24)
        expect(store.resultHtml).toBe('') // 應該清除之前的結果
        expect(store.error).toBe('')
      })

      it('應該重置表單到初始狀態再設定新資料', () => {
        const store = useConsultationStore()
        
        // 先設定一些資料
        store.form.EarNum = 'OLD001'
        store.form.Breed = 'OldBreed'
        store.form.Body_Weight_kg = 30
        
        // 設定新資料（只包含部分欄位）
        const newData = {
          EarNum: 'G001',
          Breed: 'Alpine'
        }
        
        store.setFormData(newData)

        expect(store.form.EarNum).toBe('G001')
        expect(store.form.Breed).toBe('Alpine')
        expect(store.form.Body_Weight_kg).toBe(null) // 應該重置為預設值
      })
    })

    describe('getRecommendation', () => {
      it('應該成功獲取營養建議', async () => {
        const store = useConsultationStore()
        const apiKey = 'test-api-key'
        const mockResponse = {
          recommendation_html: '<div>建議的營養配方...</div>'
        }

        api.getRecommendation.mockResolvedValue(mockResponse)

        await store.getRecommendation(apiKey)

        expect(store.isLoading).toBe(false)
        expect(store.resultHtml).toBe(mockResponse.recommendation_html)
        expect(store.error).toBe('')
        expect(api.getRecommendation).toHaveBeenCalledWith(apiKey, expect.any(Object))
      })

      it('應該處理獲取建議失敗', async () => {
        const store = useConsultationStore()
        const apiKey = 'test-api-key'
        const errorMessage = '獲取建議失敗'

        api.getRecommendation.mockRejectedValue({ error: errorMessage })

        await store.getRecommendation(apiKey)

        expect(store.isLoading).toBe(false)
        expect(store.error).toBe(errorMessage)
        expect(store.resultHtml).toContain('獲取建議失敗')
      })

      it('loading 狀態應該正確切換', async () => {
        const store = useConsultationStore()
        
        let resolvePromise
        const mockPromise = new Promise((resolve) => {
          resolvePromise = resolve
        })
        api.getRecommendation.mockReturnValue(mockPromise)

        const getPromise = store.getRecommendation('test-key')
        expect(store.isLoading).toBe(true)

        resolvePromise({ recommendation_html: '<div>建議</div>' })
        await getPromise
        expect(store.isLoading).toBe(false)
      })

      it('應該在獲取新建議前清除舊結果', async () => {
        const store = useConsultationStore()
        
        // 設定舊結果
        store.resultHtml = '<div>舊建議</div>'
        
        api.getRecommendation.mockResolvedValue({
          recommendation_html: '<div>新建議</div>'
        })

        await store.getRecommendation('test-key')

        expect(store.resultHtml).toBe('<div>新建議</div>')
      })
    })

    describe('reset', () => {
      it('應該重置所有狀態', () => {
        const store = useConsultationStore()
        
        // 修改狀態
        store.form.EarNum = 'G001'
        store.form.Breed = 'Alpine'
        store.isLoading = true
        store.resultHtml = '<div>測試結果</div>'
        store.error = '測試錯誤'

        store.reset()

        expect(store.form.EarNum).toBe('')
        expect(store.form.Breed).toBe('')
        expect(store.form.breed_category).toBe('Dairy') // 預設值
        expect(store.isLoading).toBe(false)
        expect(store.resultHtml).toBe('')
        expect(store.error).toBe('')
      })
    })
  })

  describe('表單驗證與數據處理', () => {
    it('應該正確處理數值類型的欄位', () => {
      const store = useConsultationStore()
      const data = {
        Body_Weight_kg: '50.5',  // 字符串
        Age_Months: 24,          // 數字
        target_average_daily_gain_g: null // null
      }

      store.setFormData(data)

      expect(store.form.Body_Weight_kg).toBe('50.5') // 保持原始類型
      expect(store.form.Age_Months).toBe(24)
      expect(store.form.target_average_daily_gain_g).toBe(null)
    })

    it('應該處理特殊字符和中文輸入', () => {
      const store = useConsultationStore()
      const data = {
        EarNum: 'G001-測試',
        other_remarks: '特殊符號: @#$%^&*()，中文註解'
      }

      store.setFormData(data)

      expect(store.form.EarNum).toBe('G001-測試')
      expect(store.form.other_remarks).toBe('特殊符號: @#$%^&*()，中文註解')
    })

    it('應該處理空值和未定義的欄位', () => {
      const store = useConsultationStore()
      const data = {
        EarNum: '',
        Breed: null,
        Body_Weight_kg: undefined,
        nonExistentField: 'should be ignored'
      }

      store.setFormData(data)

      expect(store.form.EarNum).toBe('')
      expect(store.form.Breed).toBe(null)
      expect(store.form.Body_Weight_kg).toBe(null)
      expect(store.form.nonExistentField).toBeUndefined()
    })
  })

  describe('邊界條件處理', () => {
    it('應該處理 API 連接錯誤', async () => {
      const store = useConsultationStore()
      const networkError = { message: 'Network Error' }

      api.getRecommendation.mockRejectedValue(networkError)

      await store.getRecommendation('test-key')

      expect(store.error).toBe('Network Error')
    })

    it('應該處理未知錯誤', async () => {
      const store = useConsultationStore()

      api.getRecommendation.mockRejectedValue({})

      await store.getRecommendation('test-key')

      expect(store.error).toBe('獲取建議時發生未知錯誤')
    })

    it('應該處理空的 API 響應', async () => {
      const store = useConsultationStore()

      api.getRecommendation.mockResolvedValue({})

      await store.getRecommendation('test-key')

      expect(store.resultHtml).toBeUndefined()
      expect(store.error).toBe('')
    })

    it('應該處理非常大的表單數據', () => {
      const store = useConsultationStore()
      const largeData = {
        EarNum: 'G001',
        other_remarks: 'x'.repeat(10000) // 非常長的註解
      }

      store.setFormData(largeData)

      expect(store.form.EarNum).toBe('G001')
      expect(store.form.other_remarks.length).toBe(10000)
    })

    it('應該處理並發的 getRecommendation 請求', async () => {
      const store = useConsultationStore()
      
      api.getRecommendation.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => resolve({ recommendation_html: '<div>建議</div>' }), 50)
        })
      })

      // 同時發送多個請求
      const promises = [
        store.getRecommendation('key1'),
        store.getRecommendation('key2'),
        store.getRecommendation('key3'),
      ]

      await Promise.all(promises)

      expect(store.isLoading).toBe(false)
      expect(store.resultHtml).toBe('<div>建議</div>')
    })
  })
})
