from flask_socketio import emit, join_room, leave_room
from flask import request, current_app
from app.models import ChatMessage
from datetime import datetime
from flask_login import current_user
import time
import threading
import uuid

# Import the GatewayAgent
from backend.app.agents.main_langgraph_experiment import GatewayAgent

# Global variable to hold the agent instance
gateway_agent = None

def get_gateway_agent():
    """Get or create the GatewayAgent singleton"""
    global gateway_agent
    if gateway_agent is None:
        import os
        gateway_agent = GatewayAgent(
            model_name=os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            debug=bool(os.environ.get('DEBUG', False))
        )
    return gateway_agent

def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print(f"Client connected: {request.sid}")
        
        # If the user is authenticated, join a room with their user ID
        if current_user.is_authenticated:
            join_room(str(current_user.id))
            print(f"User {current_user.id} joined their room")

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f"Client disconnected: {request.sid}")
        
        # If the user is authenticated, leave their room
        if current_user.is_authenticated:
            leave_room(str(current_user.id))
            print(f"User {current_user.id} left their room")

    @socketio.on('send_message')
    def handle_send_message(data):
        message = data.get('message')
        thread_id = data.get('thread_id', None)  # Expect a thread_id if sent

        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        if not message:
            emit('error', {'message': 'No message provided'})
            return
            
        if not thread_id:
            emit('error', {'message': 'No thread_id provided'})
            return
        
        try:
            # Save the user message to database
            user_message = ChatMessage.create(
                thread_id=thread_id,
                sender_id=current_user.id,
                content=message,
                message_type='user'
            )
            
            # Emit the user message to all users in the thread
            emit('new_message', {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat(),
                'sender_id': user_message.sender_id,
                'thread_id': thread_id,
                'message_type': 'user'
            }, room=f"thread_{thread_id}")
            
            # Notify the client that we're starting to process
            thinking_message_id = f"thinking_{uuid.uuid4()}"
            emit('thinking_start', {
                'id': thinking_message_id,
                'content': 'Thinking...',
                'timestamp': datetime.utcnow().isoformat(),
                'thread_id': thread_id,
            }, room=f"thread_{thread_id}")
            
            # Process the message with the GatewayAgent
            # This happens in a separate process, responses will come via websocket events
            def process_with_agent():
                try:
                    agent = get_gateway_agent()
                    # This will trigger thinking updates via websocket
                    response_content = agent.process_message(message, thread_id, current_user.id)
                    
                    # Save the final response to the database
                    assistant_message = ChatMessage.create(
                        thread_id=thread_id,
                        sender_id=None,  # None indicates system/agent
                        content=response_content,
                        message_type='assistant'
                    )
                    
                    # Emit agent response through websocket
                    socketio.emit('agent_response', {
                        'id': assistant_message.id,
                        'content': response_content,
                        'timestamp': assistant_message.timestamp.isoformat(),
                        'thread_id': thread_id,
                        'message_type': 'assistant',
                        'sender_id': None  # None indicates system/agent
                    }, room=f"thread_{thread_id}")
                    
                except Exception as e:
                    current_app.logger.error(f"Error processing message with agent: {str(e)}")
                    # Send error message through websocket
                    socketio.emit('error', {
                        'message': f"Error processing your request: {str(e)}",
                        'thread_id': thread_id
                    }, room=f"thread_{thread_id}")
            
            # Start processing in a separate thread
            processing_thread = threading.Thread(target=process_with_agent)
            processing_thread.daemon = True
            processing_thread.start()
            
        except Exception as e:
            print(f"Error handling message: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('join_thread')
    def handle_join_thread(data):
        thread_id = data.get('thread_id')
        if not thread_id:
            emit('error', {'message': 'No thread_id provided'})
            return
        
        if current_user.is_authenticated:
            # Join the thread's room
            join_room(f"thread_{thread_id}")
            print(f"User {current_user.id} joined thread {thread_id}")
            
            # Notify other users in the thread that this user has joined
            emit('user_joined', {
                'user_id': str(current_user.id),
                'thread_id': thread_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"thread_{thread_id}", include_self=False)  # Don't send to the joining user
            
            # Confirm to the client that they have joined
            emit('joined_thread', {'thread_id': thread_id})
            
            # Fetch and send message history
            messages = ChatMessage.get_messages_for_thread(thread_id)
            if messages:
                emit('message_history', {
                    'thread_id': thread_id,
                    'messages': [
                        {
                            'id': msg.id,
                            'content': msg.content,
                            'timestamp': msg.timestamp.isoformat(),
                            'sender_id': msg.sender_id,
                            'message_type': msg.message_type,
                            'thread_id': msg.thread_id
                        }
                        for msg in messages
                    ]
                })
    
    @socketio.on('leave_thread')
    def handle_leave_thread(data):
        thread_id = data.get('thread_id')
        if not thread_id:
            emit('error', {'message': 'No thread_id provided'})
            return
        
        if current_user.is_authenticated:
            # Leave the thread's room
            leave_room(f"thread_{thread_id}")
            print(f"User {current_user.id} left thread {thread_id}")
            
            # Notify other users in the thread that this user has left
            emit('user_left', {
                'user_id': str(current_user.id),
                'thread_id': thread_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"thread_{thread_id}")  # Send to the remaining users in the room
            
            # Confirm to the client that they have left
            emit('left_thread', {'thread_id': thread_id})
    
    @socketio.on('typing_indicator')
    def handle_typing_indicator(data):
        thread_id = data.get('thread_id')
        is_typing = data.get('is_typing', False)
        
        if current_user.is_authenticated and thread_id:
            # Broadcast typing indicator to all users in the thread
            emit('user_typing', {
                'user_id': str(current_user.id),
                'thread_id': thread_id,
                'is_typing': is_typing,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"thread_{thread_id}", include_self=False)  # Don't send to the typing user
    
    def send_notification(user_id, message, channel_type='system', importance='normal'):
        """
        Send a notification to a specific user.
        
        Args:
            user_id: The ID of the user to notify
            message: The notification message
            channel_type: The type of channel that generated the notification
            importance: The importance level ("normal", "high", "low")
        """
        from datetime import datetime
        notification_data = {
            'message': message,
            'type': 'notification',
            'channel': channel_type,
            'importance': importance,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit to the user's room
        socketio.emit('notification', notification_data, room=str(user_id))
        
        print(f"Notification sent to user {user_id}: {message}")
    
    # Register additional events for real-time agent feedback
    @socketio.on('get_thinking_history')
    def handle_get_thinking_history(data):
        """Handle request for thinking history from a specific message"""
        thread_id = data.get('thread_id')
        message_id = data.get('message_id')
        
        if not thread_id or not message_id:
            emit('error', {'message': 'Missing thread_id or message_id'})
            return
            
        # This would normally fetch thinking history from a database
        # For now, we just return a placeholder
        # In a real implementation, you would store thinking history in your database
        thinking_history = [
            "Thinking history would be retrieved from database",
            "This is a placeholder for demonstration"
        ]
        
        emit('thinking_history', {
            'thread_id': thread_id,
            'message_id': message_id,
            'history': thinking_history,
            'timestamp': datetime.utcnow().isoformat()
        })