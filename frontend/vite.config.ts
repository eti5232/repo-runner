import { fileURLToPath, URL } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// הפרוקסי /lg מעביר את הבקשות לשרת של LangGraph (langgraph dev) ומונע בעיות CORS.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5180,
    strictPort: true,
    proxy: {
      "/lg": {
        target: process.env.LANGGRAPH_URL ?? "http://127.0.0.1:2024",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/lg/, ""),
      },
    },
  },
});
