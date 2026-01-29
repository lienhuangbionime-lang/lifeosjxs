import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT, PROMPT_VERSION } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

// [Critical Fix] 修正模型名稱
// Google 目前支援: "gemini-1.5-flash", "gemini-1.5-pro"
// "gemini-2.5-flash" 是不存在的，會導致 API 錯誤。
const MODEL_NAME = "gemini-1.5-flash"; 

export async function POST(req: Request) {
  try {
    // 0. 環境變數檢查
    if (!process.env.GEMINI_API_KEY) {
      console.error("❌ Critical: GEMINI_API_KEY is missing in environment variables.");
      return NextResponse.json({ success: false, error: "Server Config Error: Missing API Key" }, { status: 500 });
    }

    const { text, date } = await req.json();
    console.log(`🚀 [Ingest] Starting process for ${date} with model ${MODEL_NAME}`);

    // 1. 初始化 AI
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ 
      model: MODEL_NAME, 
      generationConfig: { responseMimeType: "application/json" } 
    });

    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;

    // 2. Agent 思考 (加入錯誤捕捉)
    console.log("🤖 [Ingest] Calling Google Gemini API...");
    let result;
    try {
        result = await model.generateContent({
          contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\n" + userPrompt }] }]
        });
    } catch (aiError: any) {
        console.error("❌ [Ingest] Gemini API Call Failed:", aiError);
        return NextResponse.json({ success: false, error: `AI Error: ${aiError.message}` }, { status: 502 });
    }
    
    const responseText = result.response.text();
    console.log("✅ [Ingest] AI Response received.");

    // 3. 解析 JSON
    let data: any;
    try {
        data = JSON.parse(responseText);
    } catch (parseError) {
        console.error("❌ [Ingest] JSON Parse Failed:", responseText);
        return NextResponse.json({ success: false, error: "Invalid JSON from AI" }, { status: 500 });
    }

    // 4. 製作簽名檔
    const aiSignature = `\n\n> 🤖 **AI Insight** | Model: ${MODEL_NAME} | Engine: ${PROMPT_VERSION}`;
    const finalContent = data.markdown_body + aiSignature;

    // 5. 資料庫寫入
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
            aiModel: MODEL_NAME,
            isAi: true
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
            aiModel: MODEL_NAME,
            isAi: true,
            habits: data.habits || undefined
          }
        });
      }

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

    console.log("✨ [Ingest] Transaction Complete.");
    return NextResponse.json({ success: true, model: MODEL_NAME, data });

  } catch (error: any) {
    console.error("🔥 [Ingest] Unhandled Error:", error);
    return NextResponse.json({ success: false, error: error.message || "Internal Server Error" }, { status: 500 });
  }
}