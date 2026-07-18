import sys
import os

# Add the backend directory to sys.path so that absolute imports (e.g., 'from app.core.config import settings')
# resolve correctly when Vercel runs this file as a serverless function.
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

# Import the FastAPI application instance
from app.main import app

# This is required by Vercel serverless python runtime
handler = app
