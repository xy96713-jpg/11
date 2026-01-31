@echo off
echo ========================================================
echo   NotebookLM CLI Launcher (NotebookLM 瀵归綈鐗?
echo   [!] 宸插惎鐢ㄥ己鍒朵唬鐞?Mode: 127.0.0.1:7897
echo ========================================================
echo.

set "PATH=%PATH%;C:\Users\Administrator\AppData\Roaming\Python\Python312\Scripts"

:: [AUTO-PROXY] 寮哄埗鎸囧畾浠ｇ悊浠ョ粫杩?Google 鍖哄煙閿?
set HTTPS_PROXY=http://127.0.0.1:7897
set HTTP_PROXY=http://127.0.0.1:7897
set ALL_PROXY=http://127.0.0.1:7897

if "%1"=="" (
    echo [用法]
    echo   1. 鐧诲綍: %0 login
    echo   2. 鍒涘缓: %0 create "My Notebook"
    echo   3. 甯姪: %0 --help
    echo.
    echo 姝ｅ湪灏濊瘯鏄剧ず甯姪...
    notebooklm --help
) else (
    echo 姝ｅ湪鎵ц: notebooklm %* ...
    notebooklm %*
)

echo.
if "%1"=="login" (
    echo [娉ㄦ剰] 鐧诲綍瀹屾垚鍚庯紝璇风瓑寰呮湰绐楀彛鎻愮ず "Success" 鎴栬嚜鍔ㄧ粨 鏉熴€?
    echo       鍒囧嫁鍦ㄧ綉椤靛脊鍑哄悗鐩存帴鍏抽棴鏈獥鍙?
)
pause
