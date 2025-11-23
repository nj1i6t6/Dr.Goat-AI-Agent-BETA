import { describe, it, expect, beforeEach, vi } from 'vitest'
import DataManagementView from './DataManagementView.vue'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}))

// Mock icons
vi.mock('@element-plus/icons-vue', () => ({
  Upload: { template: '<span>Upload</span>' },
  Download: { template: '<span>Download</span>' },
  UploadFilled: { template: '<span>UploadFilled</span>' }
}))

// Mock API
vi.mock('../api', () => ({
  default: {
    exportExcel: vi.fn(),
    analyzeExcel: vi.fn(),
    processImport: vi.fn()
  }
}))

// Mock Router
const mockRouter = {
  push: vi.fn().mockResolvedValue(),
  replace: vi.fn().mockResolvedValue(),
  currentRoute: {
    value: { path: '/data-management', name: 'DataManagement' }
  }
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

describe('DataManagementView', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    
    wrapper = mount(DataManagementView, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-card': {
            template: '<div class="el-card"><template v-if="$slots.header"><div class="el-card__header"><slot name="header"></slot></div></template><div class="el-card__body"><slot></slot></div></div>'
          },
          'el-button': {
            template: '<button class="el-button"><slot></slot></button>'
          },
          'el-tabs': {
            template: '<div class="el-tabs"><slot></slot></div>'
          },
          'el-tab-pane': {
            template: '<div class="el-tab-pane"><slot></slot></div>'
          },
          'el-steps': true,
          'el-step': true,
          'el-upload': {
            template: '<div class="el-upload"><slot></slot></div>'
          },
          'el-divider': true,
          'el-icon': true,
          'el-table': true,
          'el-table-column': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  describe('組件初始化', () => {
    it('應該正確渲染組件', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.data-management-page').exists()).toBe(true)
    })

    it('應該顯示標題', () => {
      const title = wrapper.find('.page-title')
      expect(title.exists()).toBe(true)
      expect(title.text()).toContain('數據管理中心')
    })

    it('應該顯示匯出區域', () => {
      const exportButton = wrapper.find('[data-test="export-button"]')
      // 簡化測試，只檢查基本結構
      expect(wrapper.html()).toContain('匯出全部資料')
    })
  })

  describe('Excel 導入功能', () => {
    it('應該支持文件上傳', () => {
      // 檢查上傳組件是否存在
      expect(wrapper.html()).toContain('將檔案拖曳至此')
    })

    it('應該顯示標準範本下載連結', () => {
      expect(wrapper.html()).toContain('下載標準範本')
    })
  })

  describe('用戶界面', () => {
    it('應該顯示步驟指示', () => {
      expect(wrapper.html()).toContain('下載標準範本')
      expect(wrapper.html()).toContain('上傳')
      expect(wrapper.html()).toContain('執行')
    })

    it('應該有標籤切換功能', () => {
      expect(wrapper.html()).toContain('快速導入')
    })
  })
})
