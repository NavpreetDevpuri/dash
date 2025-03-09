import os
import sys
from typing import Dict, Any, List, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.slack.consumer_agent import SlackConsumer
from app.agents.slack.analyser_agent import SlackAnalyzer
from app.agents.slack.analyser_agent import notify_message

# Initialize Celery app
celery_app = Celery('slack_processing', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

@celery_app.task(name="slack.process_message")
def process_message(
    user_id: str, 
    message_data: Dict[str, Any],
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6,
    notification_callback = notify_message
) -> Dict[str, Any]:
    """
    Process a Slack message from start to finish: extract identifiers and analyze.
    
    Args:
        user_id: The ID of the user
        message_data: Slack message data including content, channel, etc.
        spam_threshold: Threshold for spam detection (0-1)
        urgent_threshold: Threshold for urgency detection (0-1)
        important_threshold: Threshold for importance detection (0-1)
        notification_callback: Callback function for message notifications
        
    Returns:
        A dictionary with the combined results of processing and analysis
    """
    try:
        # Step 1: Extract identifiers using the SlackConsumer
        consumer = SlackConsumer()
        consumer_result = consumer.process_message(user_id, message_data)
        
        if consumer_result.get("status") != "success":
            return consumer_result
        
        identifiers = consumer_result.get("identifiers", [])
        message_id = consumer_result.get("message_id")
        
        # Step 2: Analyze the message with the extracted identifiers
        analyzer = SlackAnalyzer(
            spam_threshold=spam_threshold,
            urgent_threshold=urgent_threshold,
            important_threshold=important_threshold,
            notification_callback=notification_callback
        )
        
        analysis_result = analyzer.process_message(
            user_id=user_id, 
            message_data=message_data, 
            identifiers=identifiers,
            message_id=message_id
        )
        
        # Combine results
        result = {
            "status": "success",
            "message_id": message_id,
            "identifiers": identifiers,
            "analysis": analysis_result
        }
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@celery_app.task(name="slack.process_channel_action")
def process_channel_action(
    user_id: str,
    channel_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process Slack channel actions (create, leave, add members, remove members, set topic).
    
    Args:
        user_id: The ID of the user
        channel_data: Channel action data
        
    Returns:
        A dictionary with the result of processing
    """
    try:
        # Get database connection
        db = get_user_db(user_id)
        
        # Extract data
        action = channel_data.get("action")
        channel_name = channel_data.get("channel_name")
        members = channel_data.get("members", [])
        topic = channel_data.get("topic", "")
        
        # Get channel collection
        channel_collection = db.collection("slack_channels")
        
        # Process based on action type
        if action == "create_channel":
            # Create new channel document
            channel_doc = {
                "name": channel_name,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "created_by": user_id,
                "members": members,
                "topic": "",
                "active": True
            }
            
            channel_meta = channel_collection.insert(channel_doc)
            channel_id = channel_meta["_id"]
            
            # Create edges between members and channel
            graph = db.graph("private_graph")
            for member in members:
                # Check if user exists, create if not
                user_collection = db.collection("slack_users")
                existing_user = user_collection.find({"username": member})
                
                if not existing_user:
                    # Create basic user document
                    user_doc = {
                        "username": member,
                        "email": f"{member}@example.com",  # Placeholder email
                        "created_at": datetime.datetime.utcnow().isoformat()
                    }
                    user_meta = user_collection.insert(user_doc)
                    user_id = user_meta["_id"]
                else:
                    user_id = existing_user[0]["_id"]
                
                # Create edge
                edge_collection = graph.edge_collection("slack_member_of")
                edge_collection.insert({
                    "_from": f"slack_users/{user_id}",
                    "_to": f"slack_channels/{channel_id}",
                    "added_at": datetime.datetime.utcnow().isoformat(),
                    "added_by": user_id
                })
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "message": f"Channel {channel_name} created successfully with {len(members)} members"
            }
            
        elif action == "leave_channel":
            # Find the channel
            channel = channel_collection.find({"name": channel_name, "active": True})
            if not channel:
                return {
                    "status": "error",
                    "error": f"Channel {channel_name} not found or inactive"
                }
            
            channel_id = channel[0]["_id"]
            
            # Update channel document to mark current user as left
            graph = db.graph("private_graph")
            edge_collection = graph.edge_collection("slack_member_of")
            
            # Find current user's ID
            user_collection = db.collection("slack_users")
            current_user = user_collection.find({"user_id": user_id})
            
            if current_user:
                # Remove edge connecting user to channel
                user_doc_id = current_user[0]["_id"]
                edges = edge_collection.find({
                    "_from": f"slack_users/{user_doc_id}",
                    "_to": f"slack_channels/{channel_id}"
                })
                
                for edge in edges:
                    edge_collection.delete(edge["_id"])
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "message": f"Left channel {channel_name} successfully"
            }
            
        elif action == "add_to_channel":
            # Find the channel
            channel = channel_collection.find({"name": channel_name, "active": True})
            if not channel:
                return {
                    "status": "error",
                    "error": f"Channel {channel_name} not found or inactive"
                }
            
            channel_id = channel[0]["_id"]
            
            # Add members to channel
            graph = db.graph("private_graph")
            edge_collection = graph.edge_collection("slack_member_of")
            user_collection = db.collection("slack_users")
            
            added_members = []
            for member in members:
                # Check if user exists, create if not
                existing_user = user_collection.find({"username": member})
                
                if not existing_user:
                    # Create basic user document
                    user_doc = {
                        "username": member,
                        "email": f"{member}@example.com",  # Placeholder email
                        "created_at": datetime.datetime.utcnow().isoformat()
                    }
                    user_meta = user_collection.insert(user_doc)
                    user_id = user_meta["_id"]
                else:
                    user_id = existing_user[0]["_id"]
                
                # Check if already in channel
                existing_edge = edge_collection.find({
                    "_from": f"slack_users/{user_id}",
                    "_to": f"slack_channels/{channel_id}"
                })
                
                if not existing_edge:
                    # Create edge
                    edge_collection.insert({
                        "_from": f"slack_users/{user_id}",
                        "_to": f"slack_channels/{channel_id}",
                        "added_at": datetime.datetime.utcnow().isoformat(),
                        "added_by": user_id
                    })
                    added_members.append(member)
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "added_members": added_members,
                "message": f"Added {len(added_members)} members to channel {channel_name} successfully"
            }
            
        elif action == "remove_from_channel":
            # Find the channel
            channel = channel_collection.find({"name": channel_name, "active": True})
            if not channel:
                return {
                    "status": "error",
                    "error": f"Channel {channel_name} not found or inactive"
                }
            
            channel_id = channel[0]["_id"]
            
            # Remove members from channel
            graph = db.graph("private_graph")
            edge_collection = graph.edge_collection("slack_member_of")
            user_collection = db.collection("slack_users")
            
            removed_members = []
            for member in members:
                # Find user
                existing_user = user_collection.find({"username": member})
                
                if existing_user:
                    user_id = existing_user[0]["_id"]
                    
                    # Find and remove edge
                    edges = edge_collection.find({
                        "_from": f"slack_users/{user_id}",
                        "_to": f"slack_channels/{channel_id}"
                    })
                    
                    for edge in edges:
                        edge_collection.delete(edge["_id"])
                        removed_members.append(member)
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "removed_members": removed_members,
                "message": f"Removed {len(removed_members)} members from channel {channel_name} successfully"
            }
            
        elif action == "set_channel_topic":
            # Find the channel
            channel = channel_collection.find({"name": channel_name, "active": True})
            if not channel:
                return {
                    "status": "error",
                    "error": f"Channel {channel_name} not found or inactive"
                }
            
            channel_id = channel[0]["_id"]
            
            # Update channel topic
            channel_collection.update(
                {"_id": channel_id},
                {"topic": topic}
            )
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "topic": topic,
                "message": f"Topic for channel {channel_name} set to: '{topic}'"
            }
            
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Test code
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "from": "john_doe",
        "to": "nav",
        "is_channel": False,
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for details.",
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    # Call directly for testing
    result = process_message(
        test_user_id, 
        test_message,
        spam_threshold=0.4,  # Lower spam threshold for testing
        urgent_threshold=0.6  # Lower urgency threshold for testing
    )
    print("\nFinal combined result:")
    print(result) 