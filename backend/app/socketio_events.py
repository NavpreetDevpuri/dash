from flask_socketio import emit
from flask import request
from app.models import ChatMessage
from datetime import datetime
from flask_login import current_user

def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print(f"Client connected: {request.sid}")

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f"Client disconnected: {request.sid}")

    @socketio.on('send_message')
    def handle_send_message(data):
        message = data.get('message')
        message_type = data.get('type', 'text')
        thread_id = data.get('thread_id', None)  # Expect a thread_id if sent

        if current_user.is_authenticated:
            ChatMessage.create(
                thread_id=thread_id,
                user_id=current_user.id,
                message_type=message_type,
                content=message,
                timestamp=datetime.utcnow().isoformat()
            )

        echo_data = {
            'message': message,
            'type': message_type,
            'thread_id': thread_id,
            'data': {}
        }
        # Emit the message to all other clients (skip the sender)
        socketio.emit('receive_message', echo_data, skip_sid=request.sid)