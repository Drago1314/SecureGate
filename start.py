import subprocess
import sys
import os
import webbrowser
import threading
import time

print("🔐 Apartment Visitor Security — Backend Starting...")
print("─────────────────────────────────────────────────")

# Install dependencies
print("📦 Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
print("✅ Dependencies installed!")
print("")
print("🚀 Server starting at http://localhost:8000")
print("📄 Swagger docs at http://localhost:8000/docs")
print("")
print("Press CTRL+C to stop")
print("─────────────────────────────────────────────────")

# Auto open browser after 2 seconds (server needs time to boot)
def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000/docs")

threading.Thread(target=open_browser, daemon=True).start()

# Start server
subprocess.call([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])
