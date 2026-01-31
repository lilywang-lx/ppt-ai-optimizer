import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // PPT系统后端API
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // AI产品经理工作台 - 静态资源和页面
      '/AIplatform': {
        target: 'http://localhost:5180',
        changeOrigin: true
      },
      // AI产品经理工作台 - 后端API (需要区分路径)
      '/pm-api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/pm-api/, '/api')
      }
    }
  }
})
