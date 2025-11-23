import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    // 設置代理，解決開發環境下的跨域問題
    proxy: {
      // 當請求路徑以 '/api' 開頭時，觸發代理
      '/api': {
        // 將請求轉發到我們的 Flask 後端伺服器
        target: 'http://127.0.0.1:5001',
        // 允許跨域
        changeOrigin: true,
        // 如果後端 API 的路徑本身不包含 '/api'，可以重寫路徑。
        // 在我們的案例中，後端路徑是 /api/auth/login，所以不需要重寫。
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})