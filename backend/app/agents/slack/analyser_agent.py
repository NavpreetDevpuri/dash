import os
import sys
from typing import List, Dict, Any, Optional, Callable
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.common.llm_manager import LLMManager
from app.common.base_consumer import BaseGraphConsumer
from app.agents.slack.schemas import AnalysisResult

# Initialize Celery app
celery_app = Celery('slack_analyzer', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Define edge definitions for analyzer graph
ANALYZER_EDGE_DEFINITIONS = [
    {
        "edge_collection": "message_analysis",
        "from_vertex_collections": ["analyzer_identifiers"],
        "to_vertex_collections": ["slack_messages"],
    }
]

# Define orphan collections
ANALYZER_ORPHAN_COLLECTIONS = ["analyzer_identifiers", "slack_messages"]

class SlackAnalyzer(BaseGraphConsumer):
    """
    A service that analyzes Slack messages for spam, urgency, and importance,
    and adds analysis nodes to the graph database.
    """
    def __init__(
        self, 
        model_provider: str = "openai", 
        model_name: str = "gpt-4o-mini", 
        temperature: float = 0,
        spam_threshold: float = 0.5,
        urgent_threshold: float = 0.7,
        important_threshold: float = 0.6,
        notification_callback: Optional[Callable[[str, Dict[str, Any], Dict[str, Any]], None]] = None
    ):
        """
        Initialize the SlackAnalyzer.
        
        Args:
            model_provider: The LLM provider to use (openai, anthropic, gemini)
            model_name: The model name to use
            temperature: The temperature for the model
            spam_threshold: Threshold for spam detection (0-1)
            urgent_threshold: Threshold for urgency detection (0-1)
            important_threshold: Threshold for importance detection (0-1)
            notification_callback: Callback function for all types of notifications
                                   (user_id, message_data, analysis)
        """
        super().__init__()
        self.llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(AnalysisResult)
        
        # Set thresholds
        self.spam_threshold = spam_threshold
        self.urgent_threshold = urgent_threshold
        self.important_threshold = important_threshold
        
        # Set notification callback
        self._notification_callback = notification_callback
    
    def analyze_message(self, message_content: str, identifiers: List[str]) -> AnalysisResult:
        """
        Analyze a message to determine if it's spam, urgent, or important.
        
        Args:
            message_content: The content of the Slack message
            identifiers: List of identifiers extracted from the message
            
        Returns:
            AnalysisResult with the analysis scores and reasons
        """
        # Construct prompt for analysis
        prompt = f"""
        Analyze this Slack message and determine if it appears to be spam, urgent, or important.
        
        Consider the message content and these extracted identifiers: {", ".join(identifiers)}
        
        Message:
        {message_content}
        
        Provide a detailed analysis of:
        1. Is this likely spam? (e.g., unsolicited advertising, phishing attempt)
        2. Is this urgent? (e.g., time-sensitive, requires immediate attention)
        3. Is this important? (e.g., from management, about critical projects)
        """
        
        # Call the LLM model
        return self.llm.invoke([{"role": "user", "content": prompt}])
    
    def _add_analysis_identifier(self, analysis_type: str) -> str:
        """
        Add an analysis identifier to the database.
        
        Args:
            analysis_type: Type of analysis (spam, urgent, important)
            
        Returns:
            The ID of the inserted identifier
        """
        return self.add_node(
            collection_name="analyzer_identifiers",
            data={
                "type": analysis_type,
                "created_at": str(datetime.datetime.utcnow())
            },
            unique_key="type",
            unique_value=analysis_type
        )
    
    def process_message(
        self,
        user_id: str,
        message_data: Dict[str, Any],
        identifiers: List[str],
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a Slack message, analyze it, and store the results in the database.
        
        Args:
            user_id: The ID of the user
            message_data: Slack message data including content, channel, etc.
            identifiers: List of identifiers extracted from the message
            message_id: Optional message ID if already created by consumer
            
        Returns:
            A dictionary with the results of the analysis
        """
        # Get database connection for the user and set up graph
        db = get_user_db(user_id)
        if not db:
            return {"error": "Failed to connect to database", "status": "failed"}
        
        # Set up graph using the provided database connection
        self.setup_graph(db, "slack_analysis", ANALYZER_EDGE_DEFINITIONS, ANALYZER_ORPHAN_COLLECTIONS)
        
        try:
            # Get message content
            message_content = message_data.get("content", "")
            
            # Analyze the message
            analysis = self.analyze_message(message_content, identifiers)
            
            # Use provided message_id or look it up if not provided
            if not message_id:
                # Check if message already exists (by timestamp)
                timestamp = message_data.get("timestamp")
                existing_message = None
                
                if timestamp:
                    query = """
                    FOR doc IN slack_messages
                    FILTER doc.timestamp == @timestamp
                    RETURN doc
                    """
                    cursor = self.db.aql.execute(query, bind_vars={"timestamp": timestamp})
                    if cursor.count() > 0:
                        existing_message = next(cursor)
                
                # If message doesn't exist, add it
                if not existing_message:
                    message_id = self._add_slack_message(message_data)
                else:
                    message_id = existing_message["_id"]
            
            # Add analysis identifiers and link to message
            analysis_ids = {}
            
            # Prepare analysis data for notifications
            analysis_data = {
                "is_spam": analysis.is_spam,
                "is_urgent": analysis.is_urgent,
                "is_important": analysis.is_important,
                "spam_score": analysis.spam_score,
                "urgency_score": analysis.urgency_score,
                "importance_score": analysis.importance_score,
                "reason": analysis.reason
            }
            
            # Add spam identifier if score is above threshold
            if analysis.spam_score > self.spam_threshold:
                spam_id = self._add_analysis_identifier("spam")
                self.add_edge(
                    edge_collection="message_analysis", 
                    from_id=spam_id, 
                    to_id=message_id,
                    data={
                        "score": analysis.spam_score,
                        "reason": analysis.reason,
                        "created_at": str(datetime.datetime.utcnow())
                    }
                )
                analysis_ids["spam"] = spam_id
            
            # Add urgent identifier if score is above threshold
            if analysis.urgency_score > self.urgent_threshold:
                urgent_id = self._add_analysis_identifier("urgent")
                self.add_edge(
                    edge_collection="message_analysis", 
                    from_id=urgent_id, 
                    to_id=message_id,
                    data={
                        "score": analysis.urgency_score,
                        "reason": analysis.reason,
                        "created_at": str(datetime.datetime.utcnow())
                    }
                )
                analysis_ids["urgent"] = urgent_id
            
            # Add important identifier if score is above threshold
            if analysis.importance_score > self.important_threshold:
                important_id = self._add_analysis_identifier("important")
                self.add_edge(
                    edge_collection="message_analysis", 
                    from_id=important_id, 
                    to_id=message_id,
                    data={
                        "score": analysis.importance_score,
                        "reason": analysis.reason,
                        "created_at": str(datetime.datetime.utcnow())
                    }
                )
                analysis_ids["important"] = important_id
            
            # Send a single notification with all analysis data if callback is set
            # and if any of the thresholds were exceeded
            if self._notification_callback and (
                analysis.spam_score > self.spam_threshold or
                analysis.urgency_score > self.urgent_threshold or
                analysis.importance_score > self.important_threshold
            ):
                self._notification_callback(user_id, message_data, analysis_data)
            
            return {
                "status": "success",
                "message_id": message_id,
                "analysis": analysis_data,
                "analysis_ids": analysis_ids
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _add_slack_message(self, message_data: Dict[str, Any]) -> str:
        """
        Add a Slack message to the database.
        
        Args:
            message_data: Slack message data
            
        Returns:
            The ID of the inserted message
        """
        # Keep the original data structure but ensure required fields
        message_data_copy = message_data.copy()
        
        # Ensure created_at field
        if "created_at" not in message_data_copy:
            message_data_copy["created_at"] = str(datetime.datetime.utcnow())
            
        return self.add_node(
            collection_name="slack_messages",
            data=message_data_copy
        )

# Combined notification function with LLM for concise messaging
def notify_message(user_id: str, message_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Send a combined notification about a message based on analysis results.
    Uses an LLM to generate a concise, user-friendly notification.
    
    Args:
        user_id: User ID
        message_data: Message data
        analysis: Analysis results (is_spam, is_urgent, is_important, etc.)
    """
    channel = message_data.get("channel", "unknown")
    content = message_data.get("content", "")
    content_preview = content[:50] + "..." if len(content) > 50 else content
    
    # Determine what kinds of attributes the message has
    attributes = []
    if analysis.get("is_spam") and analysis.get("spam_score", 0) > 0.5:
        attributes.append(f"spam (score: {analysis.get('spam_score', 0):.2f})")
    
    if analysis.get("is_urgent") and analysis.get("urgency_score", 0) > 0.7:
        attributes.append(f"urgent (score: {analysis.get('urgency_score', 0):.2f})")
    
    if analysis.get("is_important") and analysis.get("importance_score", 0) > 0.6:
        attributes.append(f"important (score: {analysis.get('importance_score', 0):.2f})")
    
    if not attributes:
        return  # No notification needed
    
    # Use LLM to generate a concise notification
    try:
        llm = LLMManager.get_model(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0.3
        )
        
        prompt = f"""
        I need to notify a user about a message that has been analyzed. Please generate a CONCISE notification 
        that informs the user about this message in a helpful way.
        
        Message details:
        - Channel: {channel}
        - Content: {content}
        - Classification: {', '.join(attributes)}
        - Reason: {analysis.get('reason', 'No specific reason provided')}
        
        Guidelines for the notification:
        1. Be concise but informative (keep it under 2-3 sentences)
        2. Mention the specific issues detected (spam/urgent/important)
        3. Include channel name and a short preview of content
        4. Tone should be professional but conversational
        5. Avoid unnecessary words or explanations
        6. Do not include headers like "Notification" or "Message Analysis", keep it conversational message
        
        Your notification should be immediately actionable for the user.
        """
        
        response = llm.invoke([{"role": "user", "content": prompt}])
        notification_text = response.content
        
        # Print the LLM-generated notification
        print(f"\n=== NOTIFICATION FOR USER {user_id} ===")
        print(notification_text)
        print("=" * 40)
        
    except Exception as e:
        # Fallback to basic notification if LLM fails
        notification_type = " | ".join(attributes)
        print(f"[NOTIFICATION] User {user_id}: {notification_type} message in {channel}: {content_preview}")
        print(f"Reason: {analysis.get('reason', 'No reason provided')}")

# Test code for SlackAnalyzer
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "content": "URGENT: The server is down! We need to fix this ASAP or we'll lose client data!",
        "channel": "infra-alerts",
        "username": "sysadmin",
        "email": "admin@example.com",
        "timestamp": str(datetime.datetime.utcnow())
    }
    test_identifiers = ["urgent", "server", "client data"]
    
    # Create analyzer with custom thresholds and single callback
    analyzer = SlackAnalyzer(
        spam_threshold=0.4,
        urgent_threshold=0.6,
        important_threshold=0.5,
        notification_callback=notify_message
    )
    
    result = analyzer.process_message(test_user_id, test_message, test_identifiers)
    print(result)
