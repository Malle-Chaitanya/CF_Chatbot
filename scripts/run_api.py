"""
Run the RAG Search API (uvicorn) with PYTHONPATH set so backend/src is on the path.

Usage:
  From repo root:    python scripts/run_api.py
  From backend dir:   python ..\scripts\run_api.py
"""
import os
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_backend_src = _repo_root / "backend" / "src"
_backend_src_str = str(_backend_src)

if _backend_src_str not in os.environ.get("PYTHONPATH", "").split(os.pathsep):
    existing = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = _backend_src_str + (os.pathsep + existing if existing else "")

# Ensure current process can import too (for uvicorn run before reload spawn)
if _backend_src_str not in sys.path:
    sys.path.insert(0, _backend_src_str)

# Run uvicorn with api.main:app (module path relative to backend/src)
import uvicorn

if __name__ == "__main__":
    # app is api.main:app so that backend/src is the root (api.main -> backend/src/api/main.py)
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(_repo_root / "backend")],
    )
