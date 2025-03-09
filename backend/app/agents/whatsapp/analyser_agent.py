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
from app.agents.whatsapp.schemas import AnalysisResult

# Initialize Celery app
celery_app = Celery('whatsapp_analyzer', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection names
WHATSAPP_MESSAGES_COLLECTION = "whatsapp_messages"
ANALYZER_IDENTIFIERS_COLLECTION = "analyzer_identifiers"
WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION = "whatsapp_message_analysis"

class WhatsAppAnalyzer(BaseGraphConsumer):
    """
    A service that analyzes WhatsApp messages for spam, urgency, and importance,
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
        Initialize the WhatsAppAnalyzer.
        
        Args:
            model_provider: The LLM provider to use (openai, anthropic, gemini)
            model_name: The model name to use
            temperature: The temperature for the model
            spam_threshold: Threshold for spam detection (0-1)
            urgent_threshold: Threshold for urgency detection (0-1)
            important_threshold: Threshold for importance detection (0-1)
            notification_callback: Optional callback function for when message is analyzed
        """
        super().__init__()
        self.llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(AnalysisResult)
        
        self.spam_threshold = spam_threshold
        self.urgent_threshold = urgent_threshold
        self.important_threshold = important_threshold
        self.notification_callback = notification_callback
    
    def analyze_message(self, message_content: str, identifiers: List[str]) -> AnalysisResult:
        """
        Use an LLM to analyze the message content for spam, urgency, and importance.
        
        Args:
            message_content: The content of the WhatsApp message
            identifiers: List of extracted identifiers from the message
            
        Returns:
            An AnalysisResult with spam, urgency, and importance scores
        """
        # Construct prompt for message analysis
        identifiers_text = ", ".join(identifiers) if identifiers else "None"
        prompt = f"""
        Analyze this WhatsApp message for the following factors:
        1. Spam likelihood (0.0 to 1.0): Is this message spam/scam or legitimate?
        2. Urgency (0.0 to 1.0): How time-sensitive or urgent is this message?
        3. Importance (0.0 to 1.0): How important is this message for the recipient?
        
        Message content: "{message_content}"
        
        Extracted identifiers: {identifiers_text}
        
        Respond with scores for each factor.
        """
        
        # Call the model
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        
        return response
    
    def _add_analysis_identifier(self, db, analysis_type: str, analysis_data: Dict[str, Any]) -> str:
        """
        Add an analysis identifier to the database.
        
        Args:
            db: Database connection
            analysis_type: The type of analysis (spam, urgent, important)
            analysis_data: The analysis data to store
            
        Returns:
            The ID of the inserted identifier
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(ANALYZER_IDENTIFIERS_COLLECTION):
            return None
            
        # Prepare document
        doc = {
            "type": analysis_type,
            "timestamp": str(datetime.datetime.utcnow())
        }
        
        # Add analysis data
        doc.update(analysis_data)
        
        # Insert document
        result = db.collection(ANALYZER_IDENTIFIERS_COLLECTION).insert(doc)
        return result["_id"]
    
    def _add_edge(self, db, from_id: str, to_id: str, collection_name: str, data: Dict[str, Any] = None) -> str:
        """
        Add an edge between two vertices.
        
        Args:
            db: Database connection
            from_id: The ID of the source vertex
            to_id: The ID of the target vertex
            collection_name: The name of the edge collection
            data: Additional edge data
            
        Returns:
            The ID of the inserted edge
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(collection_name):
            return None
        
        # Prepare edge document
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "created_at": str(datetime.datetime.utcnow())
        }
        
        # Add optional data if provided
        if data:
            edge_doc.update(data)
        
        # Insert edge
        result = db.collection(collection_name).insert(edge_doc)
        return result["_id"]
        
    def process_message(
        self,
        user_id: str,
        message_data: Dict[str, Any],
        identifiers: List[str],
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a WhatsApp message, analyze it, and store analysis in the database.
        
        Args:
            user_id: The ID of the user
            message_data: WhatsApp message data including content
            identifiers: List of identifiers extracted from the message
            message_id: Optional ID of an existing message to analyze
            
        Returns:
            A dictionary with the results of the analysis
        """
        # Get message content from data
        message_content = message_data.get("content", "")
        
        # Analyze the message
        analysis = self.analyze_message(message_content, identifiers)
        
        # Get database connection for the user
        db = get_user_db(user_id)
        if not db:
            return {"error": "Failed to connect to database", "status": "failed"}
        
        try:
            # If no message_id provided, add the message
            if not message_id:
                message_id = self._add_whatsapp_message(db, message_data)
                
            # Process spam score
            spam_data = {
                "score": analysis.spam_score,
                "threshold": self.spam_threshold
            }
            
            # Process urgency score
            urgency_data = {
                "score": analysis.urgency_score,
                "threshold": self.urgent_threshold
            }
            
            # Process importance score
            importance_data = {
                "score": analysis.importance_score,
                "threshold": self.important_threshold
            }
            
            # Add analysis nodes and edges
            spam_id = self._add_analysis_identifier(db, "spam", spam_data)
            if spam_id and message_id:
                self._add_edge(db, spam_id, message_id, WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION, {"analysis_type": "spam"})
            
            urgency_id = self._add_analysis_identifier(db, "urgency", urgency_data)
            if urgency_id and message_id:
                self._add_edge(db, urgency_id, message_id, WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION, {"analysis_type": "urgency"})
            
            importance_id = self._add_analysis_identifier(db, "importance", importance_data)
            if importance_id and message_id:
                self._add_edge(db, importance_id, message_id, WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION, {"analysis_type": "importance"})
            
            # Prepare results
            analysis_result = {
                "spam": spam_data,
                "urgency": urgency_data,
                "importance": importance_data,
                "message_id": message_id
            }
            
            # Call notification callback if provided and message meets notification criteria
            should_notify = (
                self.notification_callback and 
                (analysis.urgency_score >= self.urgent_threshold or 
                 analysis.importance_score >= self.important_threshold) and
                analysis.spam_score < self.spam_threshold
            )
            
            if should_notify:
                self.notification_callback(user_id, message_data, analysis_result)
            
            return {
                "status": "success",
                "analysis": analysis_result
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _add_whatsapp_message(self, db, message_data: Dict[str, Any]) -> str:
        """
        Add a WhatsApp message to the database.
        
        Args:
            db: Database connection
            message_data: WhatsApp message data
            
        Returns:
            The ID of the inserted message
        """
        # Check if collection exists, if not it will be created by the migration
        if not db.has_collection(WHATSAPP_MESSAGES_COLLECTION):
            return None
        
        # Keep the original data structure but ensure required fields
        message_data_copy = message_data.copy()
        
        # Ensure created_at field
        if "created_at" not in message_data_copy:
            message_data_copy["created_at"] = str(datetime.datetime.utcnow())
            
        # Insert document
        result = db.collection(WHATSAPP_MESSAGES_COLLECTION).insert(message_data_copy)
        return result["_id"]


def notify_message(user_id: str, message_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Default notification function for WhatsApp message analysis.
    
    Args:
        user_id: The ID of the user
        message_data: WhatsApp message data
        analysis: Analysis results
    """
    # Build notification message
    notification = ["WhatsApp Message Analysis:"]
    
    # Add sender info
    sender = message_data.get("name", "Unknown contact")
    notification.append(f"From: {sender}")
    
    # Add urgency and importance info
    is_urgent = analysis["urgency"]["score"] >= analysis["urgency"]["threshold"]
    is_important = analysis["importance"]["score"] >= analysis["importance"]["threshold"]
    
    if is_urgent:
        notification.append("🔴 URGENT MESSAGE")
    
    if is_important:
        notification.append("⭐ IMPORTANT MESSAGE")
    
    # Add message preview
    content = message_data.get("content", "")
    preview = content[:100] + "..." if len(content) > 100 else content
    notification.append(f"Message: {preview}")
    
    # Add scores
    notification.append(f"Urgency score: {analysis['urgency']['score']:.2f}")
    notification.append(f"Importance score: {analysis['importance']['score']:.2f}")
    
    # Print notification (in production this would send to notification service)
    print("\n".join(notification))


# Celery task to analyze WhatsApp messages
@celery_app.task(name="whatsapp.analyze_message")
def analyze_whatsapp_message(
    user_id: str, 
    message_data: Dict[str, Any],
    identifiers: List[str],
    message_id: Optional[str] = None,
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Celery task to analyze a WhatsApp message.
    
    Args:
        user_id: The ID of the user
        message_data: WhatsApp message data
        identifiers: List of identifiers extracted from the message
        message_id: Optional ID of an existing message
        spam_threshold: Threshold for spam detection
        urgent_threshold: Threshold for urgency detection
        important_threshold: Threshold for importance detection
        
    Returns:
        A dictionary with the results of analysis
    """
    analyzer = WhatsAppAnalyzer(
        spam_threshold=spam_threshold,
        urgent_threshold=urgent_threshold,
        important_threshold=important_threshold,
        notification_callback=notify_message
    )
    
    return analyzer.process_message(
        user_id=user_id,
        message_data=message_data,
        identifiers=identifiers,
        message_id=message_id
    )


# Test code
if __name__ == "__main__":
    # Sample user ID and message data for testing
    test_user_id = "1270834"
    test_message = {
        "content": "URGENT: We need to update the dashboard project for Acme Inc by tomorrow. Please call me ASAP.",
        "group_id": "dashboard-team-group",
        "phone_number": "+14155552671",
        "name": "John Smith",
        "timestamp": str(datetime.datetime.utcnow())
    }
    
    # Sample identifiers
    test_identifiers = ["urgent", "dashboard project", "acme inc", "tomorrow", "asap"]
    
    # Call directly for testing
    result = analyze_whatsapp_message(
        test_user_id, 
        test_message,
        test_identifiers,
        spam_threshold=0.4,  # Lower spam threshold for testing
        urgent_threshold=0.6,  # Lower urgency threshold for testing
        important_threshold=0.6
    )
    
    print("Analysis result:")
    print(result) 