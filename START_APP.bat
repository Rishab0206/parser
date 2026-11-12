@echo off
title Bank Statement Intelligence Launcher
echo ========================================================
echo   Launching Bank Statement Intelligence (Port 3000 / 8000)
echo ========================================================

powershell -NoProfile -Command "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine = 'cmd.exe /c E:\bank-statement-intelligence\start_backend.bat'}; Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine = 'cmd.exe /c E:\bank-statement-intelligence\start_frontend.bat'}" >nul 2>&1

timeout /t 3 /nobreak >nul
start http://localhost:3000
echo Running! You can close this window.
exit
