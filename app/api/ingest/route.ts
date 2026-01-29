import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { AGENTIC_INGEST_SYSTEM_PROMPT } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
const model = genAI.getGenerativeModel({ 
  model: "gemini-1.5-flash", 
  generationConfig: { responseMimeType: "application/json" } 
});

export async function POST(req: Request) {
  try {
    const { text, date } = await req.json();
    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;

    // 1. Agent 思考
    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\n" + userPrompt }] }]
    });
    const data = JSON.parse(result.response.text());

    // 2. 資料庫寫入 (Safety Fix: Append instead of Overwrite)
    await prisma.$transaction(async (tx) => {
      // 檢查是否已有當日紀錄
      const existingLog = await tx.logEntry.findUnique({ where: { date: new Date(data.meta.date) } });

      let log;
      if (existingLog) {
        // [Fix] 如果存在，則追加內容
        log = await tx.logEntry.update({
          where: { date: new Date(data.meta.date) },
          data: {
            // 保留舊內容，追加新內容 (用分隔線分開)
            content: existingLog.content + "\n\n---\n\n" + data.markdown_body,
            // 數值更新為最新評估
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy
          }
        });
      } else {
        // 如果不存在，則建立新紀錄
        log = await tx.logEntry.create({
          data: {
            date: new Date(data.meta.date),
            content: data.markdown_body,
            mood: data.meta.metrics.mood,
            focus: data.meta.metrics.focus,
            energy: data.meta.metrics.energy
          }
        });
      }

      // 任務與專案 (保持不變)
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

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ success: false, error: "Ingest Failed" }, { status: 500 });
  }
}