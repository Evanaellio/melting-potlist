import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            vue: 'vue/dist/vue.esm-bundler.js',
        },
    },
    base: "/content/",
    build: {
        outDir: "./dist",
        manifest: true,
        rollupOptions: {
            input: '/src/main.js',
        },
        modulePreload: {
            polyfill: false
        }
    }
})