import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/wards': 'http://localhost:8000',
      '/alerts': 'http://localhost:8000',
      '/anomalies': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
