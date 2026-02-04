// 檔案: frontend-body/tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    // [關鍵修復] 確保這裡指向正確的資料夾
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}', // 如果 lib 裡有用到樣式
  ],
  theme: {
    extend: {
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      // [關鍵] 這裡定義了動畫，如果沒載入，Menu 會很僵硬
      animation: {
        'scale-in': 'scale-in 0.15s ease-out forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
export default config;