import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Frontend runs on http://localhost:5173 and talks to the FastAPI backend on port 8000
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})