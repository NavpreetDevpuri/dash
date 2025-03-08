from app import create_app, socketio
from config import Config
import logging
import sys
import os
import traceback

# Configure simplified logging format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Reduce noise from Werkzeug
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Set Flask logging to show errors
logging.getLogger('flask').setLevel(logging.ERROR)

# Make sure unhandled exceptions are logged
def handle_exception(exc_type, exc_value, exc_traceback):
    """Log unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

app = create_app(Config)

if __name__ == '__main__':
    # Use a different port to avoid AirPlay Receiver conflicts on macOS
    port = int(os.environ.get('PORT', 5002))
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)