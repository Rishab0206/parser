@echo off
cd /d "E:\bank-statement-intelligence\frontend"
cmd /c "npm run dev -- --host 0.0.0.0 --port 3000" > "E:\bank-statement-intelligence\frontend.log" 2>&1
