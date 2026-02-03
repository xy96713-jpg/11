@echo off
chcp 65001 >nul
echo [1/3] 正在安全重启 Chrome (God Mode)...
taskkill /F /IM chrome.exe /IM GoogleCrashHandler.exe /IM GoogleUpdate.exe >nul 2>&1

echo [2/3] 启动您的原生 Chrome...
:: 不带 --user-data-dir，让 Chrome 自动加载您的默认登录配置
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
timeout /t 8 >nul

echo [3/3] 连接智能体到浏览器...
python "%~dp0scripts\douyin_note_taker.py" %* --cdp

echo Mission Complete.
pause
