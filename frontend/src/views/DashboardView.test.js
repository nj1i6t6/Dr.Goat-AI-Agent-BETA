/**
 * DashboardView 測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import DashboardView from './DashboardView.vue'
import { useSettingsStore } from '../stores/settings'
import api from '../api'

// Mock api
vi.mock('../api', () => ({
  default: {
    getAllSheep: vi.fn(),
    getDashboardData: vi.fn(),
    getFarmReport: vi.fn(),
    getAgentStatus: vi.fn(),
    getAgentTip: vi.fn(),
  }
}))

// Mock router
const mockRouter = {
  push: vi.fn()
}

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn()
  },
  ElMessageBox: {
    alert: vi.fn()
  }
}))

describe('DashboardView', () => {
  let wrapper
  let pinia
  let settingsStore

  // Mock data
  const mockSheepList = [
    { id: 1, ear_num: 'SH001', name: 'Test Sheep 1' },
    { id: 2, ear_num: 'SH002', name: 'Test Sheep 2' }
  ]

  const mockDashboardData = {
    reminders: [
      {
        ear_num: 'SH001',
        type: '疫苗接種',
        due_date: '2024-01-15',
        status: '即將到期'
      }
    ],
    health_alerts: [
      {
        ear_num: 'SH002',
        type: '健康檢查',
        message: '需要檢查體溫'
      }
    ],
    flock_status_summary: [
      { status: 'maintenance', count: 5 },
      { status: 'lactating_peak', count: 3 }
    ],
    esg_metrics: {
      fcr: 2.5
    }
  }

  const mockFarmReport = {
    flock_composition: {
      total: 10,
      by_breed: [
        { name: '努比亞', count: 6 },
        { name: '波爾', count: 4 }
      ],
      by_sex: [
        { name: '母羊', count: 7 },
        { name: '公羊', count: 3 }
      ]
    },
    production_summary: {
      avg_birth_weight: 3.2,
      avg_litter_size: 1.8,
      avg_milk_yield: 2.5
    },
    health_summary: {
      top_diseases: [
        { name: '感冒', count: 5 },
        { name: '腹瀉', count: 3 }
      ]
    }
  }

  beforeEach(() => {
    pinia = createPinia()
    
    wrapper = mount(DashboardView, {
      global: {
        plugins: [pinia],
        mocks: {
          $router: mockRouter
        },
        stubs: {
          'el-result': {
            template: '<div class="el-result"><slot name="extra" /></div>'
          },
          'el-button': {
            template: '<button @click="$emit(\'click\')"><slot /></button>',
            emits: ['click']
          },
          'el-card': {
            template: '<div class="el-card"><slot name="header" /><slot /></div>'
          },
          'el-row': {
            template: '<div class="el-row"><slot /></div>'
          },
          'el-col': {
            template: '<div class="el-col"><slot /></div>'
          },
          'el-empty': {
            template: '<div class="el-empty">{{ description }}</div>',
            props: ['description']
          },
          'el-alert': {
            template: '<div class="el-alert"><slot /></div>',
            props: ['title', 'type', 'closable', 'showIcon']
          },
          'el-tag': {
            template: '<span class="el-tag">{{ $slots.default?.[0]?.children || "" }}</span>',
            props: ['type', 'size', 'effect']
          }
        }
      }
    })

    settingsStore = useSettingsStore()

    // 重置所有 mocks
    vi.clearAllMocks()
    api.getAgentStatus.mockResolvedValue({ rag_enabled: false, message: '', detail: null })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  describe('初始化和數據加載', () => {
    it('應該正確初始化組件', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.dashboard-page').exists()).toBe(true)
    })

    it('當沒有羊隻時應該顯示引導畫面', async () => {
      api.getAllSheep.mockResolvedValue([])
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.el-result').exists()).toBe(true)
      expect(wrapper.vm.hasSheep).toBe(false)
    })

    it('當有羊隻時應該顯示儀表板內容', async () => {
    api.getAllSheep.mockResolvedValue(mockSheepList)
    api.getDashboardData.mockResolvedValue(mockDashboardData)
    api.getAgentStatus.mockResolvedValue({ rag_enabled: true, message: 'RAG Ready', detail: 'test' })
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.hasSheep).toBe(true)
      expect(wrapper.vm.initialLoading).toBe(false)
    })

    it('應該處理 API 錯誤', async () => {
      const { ElMessage } = await import('element-plus')
      api.getAllSheep.mockRejectedValue(new Error('API Error'))
      
      await wrapper.vm.fetchInitialData()
      
      expect(ElMessage.error).toHaveBeenCalledWith('無法獲取羊群資料')
      expect(wrapper.vm.initialLoading).toBe(false)
    })
  })

  describe('數據顯示', () => {
    beforeEach(async () => {
      api.getAllSheep.mockResolvedValue(mockSheepList)
      api.getDashboardData.mockResolvedValue(mockDashboardData)
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()
    })

    it('應該正確顯示提醒事項', () => {
      expect(wrapper.vm.dashboardData.reminders).toEqual(mockDashboardData.reminders)
    })

    it('應該正確顯示健康警示', () => {
      expect(wrapper.vm.dashboardData.health_alerts).toEqual(mockDashboardData.health_alerts)
    })

    it('應該正確顯示羊群狀態摘要', () => {
      expect(wrapper.vm.dashboardData.flock_status_summary).toEqual(mockDashboardData.flock_status_summary)
    })

    it('應該正確顯示 ESG 指標', () => {
      expect(wrapper.vm.dashboardData.esg_metrics).toEqual(mockDashboardData.esg_metrics)
    })
  })

  describe('狀態映射', () => {
    it('應該正確映射狀態文本', () => {
      expect(wrapper.vm.getStatusText('maintenance')).toBe('維持期')
      expect(wrapper.vm.getStatusText('lactating_peak')).toBe('泌乳高峰期')
      expect(wrapper.vm.getStatusText('unknown_status')).toBe('unknown_status')
      expect(wrapper.vm.getStatusText(null)).toBe('未分類')
    })

    it('應該正確映射標籤類型', () => {
      expect(wrapper.vm.getTagType('已過期')).toBe('danger')
      expect(wrapper.vm.getTagType('即將到期')).toBe('warning')
      expect(wrapper.vm.getTagType('停藥中')).toBe('info')
      expect(wrapper.vm.getTagType('其他')).toBe('primary')
    })
  })

  describe('報告生成', () => {
    beforeEach(async () => {
      api.getAllSheep.mockResolvedValue(mockSheepList)
      api.getDashboardData.mockResolvedValue(mockDashboardData)
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()
    })

    it('應該成功生成農場報告', async () => {
      const { ElMessageBox } = await import('element-plus')
      api.getFarmReport.mockResolvedValue(mockFarmReport)
      
      await wrapper.vm.generateFarmReport()
      
      expect(api.getFarmReport).toHaveBeenCalled()
      expect(ElMessageBox.alert).toHaveBeenCalled()
      expect(wrapper.vm.reportLoading).toBe(false)
    })

    it('應該處理報告生成錯誤', async () => {
      const { ElMessage } = await import('element-plus')
      const error = { error: '生成報告失敗' }
      api.getFarmReport.mockRejectedValue(error)
      
      await wrapper.vm.generateFarmReport()
      
      expect(ElMessage.error).toHaveBeenCalledWith('生成報告失敗: 生成報告失敗')
      expect(wrapper.vm.reportLoading).toBe(false)
    })

    it('應該在生成報告時顯示載入狀態', async () => {
      api.getFarmReport.mockImplementation(() => new Promise(resolve => {
        setTimeout(() => resolve(mockFarmReport), 100)
      }))
      
      const reportPromise = wrapper.vm.generateFarmReport()
      
      expect(wrapper.vm.reportLoading).toBe(true)
      await reportPromise
      expect(wrapper.vm.reportLoading).toBe(false)
    })
  })

  describe('路由導航', () => {
    it('應該正確導航到數據管理頁面', async () => {
      api.getAllSheep.mockResolvedValue([])
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()

      const button = wrapper.find('button')
      await button.trigger('click')
      
      expect(mockRouter.push).toHaveBeenCalledWith('/data-management')
    })
  })

  describe('Store 集成', () => {
    it('應該調用 settings store 的 fetchAndSetAgentTip', async () => {
      api.getAllSheep.mockResolvedValue(mockSheepList)
      api.getDashboardData.mockResolvedValue(mockDashboardData)
      
      const fetchSpy = vi.spyOn(settingsStore, 'fetchAndSetAgentTip')
      
      await wrapper.vm.fetchInitialData()
      
      expect(fetchSpy).toHaveBeenCalled()
    })
  })

  describe('邊界條件處理', () => {
    it('應該處理空的儀表板數據', async () => {
      api.getAllSheep.mockResolvedValue(mockSheepList)
      api.getDashboardData.mockResolvedValue({
        reminders: [],
        health_alerts: [],
        flock_status_summary: [],
        esg_metrics: {}
      })
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.dashboardData.reminders).toEqual([])
      expect(wrapper.vm.dashboardData.health_alerts).toEqual([])
    })

    it('應該處理缺少 FCR 數據的情況', async () => {
      api.getAllSheep.mockResolvedValue(mockSheepList)
      api.getDashboardData.mockResolvedValue({
        ...mockDashboardData,
        esg_metrics: {}
      })
      
      await wrapper.vm.fetchInitialData()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.dashboardData.esg_metrics.fcr).toBeUndefined()
    })

    it('應該處理儀表板數據載入失敗', async () => {
      const { ElMessage } = await import('element-plus')
      api.getAllSheep.mockResolvedValue(mockSheepList)
      api.getDashboardData.mockRejectedValue({ error: '載入失敗' })
      
      await wrapper.vm.fetchInitialData()
      
      expect(ElMessage.error).toHaveBeenCalledWith('載入儀表板數據失敗: 載入失敗')
    })
  })
})
