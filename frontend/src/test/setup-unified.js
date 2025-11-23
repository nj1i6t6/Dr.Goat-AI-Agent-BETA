import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// 全局 Mock 設定
global.console = {
  ...console,
  // 在測試期間抑制某些 console 輸出
  warn: vi.fn(),
  error: vi.fn()
}

// 設定 Vue Test Utils 全局組件 stubs
config.global.stubs = {
  'el-form': true,
  'el-form-item': true,
  'el-input': true,
  'el-select': true,
  'el-option': true,
  'el-button': true,
  'el-card': true,
  'el-row': true,
  'el-col': true,
  'el-tabs': true,
  'el-tab-pane': true,
  'el-alert': true,
  'el-dialog': true,
  'el-table': true,
  'el-table-column': true,
  'el-pagination': true,
  'el-tooltip': true,
  'el-icon': true,
  'FieldHelper': true,
  'SheepFilter': true,
  'SheepModal': true,
  'BasicInfoTab': true,
  'HealthTab': true,
  'ProductionTab': true,
  'BreedingTab': true
}

// Mock window objects
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000'
  },
  writable: true
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.sessionStorage = sessionStorageMock

// Mock URL 構造函數
global.URL = class URL {
  constructor(url, base) {
    this.href = url
    this.origin = base || 'http://localhost:3000'
  }
}

// Mock File and FileReader for file upload tests
global.File = class File {
  constructor(chunks, filename, options = {}) {
    this.chunks = chunks
    this.name = filename
    this.size = chunks.reduce((acc, chunk) => acc + chunk.length, 0)
    this.type = options.type || ''
    this.lastModified = Date.now()
  }
}

global.FileReader = class FileReader {
  constructor() {
    this.readyState = 0
    this.result = null
    this.error = null
    this.onload = null
    this.onerror = null
  }
  
  readAsText(file) {
    setTimeout(() => {
      this.readyState = 2
      this.result = 'mock file content'
      if (this.onload) this.onload({ target: this })
    }, 0)
  }
  
  readAsArrayBuffer(file) {
    setTimeout(() => {
      this.readyState = 2
      this.result = new ArrayBuffer(8)
      if (this.onload) this.onload({ target: this })
    }, 0)
  }
}
