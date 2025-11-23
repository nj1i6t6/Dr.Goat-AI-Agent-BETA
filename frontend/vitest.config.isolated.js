import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/tests/setup.isolated.js'],
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: true
      }
    },
    // 隔離測試以避免循環依賴
    isolate: true,
    server: {
      deps: {
        external: ['vue-router', 'pinia']
      }
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/main.js',
        'src/tests/',
        '**/*.spec.js',
        '**/*.test.js',
      ],
    },
  },
})
