import os
import sys
from typing import Dict, Any, List, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.email_agent.consumer_agent import EmailConsumer
from app.agents.email_agent.analyser_agent import EmailAnalyzer
from app.agents.email_agent.analyser_agent import notify_message

# Initialize Celery app
celery_app = Celery('email_processing', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

@celery_app.task(name="email.process_message")
def process_message(
    user_id: str, 
    email_data: Dict[str, Any],
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6,
    notification_callback = notify_message
) -> Dict[str, Any]:
    """
    Process an email message from start to finish: extract identifiers and analyze.
    
    Args:
        user_id: The ID of the user
        email_data: Email message data including content, metadata, etc.
        spam_threshold: Threshold for spam detection (0-1)
        urgent_threshold: Threshold for urgency detection (0-1)
        important_threshold: Threshold for importance detection (0-1)
        notification_callback: Callback function for email notifications
        
    Returns:
        A dictionary with the combined results of processing and analysis
    """
    try:
        # Step 1: Extract identifiers using the EmailConsumer
        consumer = EmailConsumer()
        consumer_result = consumer.process_message(user_id, email_data)
        
        if consumer_result.get("status") != "success":
            return consumer_result
        
        identifiers = consumer_result.get("identifiers", [])
        message_id = consumer_result.get("message_id")
        
        # Step 2: Analyze the message using the EmailAnalyzer
        analyzer = EmailAnalyzer(
            spam_threshold=spam_threshold,
            urgent_threshold=urgent_threshold,
            important_threshold=important_threshold,
            notification_callback=notification_callback
        )
        
        analysis_result = analyzer.process_message(
            user_id, 
            email_data,
            identifiers,
            message_id
        )
        
        # Step 3: Combine results
        combined_result = {
            "status": "success",
            "message_id": message_id,
            "identifiers": identifiers,
            "attachments": consumer_result.get("attachments", []),
            "analysis": {
                "spam_score": analysis_result.get("spam_score"),
                "urgency_score": analysis_result.get("urgency_score"),
                "importance_score": analysis_result.get("importance_score"),
                "category": analysis_result.get("category"),
                "categories": analysis_result.get("categories", []),
                "is_spam": analysis_result.get("is_spam", False),
                "is_urgent": analysis_result.get("is_urgent", False),
                "is_important": analysis_result.get("is_important", False),
                "reason": analysis_result.get("reason", ""),
                "summary": analysis_result.get("summary", "")
            }
        }
        
        return combined_result
    
    except Exception as e:
        print(f"Error processing email message: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="email.process_folder_action")
def process_folder_action(
    user_id: str,
    folder_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process an email folder action (create/update/delete).
    
    Args:
        user_id: The ID of the user
        folder_data: Email folder data
        
    Returns:
        A dictionary with the results of the folder action
    """
    try:
        from app.agents.email_agent.consumer_agent import process_email_folder_action
        return process_email_folder_action(user_id, folder_data)
    except Exception as e:
        print(f"Error processing folder action: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="email.process_batch")
def process_batch(
    user_id: str,
    email_batch: List[Dict[str, Any]],
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Process a batch of email messages.
    
    Args:
        user_id: The ID of the user
        email_batch: List of email messages to process
        spam_threshold: Threshold for spam detection (0-1)
        urgent_threshold: Threshold for urgency detection (0-1)
        important_threshold: Threshold for importance detection (0-1)
        
    Returns:
        A dictionary with the results of batch processing
    """
    results = []
    errors = []
    
    for email_data in email_batch:
        try:
            result = process_message(
                user_id,
                email_data,
                spam_threshold,
                urgent_threshold,
                important_threshold
            )
            
            if result.get("status") == "success":
                results.append(result)
            else:
                errors.append({
                    "email": email_data.get("subject", "Unknown"),
                    "error": result.get("message", "Unknown error")
                })
        except Exception as e:
            errors.append({
                "email": email_data.get("subject", "Unknown"),
                "error": str(e)
            })
    
    return {
        "status": "success" if len(errors) == 0 else "partial_success",
        "processed": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors
    }


@celery_app.task(name="email.sync_email_provider")
def sync_email_provider(
    user_id: str,
    provider_config: Dict[str, Any],
    max_emails: int = 100,
    sync_folders: bool = True,
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Sync emails from an email provider (like Gmail, Outlook, etc.)
    
    Args:
        user_id: The ID of the user
        provider_config: Configuration for the email provider
        max_emails: Maximum number of emails to sync
        sync_folders: Whether to sync folders as well
        spam_threshold: Threshold for spam detection (0-1)
        urgent_threshold: Threshold for urgency detection (0-1)
        important_threshold: Threshold for importance detection (0-1)
        
    Returns:
        A dictionary with the results of the sync operation
    """
    # Note: This is a placeholder for the actual implementation
    # In a real implementation, this would:
    # 1. Connect to the email provider API using the provider_config
    # 2. Fetch folders if sync_folders is True
    # 3. Fetch emails (up to max_emails)
    # 4. Process each email
    
    # Mock implementation for demonstration
    results = {
        "status": "success",
        "provider": provider_config.get("provider", "unknown"),
        "emails_synced": 0,
        "folders_synced": 0,
        "errors": []
    }
    
    try:
        # TODO: Implement the actual email provider sync logic
        # This would connect to Gmail, Outlook, etc. API
        # and fetch emails and folders
        
        # Mock data for demonstration
        if sync_folders:
            # Create standard folders
            standard_folders = [
                {"name": "INBOX", "type": "INBOX"},
                {"name": "Sent", "type": "SENT"},
                {"name": "Drafts", "type": "DRAFTS"},
                {"name": "Spam", "type": "SPAM"},
                {"name": "Trash", "type": "TRASH"},
                {"name": "Archive", "type": "ARCHIVE"}
            ]
            
            for folder_data in standard_folders:
                process_folder_action(user_id, {
                    "name": folder_data["name"],
                    "type": folder_data["type"],
                    "action": "create"
                })
                
            results["folders_synced"] = len(standard_folders)
        
        # Mock syncing some emails
        # In a real implementation, this would fetch from the email provider API
        
        return results
    
    except Exception as e:
        print(f"Error syncing email provider: {str(e)}")
        return {
            "status": "error",
            "provider": provider_config.get("provider", "unknown"),
            "message": str(e)
        }


if __name__ == "__main__":
    # Example usage
    test_user_id = "1270834"
    test_email = {
        "subject": "Meeting tomorrow",
        "body": "Let's discuss the project tomorrow at 10am. Please bring the latest reports.",
        "from": "john.doe@example.com",
        "to": ["jane.smith@example.com"],
        "date": datetime.datetime.now().isoformat(),
        "folder": "INBOX"
    }
    
    result = process_message(test_user_id, test_email)
    print(f"Result: {result}") 