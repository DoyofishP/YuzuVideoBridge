@echo off
setlocal EnableExtensions DisableDelayedExpansion
title YuzuVideoBridge - Git Commit and Push

set "REPO=F:\YuzuVideoBridge"
cd /d "%REPO%"
if errorlevel 1 (
    echo ERROR: Cannot enter repository: "%REPO%"
    pause
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo ERROR: This folder is not a Git repository.
    pause
    exit /b 1
)

echo ==============================================
echo    Repository: %REPO%
echo ==============================================
echo.
git status --short
echo.
choice /C YN /M "Stage ALL changes shown above and push"
if errorlevel 2 (
    echo Cancelled.
    exit /b 0
)

echo.
set "MSG="
set /p "MSG=Commit message (Enter for default): "
if not defined MSG set "MSG=Update YuzuVideoBridge"

git add -A
if errorlevel 1 (
    echo ERROR: git add failed.
    pause
    exit /b 1
)

git diff --cached --quiet
if errorlevel 1 (
    git commit -m "%MSG%"
    if errorlevel 1 (
        echo ERROR: git commit failed.
        pause
        exit /b 1
    )
) else (
    echo No new changes to commit. Trying to push existing commits.
)

git push
if errorlevel 1 (
    echo ERROR: git push failed.
    pause
    exit /b 1
)

echo.
echo SUCCESS. Git push completed.
pause
