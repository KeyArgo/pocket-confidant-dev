import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      // The LLM weights are cached by WebLLM's own Cache Storage layer — do NOT
      // let Workbox try to precache 1GB of model. Only precache the app shell.
      workbox: {
        // Precache the app shell + JS. The big ONNX .wasm (~21MB) and LLM weights
        // are intentionally NOT precached — transformers.js / WebLLM cache those
        // on demand in their own Cache Storage. (Follow-up: code-split web-llm +
        // transformers via dynamic import so the shell isn't 7MB.)
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
        maximumFileSizeToCacheInBytes: 10 * 1024 * 1024,
        navigateFallbackDenylist: [/^\/api/],
      },
      manifest: {
        name: "Pocket Confidant",
        short_name: "Confidant",
        description:
          "A confidential AI partner for self-understanding. 100% on your device.",
        theme_color: "#b07a4f",
        background_color: "#f7f1e6",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
    }),
  ],
  test: {
    globals: true,
    environment: "node",
  },
});
