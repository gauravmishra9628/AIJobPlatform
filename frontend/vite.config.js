import { defineConfig } from "vite";

export default defineConfig({
  preview: {
    host: true,
    allowedHosts: ["aijobplatform-1.onrender.com", "aijobplatform-3.onrender.com"],
  },
});