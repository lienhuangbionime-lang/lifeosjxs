
import subprocess
import os
import sys
from datetime import date

# --- CORTEX KERNEL CONFIGURATION ---
# 自動偵測作業系統並選擇對應的二進制核心
if os.name == 'nt':
    # Windows
    KERNEL_BINARY = os.path.join("bin", "life_win64.exe")
else:
    # Linux / Mac (未來擴充用)
    KERNEL_BINARY = os.path.join("bin", "life_linux")

def check_kernel_integrity():
    """
    檢查核心是否存在。
    不再嘗試編譯，而是要求預編譯的二進制檔必須存在。
    """
    if not os.path.exists(KERNEL_BINARY):
        # Silent fallback: Cloud-Only Mode active
        return False
    return True

def write_to_kernel(date_obj, content, mood=5, flags=1):
    """
    呼叫 C Kernel 寫入日記 (執行檔模式)
    """
    if not check_kernel_integrity():
        # Cloud-Only Mode: Skip local write silently
        return False

    try:
        # 構建指令: bin/life_win64.exe write YYYY MM DD "Content" mood flags
        cmd = [
            KERNEL_BINARY,
            "write",
            str(date_obj.year),
            str(date_obj.month),
            str(date_obj.day),
            content,
            str(mood),
            str(flags)
        ]
        
        # 執行外部程序
        # capture_output=True 讓我們能攔截 C 的 printf 輸出
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            # 成功
            print(f"[OK] Kernel Local Backup: {result.stdout.strip()}")
            return True
        else:
            # C 程式回傳錯誤 (例如日期錯誤)
            print(f"[WARN] Kernel Warning: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"[WARN] System Failure (Driver Level): {e}")
        return False

def read_from_kernel(date_obj):
    """
    呼叫 C Kernel 讀取日記
    """
    if not check_kernel_integrity():
        return None

    try:
        cmd = [
            KERNEL_BINARY,
            "read",
            str(date_obj.year),
            str(date_obj.month),
            str(date_obj.day)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None # 該日無資料
            
    except Exception as e:
        print(f"[WARN] Read Failure: {e}")
        return None

# --- 測試區 (直接執行此檔案可測試) ---
if __name__ == "__main__":
    print(f"Testing Kernel Driver with binary: {KERNEL_BINARY}")
    
    # 測試寫入
    test_date = date.today()
    if check_kernel_integrity():
        success = write_to_kernel(test_date, "Cortex Binary Driver Test - Operation Proposal B", mood=10, flags=1)
        
        if success:
            print("\n--- Reading Back Data ---")
            content = read_from_kernel(test_date)
            print(content)
    else:
        print("[ERROR] Binary not found. Please compile or download 'life_win64.exe' to 'bin/' folder.")
