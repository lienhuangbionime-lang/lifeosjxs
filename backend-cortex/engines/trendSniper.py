#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TrendSniper V24 台股掃描引擎
[Cortex Sync Edition]
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import json
import os
from typing import Optional, Dict, List, Any
from bs4 import BeautifulSoup
import chardet

# ==========================================
# 📐 SYSTEM CONSTITUTION (憲章參數)
# ==========================================
class Config:
    LOOKBACK_DAYS = 200
    MA_LONG = 90
    MA_SHORT = 20
    TH_TREND_GAP = 1.01
    TH_KISS_DIST = 0.02
    TH_VWAP_DEV_MAX = 0.15
    TH_VOL_COMPRESS = 0.5
    MIN_PRICE = 10
    MIN_VOL_AMT = 50000000

# ==========================================
# 🛠️ ENGINE CORE (引擎核心)
# ==========================================
class TrendSniperEngine:
    def __init__(self, progress_callback=None):
        self.report = []
        self.progress_callback = progress_callback

    def _emit_progress(self, current: int, total: int, ticker: str = ""):
        if self.progress_callback:
            self.progress_callback({
                "current": current,
                "total": total,
                "ticker": ticker,
                "percentage": int((current / total * 100)) if total > 0 else 0
            })

    def get_all_tw_tickers(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        market_types = [(2, '.TW', '上市'), (4, '.TWO', '上櫃')]
        all_dfs = []
        for mode, suffix, market_name in market_types:
            url = f"https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}"
            try:
                r = requests.get(url, verify=False, headers=headers, timeout=10)
                df = pd.read_html(r.text)[0]
                df.columns = df.iloc[0]
                df = df.iloc[2:]
                df['代號'] = df['有價證券代號及名稱'].apply(lambda x: str(x).split()[0])
                df = df[df['代號'].apply(lambda x: len(str(x)) == 4)]
                df['名稱'] = df['有價證券代號及名稱'].apply(lambda x: str(x).split()[-1])
                df['Type'] = suffix
                all_dfs.append(df[['代號', '名稱', 'Type', '產業別']].copy())
            except Exception as e:
                print(f"❌ {market_name} 清單抓取失敗: {e}")
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True)
        return pd.DataFrame()

    def fetch_data(self, ticker_full):
        try:
            stock = yf.Ticker(ticker_full)
            df = stock.history(period="1y")
            if df.empty: return None, None
            return df, stock.info
        except: return None, None

    def fetch_fubon_notes(self, ticker: str) -> str:
        try:
            url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco_{ticker}_4.djhtm"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, verify=False, headers=headers, timeout=5)
            detected = chardet.detect(response.content)
            encoding = detected.get('encoding', 'big5') or 'big5'
            try:
                html = response.content.decode(encoding)
            except:
                html = response.content.decode('big5', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            lines = text.split('\n')
            notes_parts = [line.strip() for line in lines if any(k in line for k in ['法人', '主力', '融資', '融券', '本益比', '殖利率', '股價淨值比']) if len(line.strip()) > 5]
            return ' | '.join(notes_parts[:3]) if notes_parts else ""
        except: return ""

    def analyze(self, ticker, name, suffix):
        ticker_full = f"{ticker}{suffix}"
        df, info = self.fetch_data(ticker_full)
        if df is None or len(df) < 100: return None
        close, vol = df['Close'], df['Volume']
        if close.empty or vol.empty: return None
        last_close, last_vol = close.iloc[-1], vol.iloc[-1]

        if (last_close < Config.MIN_PRICE) or (last_close * last_vol < Config.MIN_VOL_AMT):
            return None

        ma20 = close.ewm(span=Config.MA_SHORT, adjust=False).mean()
        ma90 = close.ewm(span=Config.MA_LONG, adjust=False).mean()

        if ma90.iloc[-1] == 0: return None
        f3_gap = ma20.iloc[-1] / ma90.iloc[-1]

        if ma20.iloc[-1] == 0: return None
        dist_ma20 = (last_close - ma20.iloc[-1]) / ma20.iloc[-1]
        f6_kiss = abs(dist_ma20)

        vol_ma = df['Volume'].rolling(60).sum().replace(0, 1)
        vwap_est = (df['Volume'] * df['Close']).rolling(60).sum() / vol_ma
        if pd.isna(vwap_est.iloc[-1]) or vwap_est.iloc[-1] == 0: return None
        f10_dev = (last_close - vwap_est.iloc[-1]) / vwap_est.iloc[-1]

        high_5, low_5 = df['High'].rolling(5).max(), df['Low'].rolling(5).min()
        if low_5.iloc[-1] == 0: return None
        f11_vol = (high_5.iloc[-1] - low_5.iloc[-1]) / low_5.iloc[-1]

        rev_growth = info.get('revenueGrowth', 0) if info else 0
        if rev_growth is not None and rev_growth < 0: return None

        if f3_gap < Config.TH_TREND_GAP: return None

        is_trend_up = (ma20.iloc[-1] > ma90.iloc[-1]) and (ma90.iloc[-1] > ma90.iloc[-5])
        is_pullback = f6_kiss < Config.TH_KISS_DIST
        is_not_hot = f10_dev < Config.TH_VWAP_DEV_MAX

        if is_trend_up and is_pullback and is_not_hot:
            notes = self.fetch_fubon_notes(ticker)
            return {
                "代號": ticker, "名稱": name, "訊號": "💋 回調鎖定",
                "現價": round(last_close, 2), "MA20距離%": round(dist_ma20 * 100, 2),
                "F3強度": round(f3_gap, 2), "F11壓縮度": round(f11_vol * 100, 2),
                "營收成長": f"{rev_growth:.1%}" if rev_growth else "N/A",
                "建議停損": round(ma90.iloc[-1], 2), "備註": notes
            }
        return None

    def run(self, ticker_list: Optional[List[Dict]] = None):
        if ticker_list is None:
            df_list = self.get_all_tw_tickers()
            if df_list.empty: return {"success": False, "error": "無法獲取清單"}
        else:
            df_list = pd.DataFrame(ticker_list)
        target_list = df_list.values.tolist()
        total = len(target_list)
        for idx, row in enumerate(target_list):
            self._emit_progress(idx, total, str(row[0]))
            try:
                res = self.analyze(str(row[0]), str(row[1]), str(row[2]) if len(row) > 2 else '.TW')
                if res: self.report.append(res)
                time.sleep(0.01)
            except: continue
        return {"success": True, "total_tickers": total, "matched_count": len(self.report), "results": self.report}

if __name__ == "__main__":
    import sys
    # [Fix] Progress Output to Stdout for Node.js scanApi
    def json_callback(d):
        print(f"PROGRESS:{json.dumps(d)}", flush=True)
    
    engine = TrendSniperEngine(progress_callback=json_callback)
    result = engine.run()
    # Print final JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))
