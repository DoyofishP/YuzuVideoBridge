@echo off
setlocal

echo ==========================
echo Git Add
echo ==========================
git add .

echo.
set /p msg=Commit Message: 

if "%msg%"=="" (
    echo.
    echo Commit message cannot be empty.
    pause
    exit /b 1
)

echo.
echo ==========================
echo Git Commit
echo ==========================
git commit -m "%msg%"

if errorlevel 1 (
    echo.
    echo Commit failed or nothing to commit.
    pause
    exit /b 1
)

echo.
echo ==========================
echo Git Push
echo ==========================
git push

if errorlevel 1 (
    echo.
    echo Push failed.
    pause
    exit /b 1
)

echo.
echo ==========================
echo Done.
echo ==========================
pause