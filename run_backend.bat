@echo off
echo ========================================================
echo Starting StudyMind AI - Backend Server (FastAPI / RAG)
echo ========================================================
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
