import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app

# Vercel butuh nama 'app' atau handler
handler = app