"""
LifeOS v3.1 - C Kernel Driver
Python 驅動程式，用於調用 C Kernel

設計理念：
- C Kernel: 數位原版（不可變、永久保存）
- Supabase: 工作副本（可編輯、可搜尋）
- 雙寫入策略：同時寫入兩處
"""

import ctypes
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple


# ============================================================================
# Path Configuration
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
KERNEL_DIR = BASE_DIR / "kernel"
STORAGE_DIR = KERNEL_DIR / "storage"

# C 語言檔案
C_SOURCE = KERNEL_DIR / "life_v3.c"
C_LIBRARY = KERNEL_DIR / "life_v3.so"  # Linux/Mac
if os.name == 'nt':  # Windows
    C_LIBRARY = KERNEL_DIR / "life_v3.dll"

# 資料檔案
IDX_PATH = STORAGE_DIR / "life.index"
TXT_PATH = STORAGE_DIR / "life.text"
MEDIA_PATH = STORAGE_DIR / "life.media"

# 確保目錄存在
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# C Structure Definitions (must match C code)
# ============================================================================

class DiaryMarker(ctypes.Structure):
    """對應 C 的 DiaryMarker 結構（32 bytes）"""
    _fields_ = [
        ("text_offset", ctypes.c_uint32),
        ("text_len", ctypes.c_uint32),
        ("created_at", ctypes.c_uint64),
        ("mood", ctypes.c_uint8),
        ("focus", ctypes.c_uint8),
        ("energy", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("word_count", ctypes.c_uint32),
        ("media_head_ptr", ctypes.c_uint32),
        ("media_count", ctypes.c_uint32),
        ("date_yyyymmdd", ctypes.c_uint32),
    ]


class MediaRef(ctypes.Structure):
    """對應 C 的 MediaRef 結構（64 bytes）"""
    _fields_ = [
        ("content_hash", ctypes.c_uint8 * 16),
        ("media_type", ctypes.c_uint8),
        ("storage_class", ctypes.c_uint8),
        ("duration_sec", ctypes.c_uint16),
        ("file_size_kb", ctypes.c_uint32),
        ("timestamp", ctypes.c_uint64),
        ("storage_path", ctypes.c_char * 16),
        ("compression_ratio", ctypes.c_uint32),
        ("width", ctypes.c_uint16),
        ("height", ctypes.c_uint16),
        ("next_media_ptr", ctypes.c_uint32),
        ("prev_media_ptr", ctypes.c_uint32),
    ]


# ============================================================================
# Kernel Driver
# ============================================================================

class LifeKernel:
    """
    C Kernel 驅動程式
    
    功能：
    - 編譯 C 代碼（如果需要）
    - 調用 C 函數
    - 提供 Python 友善的介面
    """
    
    def __init__(self, auto_compile: bool = True):
        """
        初始化 Kernel
        
        Args:
            auto_compile: 如果 .so/.dll 不存在，自動編譯
        """
        self.lib = None
        
        # 自動編譯（如果需要）
        if auto_compile and not C_LIBRARY.exists():
            print("🔨 Compiling C Kernel...")
            self._compile()
        
        # 載入 C 函式庫
        if C_LIBRARY.exists():
            self._load_library()
        else:
            raise FileNotFoundError(
                f"C library not found: {C_LIBRARY}\n"
                f"Please compile manually: gcc -shared -fPIC -o {C_LIBRARY} {C_SOURCE}"
            )
    
    def _compile(self):
        """自動編譯 C 代碼"""
        try:
            if os.name == 'nt':  # Windows
                # 使用 MinGW 或 MSVC
                cmd = [
                    "gcc",
                    "-shared",
                    "-o", str(C_LIBRARY),
                    str(C_SOURCE)
                ]
            else:  # Linux/Mac
                cmd = [
                    "gcc",
                    "-shared",
                    "-fPIC",
                    "-o", str(C_LIBRARY),
                    str(C_SOURCE)
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Compiled successfully: {C_LIBRARY}")
            else:
                print(f"❌ Compilation failed:\n{result.stderr}")
                raise RuntimeError("C compilation failed")
        
        except FileNotFoundError:
            print("❌ gcc not found. Please install gcc or compile manually.")
            raise
    
    def _load_library(self):
        """載入 C 函式庫"""
        self.lib = ctypes.CDLL(str(C_LIBRARY))
        
        # 定義函數簽名
        # int log_entry(const char* idx_path, const char* txt_path, uint32_t day_offset, 
        #               const char* text, uint8_t mood, uint8_t focus, uint8_t energy)
        self.lib.log_entry.argtypes = [
            ctypes.c_char_p,  # idx_path
            ctypes.c_char_p,  # txt_path
            ctypes.c_uint32,  # day_offset
            ctypes.c_char_p,  # text
            ctypes.c_uint8,   # mood
            ctypes.c_uint8,   # focus
            ctypes.c_uint8,   # energy
        ]
        self.lib.log_entry.restype = ctypes.c_int
        
        # int read_entry(const char* idx_path, const char* txt_path, uint32_t day_offset,
        #                DiaryMarker* marker, char* text, size_t max_len)
        self.lib.read_entry.argtypes = [
            ctypes.c_char_p,           # idx_path
            ctypes.c_char_p,           # txt_path
            ctypes.c_uint32,           # day_offset
            ctypes.POINTER(DiaryMarker), # marker
            ctypes.c_char_p,           # text
            ctypes.c_size_t,           # max_len
        ]
        self.lib.read_entry.restype = ctypes.c_int
        
        # uint32_t calculate_day_offset(int year, int month, int day)
        self.lib.calculate_day_offset.argtypes = [
            ctypes.c_int,  # year
            ctypes.c_int,  # month
            ctypes.c_int,  # day
        ]
        self.lib.calculate_day_offset.restype = ctypes.c_uint32
    
    def save(self, date: datetime, content: str, mood: int, focus: int, energy: int) -> bool:
        """
        儲存日記到 C Kernel（Append-Only）
        
        Args:
            date: 日期
            content: 文字內容
            mood: 心情 (0-10)
            focus: 專注度 (0-10)
            energy: 能量 (0-10)
        
        Returns:
            True=成功, False=已存在（不可變）
        """
        # 計算天數偏移
        day_offset = self.lib.calculate_day_offset(
            date.year,
            date.month,
            date.day
        )
        
        # 調用 C 函數
        result = self.lib.log_entry(
            str(IDX_PATH).encode('utf-8'),
            str(TXT_PATH).encode('utf-8'),
            day_offset,
            content.encode('utf-8'),
            mood,
            focus,
            energy
        )
        
        if result == 1:
            print(f"✅ Kernel: Day {day_offset} ({date.date()}) locked successfully.")
            return True
        elif result == 0:
            print(f"⚠️ Kernel: Day {day_offset} ({date.date()}) already exists. Immutable.")
            return False
        else:
            print(f"❌ Kernel: Error writing day {day_offset}")
            return False
    
    def read(self, date: datetime) -> Optional[Tuple[DiaryMarker, str]]:
        """
        從 C Kernel 讀取日記
        
        Args:
            date: 日期
        
        Returns:
            (DiaryMarker, text) 或 None（如果不存在）
        """
        # 計算天數偏移
        day_offset = self.lib.calculate_day_offset(
            date.year,
            date.month,
            date.day
        )
        
        # 準備緩衝區
        marker = DiaryMarker()
        text_buffer = ctypes.create_string_buffer(65536)  # 64KB
        
        # 調用 C 函數
        result = self.lib.read_entry(
            str(IDX_PATH).encode('utf-8'),
            str(TXT_PATH).encode('utf-8'),
            day_offset,
            ctypes.byref(marker),
            text_buffer,
            len(text_buffer)
        )
        
        if result == 1:
            text = text_buffer.value.decode('utf-8')
            return (marker, text)
        else:
            return None
    
    def get_day_offset(self, date: datetime) -> int:
        """獲取天數偏移（從 2026-01-01 開始）"""
        return self.lib.calculate_day_offset(date.year, date.month, date.day)


# ============================================================================
# Usage Example
# ============================================================================

def example_usage():
    """使用範例"""
    kernel = LifeKernel()
    
    # 儲存日記
    today = datetime.now()
    success = kernel.save(
        date=today,
        content="今天完成了 C Kernel 的實現，這是數位原版！",
        mood=8,
        focus=9,
        energy=7
    )
    
    if success:
        print("✅ 日記已鎖定到 C Kernel")
    else:
        print("⚠️ 該日期已存在記錄（不可變）")
    
    # 讀取日記
    result = kernel.read(today)
    if result:
        marker, text = result
        print(f"\n📖 讀取成功:")
        print(f"  心情: {marker.mood}")
        print(f"  專注: {marker.focus}")
        print(f"  能量: {marker.energy}")
        print(f"  內容: {text}")
    else:
        print("❌ 該日期沒有記錄")


if __name__ == "__main__":
    example_usage()
