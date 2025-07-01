import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
//export default defineConfig({
//  plugins: [react()],
//})

export default defineConfig({
  plugins:[react(),tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5177,
    strictPort: true,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
