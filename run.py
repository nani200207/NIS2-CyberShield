import os
import sys
import subprocess
import time
import webbrowser

# Reconfigure standard output encoding to UTF-8 to prevent Windows terminal CP1252 exceptions on emojis
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Beautiful Terminal Banner
BANNER = """
========================================================================
    🛡️  NIS2 CYBERSHIELD COMPLIANCE PLATFORM & AI ADVISOR  🛡️
========================================================================
  [+] Automatically scans IT environments
  [+] Maps assets to Swedish NIS2 scope criteria
  [+] Runs Article 21 Custom Gaps Evaluator
  [+] Integrates LangChain AI Remediation Chat
  [+] Compiles Audit PDFs for Swedish MSB / NCSC-SE
========================================================================
"""

REQUIRED_PACKAGES = [
    "fastapi", "uvicorn", "sqlalchemy", "jinja2", "reportlab",
    "python-dotenv", "google-generativeai", "requests", "pydantic", "apscheduler"
]

def check_and_install_dependencies():
    print("[*] Verifying local Python environment requirements...")
    missing = []
    
    for pkg in REQUIRED_PACKAGES:
        try:
            if pkg == "google-generativeai":
                import google.generativeai
            elif pkg == "python-dotenv":
                import dotenv
            elif pkg == "pydantic-settings":
                import pydantic_settings
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)
            
    if missing:
        print(f"[!] Missing required packages: {missing}")
        print("[*] Executing automated dependency installation...")
        try:
            # We install using requirements.txt or direct packages
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("[+] Dependency installations completed successfully!")
        except Exception as e:
            print(f"[ERROR] Failed to run pip installation: {str(e)}")
            print("[*] Trying direct package installations...")
            for pkg in missing:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                except Exception as ex:
                    print(f"[ERROR] Could not install {pkg}: {str(ex)}")
    else:
        print("[+] Environment check successful! All packages are fully satisfied.")

def main():
    print(BANNER)
    
    # 1. Align imports and verify workspace requirements
    check_and_install_dependencies()
    
    print("\n[*] Starting NIS2 CyberShield Platform Daemon...")
    print("[*] Dashboard UI address: http://localhost:8000")
    print("[*] API Documentation:   http://localhost:8000/docs")
    print("[*] Press Ctrl+C to terminate the platform at any time.\n")
    
    # 2. Try auto-opening dashboard in default browser
    try:
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")
    except Exception as e:
        print(f"[!] Could not open default web browser: {str(e)}")
        
    # 3. Spin up Uvicorn FastAPI
    try:
        import uvicorn
        # Execute backend uvicorn server in current python runtime
        uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
    except KeyboardInterrupt:
        print("\n[-] Shutdown request received. CyberShield platform terminated successfully.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to execute FastAPI daemon server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
