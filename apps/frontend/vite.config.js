import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'sam.chat',
      'www.sam.chat',
      '65.109.54.94',
      'localhost',
      '127.0.0.1'
    ],
    proxy: {
      // Proxy /api requests to the backend server running on port 3000
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        // secure: false, // Uncomment if backend is not HTTPS
        // rewrite: (path) => path.replace(/^\/api/, '') // Uncomment if backend doesn't expect /api prefix
      }
    }
  }
})
