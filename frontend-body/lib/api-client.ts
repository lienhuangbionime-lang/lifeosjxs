import createClient from "openapi-fetch";
import type { paths } from "@/lib/types/api-schema"; // 剛剛生成的檔案

// 建立強型別的神經客戶端
export const apiClient = createClient<paths>({ 
  // 透過 next.config.js 的 rewrite 轉發到 Python
  baseUrl: "/api/py", 
});

// [使用範例] (您可以複製這段去 CaptureView 取代原本的 fetch)
/*
const { data, error } = await apiClient.POST("/api/v1/ingest", {
  body: { 
    text: "測試訊息", 
    date: "2024-02-04" 
  } 
});

if (data) {
  // 這裡打 data. 時，IDE 會自動跳出 thought_trace, mood, focus...
  console.log(data.thought_trace.observation); 
}
*/