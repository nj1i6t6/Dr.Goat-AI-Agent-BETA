// 🎯 精簡測試設定檔
import { setupTestMocks } from './mocks.js'

// 一次性設定所有 Mock
setupTestMocks()

// 全局測試工具
global.nextTick = () => new Promise(resolve => setTimeout(resolve, 0))
