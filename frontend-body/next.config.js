/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // 判斷是否為開發環境
    const isDev = process.env.NODE_ENV === 'development';

    return [
      {
        source: '/api/py/:path*',
        // [修正] 本地測試時指向 localhost:8000，上線時才指向 Render
        // [修正] 優先讀取環境變數，否則依據環境自動判斷
        destination: process.env.NEXT_PUBLIC_PYTHON_API_URL
          ? `${process.env.NEXT_PUBLIC_PYTHON_API_URL}/api/v1/:path*`
          : isDev
            ? 'http://127.0.0.1:8000/api/v1/:path*'
            : 'https://lifeosjxs.onrender.com/api/v1/:path*',
      },
    ]
  },
}

module.exports = nextConfig