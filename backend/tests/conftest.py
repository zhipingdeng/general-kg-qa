"""Shared test fixtures."""
import sys
import os

# Add backend/ to sys.path so `app.xxx` imports resolve
_backend_dir = os.path.join(os.path.dirname(__file__), "..")
if _backend_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_dir))
