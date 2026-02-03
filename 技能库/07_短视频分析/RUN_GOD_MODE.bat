@echo off
setlocal
chcp 65001 >nul

echo [🤖 ANTIGRAVITY GOD MODE]
echo ==========================================
echo 此脚本将为您启动具备“上帝模式”控制权的 Chrome。
echo 目标配置文件: Profile 4 (您的主账号)
echo ==========================================

echo [1/3] 正在清理现有 Chrome 进程...
taskkill /F /IM chrome.exe /T >nul 2>&1

echo [2/3] 正在清除运行锁 (SingletonLock)...
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\lockfile" del /F /Q "%LOCALAPPDATA%\Google\Chrome\User Data\lockfile" >nul 2>&1
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\SingletonLock" del /F /Q "%LOCALAPPDATA%\Google\Chrome\User Data\SingletonLock" >nul 2>&1

echo [3/3] 正在以调试模式启动 Chrome...
:: 启动至默认新标签页
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data" --profile-directory="Profile 4" --no-first-run --remote-allow-origins=* "chrome://newtab/"

echo.
echo ✅ 启动成功！如果您看到的是插件界面而不是 Google 搜索：
echo 请在插件设置中关闭 "New Tab override" 选项。
echo.
pause
