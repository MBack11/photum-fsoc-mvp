import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Project Pages URL: https://mback11.github.io/photum-fsoc-mvp/
export default defineConfig({
  plugins: [react()],
  base: '/photum-fsoc-mvp/',
})
