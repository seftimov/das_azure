import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
workers = 1
worker_class = 'sync'
timeout = 120
keepalive = 2
