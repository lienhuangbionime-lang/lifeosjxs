import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT, PROMPT_VERSION } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

// [Critical Fix] 請使用正確的模型名稱
// 目前 Google API 支援: "gemini-1.5-flash", "gemini-1.5-pro"
const MODEL_NAME = "gemini-2.5-flash"; 

export async function POST(req: Request) {
  try {
    // 0. 檢查 API Key 是否存在
    if (!process.env.GEMINI_API_KEY) {
      console.error("❌ GEMINI_API_KEY is missing in environment variables.");
      return NextResponse.json({ success: false, error: "Server Configuration Error: Missing API Key" }, { status: 500 });
    }

    const { text, date } = await req.json();
    console.log(`🚀 [Ingest] Starting process for date: ${date}`);

    // 1. 初始化 AI
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ 
      model: MODEL_NAME, 
      generationConfig: { responseMimeType: "application/json" } 
    });

    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;

    // 2. Agent 思考
    console.log(`🤖 [Ingest] Calling Gemini (${MODEL_NAME})...`);
    
    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\n" + userPrompt }] }]
    });
    
    const responseText = result.response.text();
    console.log("✅ [Ingest] Gemini response received.");
    
    // [Fix] 明確宣告型別為 any，解決 TypeScript 編譯錯誤
    let data: any;
    try {
        data = JSON.parse(responseText);
    } catch (e) {
        console.error("❌ [Ingest] JSON Parse Error:", responseText);
        throw new Error("AI returned invalid JSON");
    }

    // 3. 製作 AI 簽名檔
    const aiSignature = `\n\n> 🤖 **AI Insight** | Model: ${MODEL_NAME} | Engine: ${PROMPT_VERSION}`;
    const finalContent = data.markdown_body + aiSignature;

    // 4. 資料庫寫入
    console.log("💾 [Ingest] Writing to Database...");
    await prisma.$transaction(async (tx) => {
      const existingLog = await tx.logEntry.findUnique({ where: { date: new Date(data.meta.date) } });

      let log;
      if (existingLog) {
        // [Append Mode]
        log = await tx.logEntry.update({
          where: { date: new Date(data.meta.date) },
          data: {
            content: existingLog.content + "\n\n---\n\n" + finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            aiModel: MODEL_NAME,
            isAi: true
          }
        });
      } else {
        // [Create Mode]
        log = await tx.logEntry.create({
          data: {
            date: new Date(data.meta.date),
            content: finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            aiModel: MODEL_NAME,
            isAi: true,
            habits: data.habits || undefined
          }
        });
      }

      // 任務處理
      if (data.tasks?.length) {
        for (const t of data.tasks) {
          // 確保專案名稱存在
          const projectName = t.project_tag || "Inbox"; 
          
          const proj = await tx.project.upsert({ 
            where: { name: projectName }, 
            update: {}, 
            create: { name: projectName } 
          });
          
          await tx.task.create({
            data: {
              title: t.title,
              context: t.context,
              dueDate: t.due_date ? new Date(t.due_date) : null,
              isUrgent: t.category === "urgent",
              projectId: proj.id,
              logEntryId: log.id,
              status: "PENDING"
            }
          });
        }
      }
    });

    console.log("✨ [Ingest] Success!");
    return NextResponse.json({ success: true, model: MODEL_NAME, data });

  } catch (error: any) {
    console.error("🔥 [Ingest Critical Error]:", error);
    return NextResponse.json({ success: false, error: error.message || "Unknown Server Error" }, { status: 500 });
  }
}