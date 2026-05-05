import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"
// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? './' : '/',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
}));
