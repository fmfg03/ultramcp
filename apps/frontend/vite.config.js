import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'sam.chat',
      'www.sam.chat',
      '65.109.54.94',
      'sam.chat',
      '127.0.0.1'
    ],
    proxy: {
      // Proxy /api requests to the Claudia MCP service running on port 8013
      '/api': {
        target: 'http://localhost:8013',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
