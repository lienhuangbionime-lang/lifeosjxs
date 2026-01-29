import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT, PROMPT_VERSION } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

// 1. 定義模型變數 (方便統一管理)
// 注意: 目前 Google 最新穩定版是 1.5-flash 或 1.5-pro。
// 如果你有 2.0 權限可用 "gemini-2.0-flash-exp"
const MODEL_NAME = "gemini-2.5-flash"; 

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
    const aiSignature = `\n\n> 🤖 **AI Insight** | Model: ${MODEL_NAME} | Engine: ${PROMPT_VERSION}`;
    const finalContent = data.markdown_body + aiSignature;

    // 4. 資料庫寫入
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
            // 更新 AI 來源資訊
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
            // 寫入 AI 來源資訊
            aiModel: MODEL_NAME,
            isAi: true
          }
        });
      }

      // 任務處理保持不變
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
              status: "PENDING"
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