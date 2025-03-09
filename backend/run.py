from app import create_app, socketio
from config import Config
from flask_cors import CORS
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

# Set up a CORS handler for OPTIONS requests
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Use a different port to avoid AirPlay Receiver conflicts on macOS
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)