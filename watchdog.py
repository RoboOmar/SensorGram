import subprocess
import time
import sys
import datetime

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [WATCHDOG] {msg}")

def main():
    log("Watchdog started. Monitoring Uvicorn server...")
    while True:
        log("Spawning Uvicorn process...")
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "backend.main:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ])
        
        # Wait for the process to terminate
        process.wait()
        
        exit_code = process.returncode
        log(f"Uvicorn process terminated with exit code {exit_code}. Restarting in 2 seconds...")
        time.sleep(2)

if __name__ == "__main__":
    main()
