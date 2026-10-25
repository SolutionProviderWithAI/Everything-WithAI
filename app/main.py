"""
Compatibility layer for Render and cloud environments configured to run:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import the FastAPI application instance from the root main.py
from main import app, portfolio_data

__all__ = ["app", "portfolio_data"]
