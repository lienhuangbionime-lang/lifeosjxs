import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { DAILY_INGEST_PROMPT } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
const model = genAI.getGenerativeModel({ 
  model: "gemini-1.5-flash", 
  generationConfig: { responseMimeType: "application/json" } 
});

export async function POST(req: Request) {
  try {
    const { text, date } = await req.json();

    // 1. Agent 思考與生成
    const userPrompt = `CURRENT DATE: ${date}\nINPUT RAW DATA:\n${text}`;
    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: DAILY_INGEST_PROMPT + "\n\n" + userPrompt }] }]
    });
    const data = JSON.parse(result.response.text());

    // 2. 並發寫入資料庫 (Prisma)
    const logEntry = await prisma.$transaction(async (tx) => {
      // Upsert Log
      const log = await tx.logEntry.upsert({
        where: { date: new Date(data.meta.date) },
        update: { 
          content: data.markdown_body,
          mood: data.meta.metrics.mood,
          focus: data.meta.metrics.focus,
          energy: data.meta.metrics.energy 
        },
        create: {
          date: new Date(data.meta.date),
          content: data.markdown_body,
          mood: data.meta.metrics.mood,
          focus: data.meta.metrics.focus,
          energy: data.meta.metrics.energy
        }
      });

      // Insert Tasks & Projects
      if (data.tasks?.length) {
        for (const t of data.tasks) {
          let projectId = null;
          if (t.project_tag) {
            const proj = await tx.project.upsert({
              where: { name: t.project_tag },
              update: {},
              create: { name: t.project_tag }
            });
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
              status: "PENDING" // 標記為等待推送
            }
          });
        }
      }
      return log;
    });

    // 3. [NEW] 觸發 Zapier Webhook (傳送 Google Tasks)
    if (data.tasks?.length > 0 && process.env.ZAPIER_TASK_WEBHOOK) {
        // 不等待回應 (Fire-and-forget) 以加快前端速度
        fetch(process.env.ZAPIER_TASK_WEBHOOK, {
            method: 'POST',
            body: JSON.stringify({ 
                tasks: data.tasks, 
                source_log: logEntry.date 
            })
        }).catch(err => console.error("Zapier Push Error:", err));
    }

    return NextResponse.json({ success: true, data });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ success: false, error: "Ingest Failed" }, { status: 500 });
  }
}