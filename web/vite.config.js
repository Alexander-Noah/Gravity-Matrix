import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

function shouldIgnoreRolldownWarning(log) {
  return (
    log?.code === 'INVALID_ANNOTATION' &&
    String(log?.id || '').includes('@vueuse/core')
  )
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 1300,
    rolldownOptions: {
      onLog(level, log, defaultHandler) {
        if (level === 'warn' && shouldIgnoreRolldownWarning(log)) {
          return
        }
        defaultHandler(level, log)
      },
      onwarn(warning, defaultHandler) {
        if (shouldIgnoreRolldownWarning(warning)) {
          return
        }
        defaultHandler(warning)
      },
    },
  },
})
