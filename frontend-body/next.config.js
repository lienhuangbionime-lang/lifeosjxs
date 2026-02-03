/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // 建議關閉，避免開發模式下 useEffect 執行兩次
  
  // [CTO 關鍵設定] 建立通往 Python 大腦的神經通道
  async rewrites() {
    return [
      {
        // 當前端呼叫 /api/py/xxx 時...
        source: '/api/py/:path*',
        // 自動轉發到 Python 後端 (Port 8001) 的 /api/v1/xxx
        destination: 'http://127.0.0.1:8001/api/v1/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
