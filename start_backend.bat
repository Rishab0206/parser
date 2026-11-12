@echo off
cd /d "E:\bank-statement-intelligence\backend"
set PYTHONPATH=E:\bank-statement-intelligence\backend
C:\Python314\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "E:\bank-statement-intelligence\backend.log" 2>&1
