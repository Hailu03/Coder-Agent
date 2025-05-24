import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import path from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['@tiptap/react', '@tiptap/starter-kit', '@tiptap/extension-highlight', '@tiptap/extension-text-style', '@tiptap/extension-color', '@tiptap/extension-code-block'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    commonjsOptions: {
      include: ['@tiptap/react', '@tiptap/starter-kit', '@tiptap/extension-highlight', '@tiptap/extension-text-style', '@tiptap/extension-color', '@tiptap/extension-code-block']
    }
  },
  server: {
    port: 3000,
    watch: {
      usePolling: true, // Thử bật tùy chọn này
    },
    host: true,
  },
})
