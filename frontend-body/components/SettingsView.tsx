// 檔案: frontend-body/components/SettingsView.tsx
import React, { useState } from 'react';
import { UploadCloud, CheckCircle, AlertTriangle, FileUp } from 'lucide-react';

// [V3 Fix] 定義這個元件能接收什麼資料
interface SettingsProps {
  logs: any[];
  onImport: (logs: any[]) => void;
}

export const SettingsView = ({ logs, onImport }: SettingsProps) => {
  const [status, setStatus] = useState("idle"); 

  // --- 功能 A: 舊記憶遷移 ---
  const migrateToCloud = async () => {
    const localData = localStorage.getItem('life_os_logs_v8_0');
    if (!localData) return alert("瀏覽器中沒有舊資料可遷移");
    
    const localLogs = JSON.parse(localData);
    if (!confirm(`準備將 ${localLogs.length} 筆本地日記上傳至雲端大腦？`)) return;

    setStatus("uploading");

    try {
      let successCount = 0;
      for (const log of localLogs) {
        // 呼叫後端 API
        const res = await fetch('/api/py/api/v1/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: log.note || log.markdown_body || "Old Entry",
            date: log.date
          }),
        });

        if (res.ok) successCount++;
        console.log(`Uploading ${log.date}: ${res.status}`);
      }
      
      alert(`遷移成功！共上傳 ${successCount} 筆回憶。`);
      setStatus("done");

    } catch (e) {
      console.error(e);
      alert("遷移過程中發生錯誤，請檢查 Console");
      setStatus("idle");
    }
  };

  return (
    <div className="p-6 text-slate-300 space-y-8">
      
      {/* 區塊 1: 記憶遷移 */}
      <section>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <UploadCloud className="text-indigo-400"/> 
          記憶同步中心
        </h2>
        
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <p className="mb-4 text-sm text-slate-400">
            目前系統共有 <span className="text-white font-bold">{logs.length}</span> 筆記憶正在運作。
            <br/>
            若您剛從 V2 升級，請點擊下方按鈕將瀏覽器快取寫入雲端資料庫。
          </p>
          
          <button 
            onClick={migrateToCloud}
            disabled={status === 'uploading'}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold flex items-center gap-2 disabled:opacity-50 transition-colors"
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
      </section>

      {/* 區塊 2: 系統資訊 */}
      <section>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <AlertTriangle className="text-amber-400"/> 
          系統狀態
        </h2>
        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-xs font-mono text-slate-500">
          <div>VERSION: LifeOS v3.1 (Autopoiesis)</div>
          <div>ENV: {process.env.NODE_ENV === 'development' ? 'Localhost' : 'Production'}</div>
          <div>BRAIN: Connected</div>
        </div>
      </section>
    </div>
  );
};