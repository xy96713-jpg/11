@echo off
echo [*] Subtitle Lab 2.0 - DJ Edition Setup
echo [*] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [*] Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] WARNING: FFmpeg not found! Please install FFmpeg and add it to your PATH.
    echo [!] Demucs and Whisper REQUIRE FFmpeg to function.
) else (
    echo [+] FFmpeg detected.
)

echo.
echo [+] Setup Complete. You can now run lyric_engine.py or open ui/index.html.
pause
