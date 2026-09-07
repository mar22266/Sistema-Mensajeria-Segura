import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 18473,
    proxy: {
      "/auth": "http://localhost:17841",
      "/users": "http://localhost:17841",
      "/messages": "http://localhost:17841",
      "/groups": "http://localhost:17841",
      "/blockchain": "http://localhost:17841",
      "/contacts": "http://localhost:17841",
      "/salud": "http://localhost:17841"
    }
  }
});
