import React from 'react';
import './globals.css'; // 我們等下會建立這個
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'LifeOS v3.1 Autopoiesis',
  description: 'Biological Operating System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-950 text-slate-100 overflow-hidden`}>
        {children}
      </body>
    </html>
  );
}
