@echo off
cd /d d:\ai_Agentic_Compliance\backend
D:\Users\14078\Miniconda3\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
