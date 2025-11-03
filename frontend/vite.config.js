import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Custom plugin to serve files from output directory
    {
      name: 'serve-output-files',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url?.startsWith('/output/')) {
            const filePath = path.join(__dirname, '..', req.url)

            // Check if file exists
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              // Determine content type
              const ext = path.extname(filePath).toLowerCase()
              const contentTypes = {
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.html': 'text/html',
                '.md': 'text/markdown',
              }

              res.setHeader('Content-Type', contentTypes[ext] || 'application/octet-stream')
              res.setHeader('Access-Control-Allow-Origin', '*')

              // Read and send file
              const fileContent = fs.readFileSync(filePath)
              res.end(fileContent)
              return
            }
          }
          next()
        })
      }
    }
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
