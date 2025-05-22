/// <reference types="vitest" />
/// <reference types="vite/client" />

import { defineConfig } from 'vite';
import solidPlugin from 'vite-plugin-solid';

export default defineConfig({
  plugins: [solidPlugin()],
  server: {
    port: 3000,
  },
  build: {
    target: 'esnext',
  },
  test: {
    globals: true,
    environment: 'jsdom', // or 'happy-dom'
    setupFiles: './vitest.setup.js', 
    transformMode: { web: [/\.[jt]sx?$/] },
    // Solid specific deps configuration
    deps: {
      optimizer: {
        web: {
          include: ['solid-js'] 
        }
      },
      inline: [/solid-js/], // Ensure solid-js is processed by Vite during tests
    },
    // Optional: if you have issues with CSS or assets in tests
    css: true, 
  },
});
