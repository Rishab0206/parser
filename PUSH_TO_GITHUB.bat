@echo off
title Push to GitHub
cd /d "E:\bank-statement-intelligence-github"
echo ========================================================
echo   Pushing Bank Statement Intelligence to GitHub
echo   Repository: https://github.com/Rishab0206/parser
echo ========================================================
echo.
git push -u origin main
echo.
echo ========================================================
echo   Done! Press any key to close.
echo ========================================================
pause >nul
