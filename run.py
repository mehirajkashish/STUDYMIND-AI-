import subprocess
import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(current_dir, "backend")):
    root_dir = current_dir
elif os.path.exists(os.path.join(current_dir, "..", "backend")):
    root_dir = os.path.abspath(os.path.join(current_dir, ".."))
else:
    root_dir = current_dir

backend_dir = os.path.join(root_dir, "backend")
frontend_dir = os.path.join(root_dir, "frontend")

print("=" * 64)
print("  StudyMind AI – Production RAG Study Assistant (v2.0)")
print("=" * 64)

# 1. Start FastAPI Backend
print("[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
backend_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
    cwd=backend_dir
)

time.sleep(1)

# 2. Start Vite Frontend
print("[2/2] Starting React Vite Frontend on http://localhost:5173 ...")
npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
frontend_proc = subprocess.Popen(
    [npm_cmd, "run", "dev"],
    cwd=frontend_dir
)

print("=" * 64)
print("  Application running!")
print("  Backend API:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)")
print("  Frontend Web: http://localhost:5173")
print("  Press Ctrl+C to stop both servers.")
print("=" * 64)

try:
    while True:
        time.sleep(1)
        if backend_proc.poll() is not None:
            print("\n[Warning] Backend process exited unexpectedly.")
            break
        if frontend_proc.poll() is not None:
            print("\n[Warning] Frontend process exited unexpectedly.")
            break
except KeyboardInterrupt:
    print("\nStopping StudyMind AI servers...")
finally:
    try:
        backend_proc.terminate()
        backend_proc.wait(timeout=2)
    except Exception:
        pass
    try:
        frontend_proc.terminate()
        frontend_proc.wait(timeout=2)
    except Exception:
        pass
    print("All servers stopped.")
