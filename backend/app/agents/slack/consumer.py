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
        
        # Return combined results
        return {
            "status": "success",
            "consumer_result": consumer_result,
            "analysis_result": analysis_result
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

# Test code
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "content": "URGENT: We need to update the dashboard project for Acme Inc. Please contact john.doe@example.com for more details.",
        "channel": "dashboard-team",
        "username": "user123",
        "email": "sender@example.com",
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