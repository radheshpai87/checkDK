import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      // Allow `import ... from '@/lib/api'` style imports
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    // Dev-server proxy: requests to /api/* are forwarded to the backend.
    // Useful when running `npm run dev` alongside `uvicorn` locally.
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL ?? 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
})
