"""Entry point: development (uvicorn) or production (gunicorn).

Run from the backend/ directory:
    python run.py          # dev mode with uvicorn + reload
    python run.py --prod   # production mode with gunicorn
"""
import sys
import os

# Add project root to sys.path so `backend.app.xxx` imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uvicorn


def main():
    if "--prod" in sys.argv:
        import subprocess
        subprocess.run([sys.executable, "-m", "gunicorn", "backend.app.main:app", "-c", "gunicorn_conf.py"])
    else:
        uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
