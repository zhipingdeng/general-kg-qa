"""Verify app creation and gunicorn config."""
import sys
import os

# Add project root to path (same as run.py)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
# Also add backend/ so gunicorn_conf can be imported
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Test 1: App creation
from backend.app.main import app
print(f"[OK] App created: {app.title} v{app.version}")

# Test 2: Routes registered
routes = [r.path for r in app.routes]
assert "/api/v1/health" in routes, "Missing /api/v1/health"
assert "/api/v1/auth/register" in routes, "Missing /api/v1/auth/register"
assert "/api/v1/auth/login" in routes, "Missing /api/v1/auth/login"
assert "/api/v1/auth/me" in routes, "Missing /api/v1/auth/me"
assert "/api/v1/qa" in routes, "Missing /api/v1/qa"
print(f"[OK] All routes registered: {routes}")

# Test 3: Gunicorn config
from gunicorn_conf import bind, workers, worker_class, timeout
print(f"[OK] Gunicorn config: workers={workers}, bind={bind}, worker_class={worker_class}, timeout={timeout}")

print("\nAll verifications passed!")
