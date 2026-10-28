import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 로컬 개발: /api 요청은 pnpm dev:api 로 띄운 FastAPI(8000)로 넘긴다.
// 서버에서는 FastAPI 가 빌드된 dist 를 함께 서빙하므로 프록시가 필요 없다.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
