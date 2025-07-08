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
      'api.sam.chat',
      'studio.sam.chat',
      'observatory.sam.chat',
      '65.109.54.94',
      '127.0.0.1',
      'localhost'
    ],
    proxy: {
      // Proxy /api requests to the backend API gateway for sam.chat
      '/api': {
        target: process.env.NODE_ENV === 'production' 
          ? 'https://api.sam.chat'
          : 'http://localhost:3001',
        changeOrigin: true,
        secure: process.env.NODE_ENV === 'production',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  define: {
    'process.env.VITE_API_URL': JSON.stringify(
      process.env.VITE_API_URL || 'https://api.sam.chat'
    ),
    'process.env.VITE_BACKEND_URL': JSON.stringify(
      process.env.VITE_BACKEND_URL || 'https://api.sam.chat'
    ),
    'process.env.VITE_STUDIO_URL': JSON.stringify(
      process.env.VITE_STUDIO_URL || 'https://studio.sam.chat'
    ),
    'process.env.VITE_OBSERVATORY_URL': JSON.stringify(
      process.env.VITE_OBSERVATORY_URL || 'https://observatory.sam.chat'
    ),
    'process.env.VITE_DOMAIN': JSON.stringify(
      process.env.VITE_DOMAIN || 'sam.chat'
    ),
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['lucide-react', 'class-variance-authority', 'clsx', 'tailwind-merge'],
        },
      },
    },
  },
})
