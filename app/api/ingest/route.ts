import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT } from "@/lib/ai/prompts"; //
import { NextResponse } from "next/server";

// 確保使用穩定的模型名稱
const MODEL_NAME = "gemini-1.5-flash"; 

export async function POST(req: Request) {
  try {
    // 1. [檢查點] 確認環境變數是否存在
    if (!process.env.GEMINI_API_KEY) {
      console.error("❌ Critical: GEMINI_API_KEY is missing in environment variables.");
      return NextResponse.json({ success: false, error: "Server Config Error: Missing API Key" }, { status: 500 });
    }

    const { text, date } = await req.json();
    console.log(`🚀 [Ingest] Processing for ${date} with model ${MODEL_NAME}`);

    // 2. 初始化 AI
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ 
      model: MODEL_NAME, 
      generationConfig: { responseMimeType: "application/json" } 
    });

    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;

    // 3. [檢查點] 呼叫 AI (並捕捉特定錯誤)
    console.log("🤖 [Ingest] Calling Gemini API...");
    let result;
    try {
        result = await model.generateContent({
          contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\n" + userPrompt }] }]
        });
    } catch (aiError: any) {
        console.error("❌ [Ingest] Gemini API Call Failed:", aiError);
        return NextResponse.json({ success: false, error: `AI Connection Error: ${aiError.message}` }, { status: 502 });
    }
    
    const responseText = result.response.text();
    console.log("✅ [Ingest] AI Response received.");

    // 4. [檢查點] 解析 JSON
    let data: any;
    try {
        data = JSON.parse(responseText);
    } catch (parseError) {
        console.error("❌ [Ingest] JSON Parse Failed. Raw text:", responseText);
        // 如果解析失敗，回傳原始文字讓你知道發生什麼事
        return NextResponse.json({ success: false, error: "AI returned invalid JSON", raw: responseText }, { status: 500 });
    }

    // 5. 製作簽名檔
    // 注意：這裡移除了 PROMPT_VERSION 的引用，因為你的 imports 可能沒包含它
    const aiSignature = `\n\n> 🤖 **AI Insight** | Model: ${MODEL_NAME}`;
    const finalContent = data.markdown_body + aiSignature;

    // 6. 資料庫寫入
    console.log("💾 [Ingest] Writing to Database...");
    await prisma.$transaction(async (tx) => {
      const existingLog = await tx.logEntry.findUnique({ where: { date: new Date(data.meta.date) } });

      let log;
      if (existingLog) {
        log = await tx.logEntry.update({
          where: { date: new Date(data.meta.date) },
          data: {
            content: existingLog.content + "\n\n---\n\n" + finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            // [New] 寫入模型資訊 (Schema 需支援這些欄位，若無請先移除這兩行)
            // aiModel: MODEL_NAME, 
            // isAi: true
          }
        });
      } else {
        log = await tx.logEntry.create({
          data: {
            date: new Date(data.meta.date),
            content: finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            // [New] 寫入模型資訊
            // aiModel: MODEL_NAME,
            // isAi: true,
            habits: data.habits || undefined
          }
        });
      }

      // 任務寫入
      if (data.tasks?.length) {
        for (const t of data.tasks) {
          const projectName = t.project_tag || "Inbox";
          const proj = await tx.project.upsert({ where: { name: projectName }, update: {}, create: { name: projectName } });
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
    console.error("🔥 [Ingest] Unhandled Error:", error);
    // 回傳具體錯誤訊息給前端
    return NextResponse.json({ success: false, error: error.message || "Internal Server Error" }, { status: 500 });
  }
}