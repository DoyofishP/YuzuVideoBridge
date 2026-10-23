@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "REPO=F:\YuzuVideoBridge"
cd /d "%REPO%" || (
    echo [ERROR] Cannot open repository: %REPO%
    pause
    exit /b 1
)

:INPUT
echo.
echo Paste a Bilibili video URL, then press Enter:
set "VIDEO_URL="
set /p "VIDEO_URL=URL: "
if not defined VIDEO_URL (
    echo [ERROR] URL cannot be empty.
    goto INPUT
)

echo.
python ".\yuzu_bili_bridge.py" "%VIDEO_URL%" --repo "%REPO%" --asr
set "RESULT=%ERRORLEVEL%"

echo.
if "%RESULT%"=="0" (
    echo [OK] Processing finished.
) else (
    echo [ERROR] Processing failed. Exit code: %RESULT%
)
pause
exit /b %RESULT%
