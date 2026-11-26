@echo off
title Push to GitHub - Banking Parser
cd /d "%~dp0"
echo ========================================================
echo   Push to GitHub - Banking Parser (Active Render Profile)
echo ========================================================
echo.
echo Current Remote:
git remote -v
echo.
echo [1] Push to current remote repository (Rishab0206/parser)
echo [2] Change to a NEW repository (e.g. https://github.com/Rishab0206/banking-parser.git) and push
echo.
set /p choice="Enter choice (1 or 2, default is 1): "

if "%choice%"=="2" (
    echo.
    set /p newrepo="Enter your new GitHub repository URL: "
    if not "%newrepo%"=="" (
        git remote remove origin
        git remote add origin %newrepo%
        echo Remote origin updated to: %newrepo%
    )
)

echo.
echo Staging all changes...
git add .
git commit -m "feat: active render profile banking-parser (multi-stage docker, procfile, render.yaml)"
echo.
echo Pushing to GitHub main branch...
git branch -M main
git push -u origin main

echo.
echo ========================================================
echo   Push Complete!
echo   Next Step on Render.com:
echo   1. Create New Web Service / Blueprint
echo   2. Select 'banking-parser'
echo ========================================================
pause
