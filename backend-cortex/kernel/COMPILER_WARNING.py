
# ⚠️ Cortex 警告：C 編譯失敗
# 由於您的 Windows 系統中沒有安裝 GCC 編譯器，
# LifeOS 已進入「雲端純淨模式 (Cloud-Only Mode)」。

# 影響範圍：
# 1. 本機 C Kernel (life_v3.c) 暫時失效。
# 2. 資料只會寫入 Supabase (雲端)。
# 3. 不會產生 life.index / life.text 本機檔案。

# 如何修復 (任選一種)：
# A. 安裝 MinGW-w64 (推薦)
#    https://www.mingw-w64.org/downloads/
#    安裝後將 bin 目錄加入 PATH 環境變數。
#
# B. 使用 Visual Studio Build Tools
#    如果您有安裝 VS C++，可以使用 cl.exe (但指令不同)。
#
# C. 忽略此錯誤
#    LifeOS 仍然可以運作，只是沒有「數位原版」備份。

print("⚠️ C Kernel Compiler (gcc) not found.")
print("☁️ Running in Cloud-Only Mode (Supabase).")
print("   To enable Local Kernel, install MinGW-w64 or GCC.")
