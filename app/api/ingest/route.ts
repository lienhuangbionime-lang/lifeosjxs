// 檔案位置: app/api/ingest/route.ts
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

    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: AGENTIC_INGEST_SYSTEM_PROMPT + "\n\nINPUT:\n" + text }] }]
    });
    const data = JSON.parse(result.response.text());

    await prisma.$transaction(async (tx) => {
      // 這裡不需要特別指定 tx: Prisma.TransactionClient，讓它自動推斷即可
      const log = await tx.logEntry.upsert({
        where: { date: new Date(data.meta.date) },
        update: { 
          content: data.markdown_body,
          mood: data.meta.metrics.mood,
          focus: data.meta.metrics.focus,
          energy: data.meta.metrics.energy,
          vtrRatio: data.meta.metrics.vtr_ratio
        },
        create: {
          date: new Date(data.meta.date),
          content: data.markdown_body,
          mood: data.meta.metrics.mood,
          focus: data.meta.metrics.focus,
          energy: data.meta.metrics.energy,
          vtrRatio: data.meta.metrics.vtr_ratio
        }
      });

      if (data.tasks?.length > 0) {
        for (const t of data.tasks) {
          let projectId = null;
          if (t.project_tag) {
            const project = await tx.project.upsert({
              where: { name: t.project_tag },
              update: {},
              create: { name: t.project_tag, status: "ACTIVE" }
            });
            projectId = project.id;
          }
          await tx.task.create({
            data: {
              title: t.title,
              context: t.context,
              dueDate: t.due_date ? new Date(t.due_date) : undefined,
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