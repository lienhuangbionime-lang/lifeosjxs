// 檔案: components/SettingsView.tsx
import React, { useState } from 'react';
import { UploadCloud, CheckCircle, AlertTriangle } from 'lucide-react';

export const SettingsView = () => {
  const [status, setStatus] = useState("idle"); // idle, uploading, done

  const migrateToCloud = async () => {
    // 1. 從舊家拿資料
    const localData = localStorage.getItem('life_os_logs_v8_0');
    if (!localData) return alert("瀏覽器中沒有舊資料可遷移");
    
    const logs = JSON.parse(localData);
    if (!confirm(`準備將 ${logs.length} 筆本地日記上傳至雲端大腦？`)) return;

    setStatus("uploading");

    try {
      let successCount = 0;
      // 2. 開始一筆筆搬運
      for (const log of logs) {
        // 為了避免太快把後端打掛，稍微等一下 (選擇性)
        // await new Promise(r => setTimeout(r, 100)); 

        const res = await fetch('/api/py/api/v1/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: log.note || log.markdown_body || "Old Entry", // 確保有內容
            date: log.date
          }),
        });

        if (res.ok) successCount++;
        console.log(`Uploading ${log.date}: ${res.status}`);
      }
      
      alert(`遷移成功！共上傳 ${successCount} / ${logs.length} 筆回憶。`);
      setStatus("done");

    } catch (e) {
      console.error(e);
      alert("遷移過程中發生錯誤，請檢查 Console");
      setStatus("idle");
    }
  };

  return (
    <div className="p-6 text-slate-300">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <UploadCloud className="text-indigo-400"/> 
        記憶遷移中心
      </h2>
      
      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
        <p className="mb-4 text-sm text-slate-400">
          偵測到您使用 V2 版本的 LocalStorage 儲存機制。
          點擊下方按鈕將資料永久寫入海馬迴 (Supabase)。
        </p>
        
        <button 
          onClick={migrateToCloud}
          disabled={status === 'uploading'}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold flex items-center gap-2 disabled:opacity-50"
        >
          {status === 'uploading' ? (
            <>⏳ 正在上傳中...</>
          ) : status === 'done' ? (
            <><CheckCircle size={18}/> 遷移完成</>
          ) : (
            <><UploadCloud size={18}/> 開始上傳至雲端</>
          )}
        </button>
      </div>
    </div>
  );
};