@echo off
REM LifeOS C Kernel - Windows 編譯腳本
REM 
REM 使用方式：
REM   compile.bat          - 編譯 C Kernel
REM   compile.bat test     - 編譯並測試
REM   compile.bat clean    - 清理編譯產物

echo ========================================
echo LifeOS C Kernel Compiler
echo ========================================
echo.

REM 檢查 gcc 是否安裝
where gcc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] gcc not found!
    echo.
    echo Please install MinGW:
    echo https://sourceforge.net/projects/mingw/
    echo.
    pause
    exit /b 1
)

echo [INFO] gcc found: 
gcc --version | findstr "gcc"
echo.

REM 切換到 kernel 目錄
cd /d "%~dp0"

REM 創建 storage 目錄
if not exist "storage" (
    echo [INFO] Creating storage directory...
    mkdir storage
)

REM 根據參數執行不同操作
if "%1"=="clean" goto CLEAN
if "%1"=="test" goto TEST
goto COMPILE

:COMPILE
echo [INFO] Compiling C Kernel...
gcc -shared -o life_v3.dll life_v3.c

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Compiled successfully: life_v3.dll
    echo.
    dir life_v3.dll | findstr "life_v3.dll"
) else (
    echo [ERROR] Compilation failed!
    pause
    exit /b 1
)

goto END

:TEST
echo [INFO] Compiling test version...
gcc -DTEST_MODE -o test_kernel.exe life_v3.c

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Test compilation failed!
    pause
    exit /b 1
)

echo [SUCCESS] Test compiled successfully
echo.
echo [INFO] Running test...
echo ========================================
test_kernel.exe
echo ========================================
echo.

REM 清理測試執行檔
del test_kernel.exe

goto END

:CLEAN
echo [INFO] Cleaning...
if exist "life_v3.dll" del life_v3.dll
if exist "test_kernel.exe" del test_kernel.exe
echo [SUCCESS] Cleaned
goto END

:END
echo.
echo Done!
pause
