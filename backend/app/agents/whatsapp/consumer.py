import os
import sys
from typing import Dict, Any, List, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.whatsapp.consumer_agent import WhatsAppConsumer
from app.agents.whatsapp.analyser_agent import WhatsAppAnalyzer
from app.agents.whatsapp.analyser_agent import notify_message

# Initialize Celery app
celery_app = Celery('whatsapp_processing', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

@celery_app.task(name="whatsapp.process_message")
def process_message(
    user_id: str, 
    message_data: Dict[str, Any],
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6,
    notification_callback = notify_message
) -> Dict[str, Any]:
    """
    Process a WhatsApp message from start to finish: extract identifiers and analyze.
    
    Args:
        user_id: The ID of the user
        message_data: WhatsApp message data including content, phone number, etc.
        spam_threshold: Threshold for spam detection (0-1)
        urgent_threshold: Threshold for urgency detection (0-1)
        important_threshold: Threshold for importance detection (0-1)
        notification_callback: Callback function for message notifications
        
    Returns:
        A dictionary with the combined results of processing and analysis
    """
    try:
        # Step 1: Extract identifiers using the WhatsAppConsumer
        consumer = WhatsAppConsumer()
        consumer_result = consumer.process_message(user_id, message_data)
        
        if consumer_result.get("status") != "success":
            return consumer_result
        
        identifiers = consumer_result.get("identifiers", [])
        message_id = consumer_result.get("message_id")
        
        # Step 2: Analyze the message with the extracted identifiers
        analyzer = WhatsAppAnalyzer(
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

@celery_app.task(name="whatsapp.process_contact")
def process_contact(
    user_id: str,
    contact_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a WhatsApp contact save operation.
    
    Args:
        user_id: The ID of the user
        contact_data: Contact data including name and phone number
        
    Returns:
        A dictionary with the result of processing
    """
    try:
        # Get database connection
        db = get_user_db(user_id)
        
        # Extract data
        name = contact_data.get("name")
        phone_number = contact_data.get("phone_number")
        
        # Create contact document in database
        contact_collection = db.collection("whatsapp_contacts")
        contact_doc = {
            "name": name,
            "phone_number": phone_number,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        
        # Check if contact already exists
        existing_contact = contact_collection.find({"phone_number": phone_number, "user_id": user_id})
        if existing_contact:
            # Update existing contact
            contact_collection.update({"_id": existing_contact[0]["_id"]}, contact_doc)
            contact_id = existing_contact[0]["_id"]
        else:
            # Create new contact
            contact_meta = contact_collection.insert(contact_doc)
            contact_id = contact_meta["_id"]
        
        return {
            "status": "success",
            "contact_id": contact_id,
            "message": f"Contact {name} saved successfully"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@celery_app.task(name="whatsapp.process_group_action")
def process_group_action(
    user_id: str,
    group_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process WhatsApp group actions (create, leave, add members, remove members).
    
    Args:
        user_id: The ID of the user
        group_data: Group action data
        
    Returns:
        A dictionary with the result of processing
    """
    try:
        # Get database connection
        db = get_user_db(user_id)
        
        # Extract data
        action = group_data.get("action")
        group_name = group_data.get("group_name")
        participants = group_data.get("participants", [])
        
        # Get group collection
        group_collection = db.collection("whatsapp_groups")
        
        # Process based on action type
        if action == "create_group":
            # Create new group document
            group_doc = {
                "name": group_name,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "created_by": user_id,
                "participants": participants,
                "active": True
            }
            
            group_meta = group_collection.insert(group_doc)
            group_id = group_meta["_id"]
            
            # Create edges between participants and group
            graph = db.graph("private_graph")
            for participant in participants:
                # Check if contact exists, create if not
                contact_collection = db.collection("whatsapp_contacts")
                existing_contact = contact_collection.find({"phone_number": participant, "user_id": user_id})
                
                if not existing_contact:
                    contact_doc = {
                        "phone_number": participant,
                        "name": participant,  # Use phone number as name if not available
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "user_id": user_id
                    }
                    contact_meta = contact_collection.insert(contact_doc)
                    contact_id = contact_meta["_id"]
                else:
                    contact_id = existing_contact[0]["_id"]
                
                # Create edge
                edge_collection = graph.edge_collection("whatsapp_member_of")
                edge_collection.insert({
                    "_from": f"whatsapp_contacts/{contact_id}",
                    "_to": f"whatsapp_groups/{group_id}",
                    "added_at": datetime.datetime.utcnow().isoformat(),
                    "added_by": user_id
                })
            
            return {
                "status": "success",
                "group_id": group_id,
                "message": f"Group {group_name} created successfully with {len(participants)} participants"
            }
            
        elif action == "leave_group":
            # Find the group
            group = group_collection.find({"name": group_name, "active": True})
            if not group:
                return {
                    "status": "error",
                    "error": f"Group {group_name} not found or inactive"
                }
            
            group_id = group[0]["_id"]
            
            # Update group document to mark current user as left
            graph = db.graph("private_graph")
            edge_collection = graph.edge_collection("whatsapp_member_of")
            
            # Find user's contact ID
            contact_collection = db.collection("whatsapp_contacts")
            user_contacts = contact_collection.find({"user_id": user_id})
            
            if user_contacts:
                for contact in user_contacts:
                    contact_id = contact["_id"]
                    # Find and remove edge
                    edges = edge_collection.find({
                        "_from": f"whatsapp_contacts/{contact_id}",
                        "_to": f"whatsapp_groups/{group_id}"
                    })
                    
                    for edge in edges:
                        edge_collection.delete(edge["_id"])
            
            return {
                "status": "success",
                "group_id": group_id,
                "message": f"Left group {group_name} successfully"
            }
            
        elif action == "add_to_group":
            # Find the group
            group = group_collection.find({"name": group_name, "active": True})
            if not group:
                return {
                    "status": "error",
                    "error": f"Group {group_name} not found or inactive"
                }
            
            group_id = group[0]["_id"]
            
            # Add participants to group
            graph = db.graph("private_graph")
            edge_collection = graph.edge_collection("whatsapp_member_of")
            contact_collection = db.collection("whatsapp_contacts")
            
            added_participants = []
            for participant in participants:
                # Check if contact exists, create if not
                existing_contact = contact_collection.find({"phone_number": participant, "user_id": user_id})
                
                if not existing_contact:
                    contact_doc = {
                        "phone_number": participant,
                        "name": participant,  # Use phone number as name if not available
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "user_id": user_id
                    }
                    contact_meta = contact_collection.insert(contact_doc)
                    contact_id = contact_meta["_id"]
                else:
                    contact_id = existing_contact[0]["_id"]
                
                # Check if already in group
                existing_edge = edge_collection.find({
                    "_from": f"whatsapp_contacts/{contact_id}",
                    "_to": f"whatsapp_groups/{group_id}"
                })
                
                if not existing_edge:
                    # Create edge
                    edge_collection.insert({
                        "_from": f"whatsapp_contacts/{contact_id}",
                        "_to": f"whatsapp_groups/{group_id}",
                        "added_at": datetime.datetime.utcnow().isoformat(),
                        "added_by": user_id
                    })
                    added_participants.append(participant)
            
            return {
                "status": "success",
                "group_id": group_id,
                "added_participants": added_participants,
                "message": f"Added {len(added_participants)} participants to group {group_name} successfully"
            }
            
        elif action == "remove_from_group":
            # Find the group
            group = group_collection.find({"name": group_name, "active": True})
            if not group:
                return {
                    "status": "error",
                    "error": f"Group {group_name} not found or inactive"
                }
            
            group_id = group[0]["_id"]
            
            # Remove participants from group
            graph = db.graph("private_graph")
            edge_collection = graph.edge_collection("whatsapp_member_of")
            contact_collection = db.collection("whatsapp_contacts")
            
            removed_participants = []
            for participant in participants:
                # Find contact
                existing_contact = contact_collection.find({"phone_number": participant, "user_id": user_id})
                
                if existing_contact:
                    contact_id = existing_contact[0]["_id"]
                    
                    # Find and remove edge
                    edges = edge_collection.find({
                        "_from": f"whatsapp_contacts/{contact_id}",
                        "_to": f"whatsapp_groups/{group_id}"
                    })
                    
                    for edge in edges:
                        edge_collection.delete(edge["_id"])
                        removed_participants.append(participant)
            
            return {
                "status": "success",
                "group_id": group_id,
                "removed_participants": removed_participants,
                "message": f"Removed {len(removed_participants)} participants from group {group_name} successfully"
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
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "from": "14155552671",
        "to": "dashboard-team-group",
        "is_group": True
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