import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { MONTHLY_REVIEW_PROMPT } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" }); // 使用 Pro 模型處理長文本

export async function POST(req: Request) {
  try {
    const { month } = await req.json(); // e.g., "2024-01"
    
    // 1. 撈取整個月的資料
    const logs = await prisma.logEntry.findMany({
        where: {
            date: {
                gte: new Date(`${month}-01`),
                lt: new Date(`${month}-31`) // 簡化寫法
            }
        },
        include: { tasks: true }
    });

    if (logs.length === 0) return NextResponse.json({ success: false, error: "No logs found" });

    // 2. 壓縮資料餵給 AI
    const context = JSON.stringify(logs.map(l => ({
        date: l.date,
        metrics: { mood: l.mood, focus: l.focus },
        content: l.content
    })));

    // 3. 執行 CCA 分析
    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: MONTHLY_REVIEW_PROMPT + "\n\nMONTHLY DATA:\n" + context }] }]
    });
    
    const analysis = JSON.parse(result.response.text());

    // 4. 回傳給前端顯示
    return NextResponse.json({ success: true, data: analysis });

  } catch (error) {
    return NextResponse.json({ success: false, error: "Analysis Failed" }, { status: 500 });
  }
}