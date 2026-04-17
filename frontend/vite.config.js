import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 获取后端 API 地址
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: API_URL,
        changeOrigin: true,
        secure: false
      }
    }
  }
})
