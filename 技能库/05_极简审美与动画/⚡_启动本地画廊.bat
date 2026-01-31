@echo off
echo ========================================================
echo   Antigravity Visual Gallery - ULTRA Mode
echo   [!] 正在启动本地高清画廊预览...
echo ========================================================
echo.

set GALLERY_PATH="d:\网页动画\index.html"

if exist %GALLERY_PATH% (
    echo [√] 找到本地画廊资源。
    start chrome "file:///D:/网页动画/index.html#/"
    echo [√] 已在 Chrome 中打开：ULTRA Visuals 首页
) else (
    echo [×] 错误：未在 D:\网页动画 找到资源。
    echo 请确认该文件夹是否存在。
)

pause
