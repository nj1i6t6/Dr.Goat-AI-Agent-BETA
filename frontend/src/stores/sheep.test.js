/**
 * sheep.js Store 測試
 * 測試羊隻資料狀態管理功能
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSheepStore } from '@/stores/sheep'

// Mock errorHandler 避免循環依賴
vi.mock('@/utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

// 模擬 API 模組
vi.mock('@/api', () => ({
  default: {
    getAllSheep: vi.fn(),
  },
}))

import api from '@/api'

describe('sheep Store', () => {
  beforeEach(() => {
    // 為每個測試創建新的 Pinia 實例
    setActivePinia(createPinia())
    // 清除所有模擬調用記錄
    vi.clearAllMocks()
  })

  describe('初始狀態', () => {
    it('應該有正確的初始狀態', () => {
      const store = useSheepStore()
      
      expect(store.sheepList).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.hasLoaded).toBe(false)
    })
  })

  describe('Getters', () => {
    it('sortedSheepList 應該按耳號排序', () => {
      const store = useSheepStore()
      
      // 設置測試數據
      store.sheepList = [
        { EarNum: 'A003', Breed: '波爾羊' },
        { EarNum: 'A001', Breed: '台灣黑山羊' },
        { EarNum: 'A002', Breed: '努比亞羊' },
        { EarNum: 'A10', Breed: '薩能羊' }, // 測試數字排序
      ]

      const sorted = store.sortedSheepList
      expect(sorted[0].EarNum).toBe('A001')
      expect(sorted[1].EarNum).toBe('A002')
      expect(sorted[2].EarNum).toBe('A003')
      expect(sorted[3].EarNum).toBe('A10')
    })

    it('filterOptions 應該返回不重複的篩選選項', () => {
      const store = useSheepStore()
      
      store.sheepList = [
        { EarNum: 'A001', Breed: '波爾羊', FarmNum: 'F001' },
        { EarNum: 'A002', Breed: '台灣黑山羊', FarmNum: 'F001' },
        { EarNum: 'A003', Breed: '波爾羊', FarmNum: 'F002' },
        { EarNum: 'A004', Breed: null, FarmNum: null }, // 測試空值處理
        { EarNum: 'A005', Breed: '', FarmNum: '' }, // 測試空字符串處理
      ]

      const options = store.filterOptions
      expect(options.breeds).toEqual(['台灣黑山羊', '波爾羊'])
      expect(options.farmNums).toEqual(['F001', 'F002'])
    })
  })

  describe('Actions', () => {
    describe('fetchSheepList', () => {
      it('應該成功獲取羊群列表', async () => {
        const store = useSheepStore()
        const mockData = [
          { EarNum: 'A001', Breed: '波爾羊' },
          { EarNum: 'A002', Breed: '台灣黑山羊' },
        ]

        // 模擬 API 成功回應
        api.getAllSheep.mockResolvedValue(mockData)

        await store.fetchSheepList()

        expect(store.isLoading).toBe(false)
        expect(store.hasLoaded).toBe(true)
        expect(store.sheepList).toEqual(mockData)
        expect(api.getAllSheep).toHaveBeenCalledTimes(1)
      })

      it('在 loading 時不應該重複請求', async () => {
        const store = useSheepStore()
        store.isLoading = true

        await store.fetchSheepList()

        expect(api.getAllSheep).not.toHaveBeenCalled()
      })

      it('已載入時不應該重複請求 (除非 force=true)', async () => {
        const store = useSheepStore()
        store.hasLoaded = true

        // 不強制刷新
        await store.fetchSheepList()
        expect(api.getAllSheep).not.toHaveBeenCalled()

        // 強制刷新
        await store.fetchSheepList(true)
        expect(api.getAllSheep).toHaveBeenCalledTimes(1)
      })

      it('應該處理 API 錯誤', async () => {
        const store = useSheepStore()
        const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

        // 模擬 API 錯誤
        api.getAllSheep.mockRejectedValue(new Error('網路錯誤'))

        await store.fetchSheepList()

        expect(store.isLoading).toBe(false)
        expect(store.hasLoaded).toBe(false)
        expect(store.sheepList).toEqual([])
        expect(consoleErrorSpy).toHaveBeenCalledWith('獲取羊群列表失敗:', expect.any(Error))

        consoleErrorSpy.mockRestore()
      })

      it('loading 狀態應該正確切換', async () => {
        const store = useSheepStore()
        
        // 模擬延遲的 API 調用
        let resolvePromise
        const mockPromise = new Promise((resolve) => {
          resolvePromise = resolve
        })
        api.getAllSheep.mockReturnValue(mockPromise)

        // 開始請求
        const fetchPromise = store.fetchSheepList()
        expect(store.isLoading).toBe(true)

        // 完成請求
        resolvePromise([])
        await fetchPromise
        expect(store.isLoading).toBe(false)
      })
    })

    describe('addSheep', () => {
      it('應該添加新羊隻到列表', () => {
        const store = useSheepStore()
        const newSheep = { EarNum: 'A001', Breed: '波爾羊' }

        store.addSheep(newSheep)

        expect(store.sheepList[0]).toEqual(newSheep)
        expect(store.sheepList).toHaveLength(1)
      })
    })

    describe('updateSheep', () => {
      it('應該更新現有羊隻', () => {
        const store = useSheepStore()
        const originalSheep = { id: 1, EarNum: 'A001', Breed: '波爾羊' }
        const updatedSheep = { id: 1, EarNum: 'A001', Breed: '台灣黑山羊' }

        store.sheepList = [originalSheep]
        store.updateSheep(updatedSheep)

        expect(store.sheepList[0]).toEqual(updatedSheep)
        expect(store.sheepList).toHaveLength(1)
      })

      it('如果找不到羊隻應該添加為新的', () => {
        const store = useSheepStore()
        const existingSheep = { id: 1, EarNum: 'A001', Breed: '波爾羊' }
        const newSheep = { id: 2, EarNum: 'A002', Breed: '台灣黑山羊' }

        store.sheepList = [existingSheep]
        store.updateSheep(newSheep)

        expect(store.sheepList).toHaveLength(2)
        expect(store.sheepList[1]).toEqual(newSheep)
      })
    })

    describe('removeSheep', () => {
      it('應該根據耳號移除羊隻', () => {
        const store = useSheepStore()
        const sheep1 = { EarNum: 'A001', Breed: '波爾羊' }
        const sheep2 = { EarNum: 'A002', Breed: '台灣黑山羊' }

        store.sheepList = [sheep1, sheep2]
        store.removeSheep('A001')

        expect(store.sheepList).toHaveLength(1)
        expect(store.sheepList[0]).toEqual(sheep2)
      })

      it('移除不存在的羊隻不應該影響列表', () => {
        const store = useSheepStore()
        const sheep1 = { EarNum: 'A001', Breed: '波爾羊' }

        store.sheepList = [sheep1]
        store.removeSheep('A999')

        expect(store.sheepList).toHaveLength(1)
        expect(store.sheepList[0]).toEqual(sheep1)
      })
    })

    describe('refreshSheepList', () => {
      it('應該強制重新獲取羊群列表', async () => {
        const store = useSheepStore()
        store.hasLoaded = true
        
        const mockData = [{ EarNum: 'A001', Breed: '波爾羊' }]
        api.getAllSheep.mockResolvedValue(mockData)

        await store.refreshSheepList()

        expect(api.getAllSheep).toHaveBeenCalledTimes(1)
        expect(store.sheepList).toEqual(mockData)
      })
    })
  })

  describe('複雜場景測試', () => {
    it('應該處理大量羊隻資料的排序', () => {
      const store = useSheepStore()
      
      // 生成大量測試資料
      const testData = []
      for (let i = 100; i >= 1; i--) {
        testData.push({
          EarNum: `A${i.toString().padStart(3, '0')}`,
          Breed: i % 2 === 0 ? '波爾羊' : '台灣黑山羊'
        })
      }

      store.sheepList = testData
      const sorted = store.sortedSheepList

      // 檢查是否正確排序
      expect(sorted[0].EarNum).toBe('A001')
      expect(sorted[99].EarNum).toBe('A100')
      expect(sorted).toHaveLength(100)
    })

    it('應該處理包含特殊字符的耳號排序', () => {
      const store = useSheepStore()
      
      store.sheepList = [
        { EarNum: 'B-002', Breed: '波爾羊' },
        { EarNum: 'A_001', Breed: '台灣黑山羊' },
        { EarNum: 'C.003', Breed: '努比亞羊' },
        { EarNum: '001-A', Breed: '薩能羊' },
      ]

      const sorted = store.sortedSheepList
      
      // 確保沒有拋出錯誤，且返回了正確數量的項目
      expect(sorted).toHaveLength(4)
      expect(sorted.every(sheep => sheep.EarNum)).toBe(true)
    })
  })
})
