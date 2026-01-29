import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { MONTHLY_REVIEW_PROMPT } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
// 使用 Pro 模型，因為一個月的日記 token 數較多
const model = genAI.getGenerativeModel({ 
    model: "gemini-1.5-pro",
    generationConfig: { responseMimeType: "application/json" }
});

export async function POST(req: Request) {
  try {
    const { month } = await req.json(); // e.g. "2024-01"
    
    // 1. 撈取該月份所有日記
    const startDate = new Date(`${month}-01`);
    const endDate = new Date(new Date(startDate).setMonth(startDate.getMonth() + 1));
    
    const logs = await prisma.logEntry.findMany({
        where: {
            date: { gte: startDate, lt: endDate }
        },
        select: { date: true, content: true, mood: true, focus: true, habits: true },
        orderBy: { date: 'asc' }
    });

    if (logs.length === 0) return NextResponse.json({ success: false, error: "無資料可分析" });

    // 2. 壓縮資料餵給 Agent
    const context = JSON.stringify(logs);
    const fullPrompt = `${MONTHLY_REVIEW_PROMPT}\n\nTARGET MONTH: ${month}\nDATA:\n${context}`;

    // 3. AI 思考
    const result = await model.generateContent(fullPrompt);
    const analysis = JSON.parse(result.response.text());

    // 4. 存入資料庫 (Upsert)
    const review = await prisma.monthlyReview.upsert({
        where: { month },
        update: {
            content: analysis.cca_report, // Markdown 報告
            strategy: analysis.next_month_config // 戰略目標 JSON
        },
        create: {
            month,
            content: analysis.cca_report,
            strategy: analysis.next_month_config
        }
    });

    return NextResponse.json({ success: true, data: review });

  } catch (error: any) {
    console.error("CCA Analysis Failed:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}