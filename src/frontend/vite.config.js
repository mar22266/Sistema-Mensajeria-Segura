import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/users": "http://localhost:8000",
      "/messages": "http://localhost:8000",
      "/groups": "http://localhost:8000",
      "/blockchain": "http://localhost:8000",
      "/salud": "http://localhost:8000"
    }
  }
});