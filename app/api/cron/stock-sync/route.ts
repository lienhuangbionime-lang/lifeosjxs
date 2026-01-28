import { NextResponse } from 'next/server';

export async function GET(req: Request) {
  // 簡單驗證，防止被路人亂 call
  if (req.headers.get('Authorization') !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // 這裡你可以呼叫 Python 爬蟲，或者直接在這裡用 fetch 抓取股票 API
  console.log("執行每日股票同步...");
  // ... 你的邏輯 ...

  return NextResponse.json({ success: true, message: "Sync Started" });
}