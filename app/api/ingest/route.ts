import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
// 引用剛修好的 Prompt
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

    // 1. Agent 思考 (Feature 5: Daily Prompt)
    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: DAILY_INGEST_PROMPT + "\n\nCURRENT DATE: " + date + "\nINPUT:\n" + text }] }]
    });
    const data = JSON.parse(result.response.text());

    // 2. 寫入資料庫
    const logEntry = await prisma.logEntry.upsert({
      where: { date: new Date(data.meta.date) },
      update: { content: data.markdown_body, mood: data.meta.metrics.mood, focus: data.meta.metrics.focus },
      create: { date: new Date(data.meta.date), content: data.markdown_body, mood: data.meta.metrics.mood, focus: data.meta.metrics.focus }
    });

    // 3. Google Task 推送 (Feature 2)
    if (data.tasks?.length > 0 && process.env.ZAPIER_TASK_WEBHOOK) {
        fetch(process.env.ZAPIER_TASK_WEBHOOK, {
            method: 'POST',
            body: JSON.stringify({ tasks: data.tasks, source: "LifeOS Agent" })
        }).catch(e => console.error("Zapier Error", e));
    }

    return NextResponse.json({ success: true, data });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}