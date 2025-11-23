import { defineConfig } from 'vitest/config'
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
    setupFiles: ['./src/test/setup-unified.js'],
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true
      }
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        // dependencies and build artifacts
        'node_modules/**',
        'dist/**',
        'coverage/**',
        // app bootstrap and test scaffolding
        'src/main.js',
        'src/test/**',
        'src/tests/**',
        // root config files (do not count towards coverage)
        'vite.config.*',
        'vitest.config.*',
        // test files themselves
        '**/*.spec.*',
        '**/*.test.*',
      ],
    },
    fileParallelism: false,
    isolate: true,
  },
  server: {
    port: 5173,
  },
})
