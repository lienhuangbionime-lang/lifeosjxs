import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/db";
import { MONTHLY_REVIEW_PROMPT } from "@/lib/ai/prompts";
import { NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });

export async function POST(req: Request) {
  try {
    const { month } = await req.json(); // e.g. "2024-02"
    // 簡單撈取該月所有日記
    const logs = await prisma.logEntry.findMany({
        where: { date: { gte: new Date(`${month}-01`), lt: new Date(`${month}-31`) } }
    });
    
    if (logs.length === 0) return NextResponse.json({ error: "No data" });

    const result = await model.generateContent({
      contents: [{ role: "user", parts: [{ text: MONTHLY_REVIEW_PROMPT + "\n\nLOGS:\n" + JSON.stringify(logs) }] }]
    });
    
    return NextResponse.json({ success: true, analysis: JSON.parse(result.response.text()) });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}