import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  test: {
    // 🎯 精簡配置 - 只保留必要選項
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/tests/setup.simple.js'],
    
    // 🚀 性能優化
    pool: 'threads',
    poolOptions: {
      threads: { singleThread: true }
    },
    
    // 📊 覆蓋率設定
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        'node_modules/**',
        'src/tests/**',
        '**/*.test.js',
        'src/main.js'
      ],
      thresholds: {
        global: {
          statements: 85,
          branches: 80,
          functions: 85,
          lines: 85
        }
      }
    },
    
    // ⚡ 執行優化
    testTimeout: 10000,
    hookTimeout: 10000,
    include: [
      'src/**/*.{test,spec}.{simple,essential}.js',
      'src/tests/*.essential.test.js'
    ]
  }
})
