/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // [FIX] On Windows, 'localhost' can resolve to IPv6 (::1) while uvicorn
    // listens on IPv4. Always use 127.0.0.1 explicitly in dev to avoid proxy hang.
    const prodUrl = 'https://lifeosjxs.onrender.com';
    const devUrl = 'http://127.0.0.1:8000';

    const isProd = process.env.NODE_ENV === 'production';
    const base = isProd
      ? (process.env.NEXT_PUBLIC_PYTHON_API_URL || prodUrl)
      : devUrl;

    return [
      {
        source: '/api/py/:path*',
        destination: `${base}/api/v1/:path*`,
      },
    ]
  },
}

module.exports = nextConfig