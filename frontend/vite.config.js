import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';
var rootDir = fileURLToPath(new URL('.', import.meta.url));
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(rootDir, './src'),
        },
    },
    server: {
        port: 3000,
    },
});
