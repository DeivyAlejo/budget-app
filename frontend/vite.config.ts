import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Expose dev server on the local network so other devices can access it.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
  },
})
