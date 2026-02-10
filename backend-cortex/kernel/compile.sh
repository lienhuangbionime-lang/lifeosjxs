#!/bin/bash
# LifeOS C Kernel - Linux/Mac 編譯腳本
#
# 使用方式：
#   ./compile.sh          - 編譯 C Kernel
#   ./compile.sh test     - 編譯並測試
#   ./compile.sh clean    - 清理編譯產物

echo "========================================"
echo "LifeOS C Kernel Compiler"
echo "========================================"
echo ""

# 檢查 gcc 是否安裝
if ! command -v gcc &> /dev/null; then
    echo "[ERROR] gcc not found!"
    echo ""
    echo "Please install gcc:"
    echo "  Mac: xcode-select --install"
    echo "  Ubuntu/Debian: sudo apt-get install gcc"
    echo "  CentOS/RHEL: sudo yum install gcc"
    echo ""
    exit 1
fi

echo "[INFO] gcc found:"
gcc --version | head -n 1
echo ""

# 切換到 kernel 目錄
cd "$(dirname "$0")"

# 創建 storage 目錄
if [ ! -d "storage" ]; then
    echo "[INFO] Creating storage directory..."
    mkdir -p storage
fi

# 根據參數執行不同操作
case "$1" in
    clean)
        echo "[INFO] Cleaning..."
        rm -f life_v3.so test_kernel
        echo "[SUCCESS] Cleaned"
        ;;
    
    test)
        echo "[INFO] Compiling test version..."
        gcc -DTEST_MODE -o test_kernel life_v3.c
        
        if [ $? -eq 0 ]; then
            echo "[SUCCESS] Test compiled successfully"
            echo ""
            echo "[INFO] Running test..."
            echo "========================================"
            ./test_kernel
            echo "========================================"
            echo ""
            
            # 清理測試執行檔
            rm -f test_kernel
        else
            echo "[ERROR] Test compilation failed!"
            exit 1
        fi
        ;;
    
    *)
        echo "[INFO] Compiling C Kernel..."
        gcc -shared -fPIC -o life_v3.so life_v3.c
        
        if [ $? -eq 0 ]; then
            echo "[SUCCESS] Compiled successfully: life_v3.so"
            echo ""
            ls -lh life_v3.so
        else
            echo "[ERROR] Compilation failed!"
            exit 1
        fi
        ;;
esac

echo ""
echo "Done!"
