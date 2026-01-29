import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT, PROMPT_VERSION } from "@/lib/ai/prompts"; // [Cite: 3]
import { NextResponse } from "next/server";

// 1. 定義模型變數 (方便統一管理與切換)
// 目前穩定版建議使用 gemini-1.5-flash
const MODEL_NAME = "gemini-1.5-flash"; 

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
const model = genAI.getGenerativeModel({ 
  model: MODEL_NAME, 
  generationConfig: { responseMimeType: "application/json" } 
});

export async function POST(req: Request) {
  try {
    const { text, date } = await req.json();
    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;

    // 2. Agent 思考
    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\n" + userPrompt }] }]
    });
    const data = JSON.parse(result.response.text());

    // 3. 製作 AI 簽名檔 (讓你在前端直接看得到是誰整理的)
    // 格式: 🤖 AI Insight | Model: gemini-1.5-flash | Engine: v7.1
    const aiSignature = `\n\n> 🤖 **AI Insight** | Model: ${MODEL_NAME} | Engine: ${PROMPT_VERSION}`;
    
    // 將簽名檔追加到 Markdown 內容後
    const finalContent = data.markdown_body + aiSignature;

    // 4. 資料庫寫入
    await prisma.$transaction(async (tx) => {
      // 檢查是否已有當日紀錄
      const existingLog = await tx.logEntry.findUnique({ where: { date: new Date(data.meta.date) } });

      let log;
      if (existingLog) {
        // [Append Mode] 若存在則追加，保留舊內容
        log = await tx.logEntry.update({
          where: { date: new Date(data.meta.date) },
          data: {
            content: existingLog.content + "\n\n---\n\n" + finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            // [Update] 更新 AI 來源資訊
            aiModel: MODEL_NAME,
            isAi: true
          }
        });
      } else {
        // [Create Mode] 若不存在則建立
        log = await tx.logEntry.create({
          data: {
            date: new Date(data.meta.date),
            content: finalContent,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy,
            // [Insert] 寫入 AI 來源資訊
            aiModel: MODEL_NAME,
            isAi: true,
            // 處理 habits (若 prompt 有回傳)
            habits: data.habits || undefined
          }
        });
      }

      // 任務處理 (保持原樣)
      if (data.tasks?.length) {
        for (const t of data.tasks) {
          let projectId = null;
          if (t.project_tag) {
            const proj = await tx.project.upsert({ where: { name: t.project_tag }, update: {}, create: { name: t.project_tag } });
            projectId = proj.id;
          }
          await tx.task.create({
            data: {
              title: t.title,
              context: t.context,
              dueDate: t.due_date ? new Date(t.due_date) : null,
              isUrgent: t.category === "urgent",
              projectId,
              logEntryId: log.id,
              status: "PENDING" // [Cite: 4]
            }
          });
        }
      }
    });

    return NextResponse.json({ success: true, model: MODEL_NAME });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ success: false, error: "Ingest Failed" }, { status: 500 });
  }
}