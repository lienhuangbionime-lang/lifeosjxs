/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // 前端呼叫路徑
        source: '/api/py/:path*',
        // [關鍵修改] 填入您剛獲得的 Render 網址
        // 注意：Render 網址後要加上 /api/v1/ 因為我們後端 main.py 有設定 prefix
        destination: 'https://lifeosjxs.onrender.com', 
      },
    ]
  },
}

module.exports = nextConfig