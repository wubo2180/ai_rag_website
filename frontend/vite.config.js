import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://172.20.46.18:8002',
        changeOrigin: true,
        secure: false,
        logLevel: 'debug',
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'static/',
    sourcemap: false,
  },
})
