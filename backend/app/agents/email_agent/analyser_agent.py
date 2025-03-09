import os
import sys
from typing import List, Dict, Any, Optional, Callable
import datetime
import json
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.email_agent.schemas import AnalysisResult
from app.common.llm_manager import LLMManager
from app.common.base_consumer import BaseGraphConsumer
from app.agents.email_agent.tools import categorize_email

# Initialize Celery app
celery_app = Celery('email', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection and edge names
ANALYSIS_COLLECTION = "analysis"
EMAIL_MESSAGE_ANALYSIS_EDGE_COLLECTION = "email_message__analysis"  # Edge linking message to analysis

class EmailAnalyzer(BaseGraphConsumer):
    """
    A Celery consumer that analyzes email messages for spam, urgency, importance, and categorization.
    It reuses our graph nodes and adds extra analysis nodes.
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
        Initialize the EmailAnalyzer.
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
    
    def analyze_message(self, email_content: str, identifiers: List[str]) -> AnalysisResult:
        """
        Use an LLM to analyze an email for spam, urgency, importance, and categorization.
        
        Args:
            email_content: The text content of the email
            identifiers: List of identifiers extracted from the email
            
        Returns:
            Analysis results
        """
        # Import here to avoid circular imports
        from app.agents.email_agent.prompts import EMAIL_ANALYSIS_PROMPT
        
        # Create a prompt with the email content and identifiers
        prompt = EMAIL_ANALYSIS_PROMPT.format(
            email_content=email_content,
            identifiers=", ".join(identifiers) if identifiers else "No identifiers found"
        )
        
        # Process with LLM
        return self.llm.invoke(prompt)
    
    def _add_analysis(self, db, analysis_result: AnalysisResult) -> str:
        """
        Add an analysis document to the database.
        
        Args:
            db: The database instance
            analysis_result: Analysis results to store
            
        Returns:
            The analysis document ID
        """
        collection = db.collection(ANALYSIS_COLLECTION)
        
        # Create analysis document
        analysis_doc = {
            "spam_score": analysis_result.spam_score,
            "urgency_score": analysis_result.urgency_score,
            "importance_score": analysis_result.importance_score,
            "category": analysis_result.category,
            "reason": analysis_result.reason,
            "is_spam": analysis_result.spam_score >= self.spam_threshold,
            "is_urgent": analysis_result.urgency_score >= self.urgent_threshold,
            "is_important": analysis_result.importance_score >= self.important_threshold,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = collection.insert(analysis_doc)
        return f"{ANALYSIS_COLLECTION}/{result['_key']}"
    
    def _add_edge(self, db, from_id: str, to_id: str, collection_name: str, data: Dict[str, Any] = None) -> str:
        """
        Add an edge between two vertices.
        
        Args:
            db: The database instance
            from_id: The source vertex ID
            to_id: The target vertex ID
            collection_name: The edge collection name
            data: Optional additional data for the edge
            
        Returns:
            The edge document ID
        """
        collection = db.collection(collection_name)
        
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        if data:
            edge_doc.update(data)
        
        try:
            result = collection.insert(edge_doc)
            return f"{collection_name}/{result['_key']}"
        except Exception as e:
            print(f"Error adding edge: {str(e)}")
            return None
    
    def summarize_email(self, email_content: str) -> str:
        """
        Generate a summary of the email content.
        
        Args:
            email_content: The text content of the email
            
        Returns:
            Email summary
        """
        # Import here to avoid circular imports
        from app.agents.email_agent.prompts import SUMMARIZATION_PROMPT
        
        # For summarization, we don't need structured output
        summary_llm = LLMManager.get_model(
            provider="openai",
            model_name="gpt-4o-mini",
            temperature=0
        )
        
        # Create a prompt with the email content
        prompt = SUMMARIZATION_PROMPT.format(email_content=email_content)
        
        # Process with LLM
        return summary_llm.invoke(prompt)
    
    def process_message(
        self,
        user_id: str,
        email_data: Dict[str, Any],
        identifiers: List[str],
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an email message for analysis.
        
        Args:
            user_id: The ID of the user
            email_data: Email message data
            identifiers: List of identifiers extracted from the email
            message_id: Optional ID of the stored message document
            
        Returns:
            A dictionary with analysis results
        """
        try:
            db = get_user_db(user_id)
            
            # Extract email content for analysis
            from app.agents.email_agent.tools import extract_email_parts
            email_content, _ = extract_email_parts(email_data)
            
            if not email_content:
                return {"status": "error", "message": "Could not extract email content"}
            
            # Analyze the email
            analysis_result = self.analyze_message(email_content, identifiers)
            
            # Generate a summary
            summary = self.summarize_email(email_content)
            
            # Store the analysis
            analysis_id = self._add_analysis(db, analysis_result)
            
            # If we have a message_id, create an edge to the analysis
            if message_id and analysis_id:
                self._add_edge(db, message_id, analysis_id, EMAIL_MESSAGE_ANALYSIS_EDGE_COLLECTION)
            
            # Apply additional categorization
            categories = categorize_email(
                email_data, 
                {
                    "spam_score": analysis_result.spam_score,
                    "urgency_score": analysis_result.urgency_score,
                    "importance_score": analysis_result.importance_score,
                    "category": analysis_result.category
                }
            )
            
            # Prepare result
            result = {
                "status": "success",
                "analysis_id": analysis_id,
                "spam_score": analysis_result.spam_score,
                "urgency_score": analysis_result.urgency_score,
                "importance_score": analysis_result.importance_score,
                "category": analysis_result.category,
                "categories": categories,
                "is_spam": analysis_result.spam_score >= self.spam_threshold,
                "is_urgent": analysis_result.urgency_score >= self.urgent_threshold,
                "is_important": analysis_result.importance_score >= self.important_threshold,
                "reason": analysis_result.reason,
                "summary": summary
            }
            
            # Trigger notification if configured and if email is important or urgent
            if self.notification_callback and (result["is_urgent"] or result["is_important"]):
                if not result["is_spam"]:  # Don't notify for spam
                    self.notification_callback(user_id, email_data, result)
            
            return result
            
        except Exception as e:
            print(f"Error analyzing email message: {str(e)}")
            return {"status": "error", "message": str(e)}

def notify_message(user_id: str, email_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Send a notification about an important or urgent email.
    
    Args:
        user_id: The ID of the user
        email_data: Email message data
        analysis: Analysis results
    """
    try:
        # Extract metadata
        from app.agents.email_agent.tools import extract_email_metadata
        metadata = extract_email_metadata(email_data)
        
        # Determine notification type
        notification_type = []
        if analysis.get("is_urgent"):
            notification_type.append("urgent")
        if analysis.get("is_important"):
            notification_type.append("important")
        
        notification_type_str = " and ".join(notification_type)
        
        # Create notification
        notification = {
            "user_id": user_id,
            "type": "email_alert",
            "title": f"{notification_type_str.capitalize()} email from {metadata.get('sender', 'unknown')}",
            "content": f"Subject: {metadata.get('subject', 'No subject')}\n\n{analysis.get('summary', '')}",
            "metadata": {
                "email_id": email_data.get("message_id", ""),
                "analysis": {
                    "spam_score": analysis.get("spam_score"),
                    "urgency_score": analysis.get("urgency_score"),
                    "importance_score": analysis.get("importance_score"),
                    "category": analysis.get("category")
                }
            },
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        # In a real implementation, this would send to a notification service
        print(f"NOTIFICATION: {json.dumps(notification, indent=2)}")
        
        # TODO: Implement actual notification delivery
        # Example: push_notification_service.send(notification)
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")


@celery_app.task(name="email.analyze_message")
def analyze_email_message(
    user_id: str, 
    email_data: Dict[str, Any],
    identifiers: List[str],
    message_id: Optional[str] = None,
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Celery task to analyze an email message.
    
    Args:
        user_id: The ID of the user
        email_data: Email message data
        identifiers: List of identifiers extracted from the email
        message_id: Optional ID of the stored message document
        spam_threshold: Threshold for spam detection (0-1)
        urgent_threshold: Threshold for urgency detection (0-1)
        important_threshold: Threshold for importance detection (0-1)
        
    Returns:
        A dictionary with analysis results
    """
    analyzer = EmailAnalyzer(
        spam_threshold=spam_threshold,
        urgent_threshold=urgent_threshold,
        important_threshold=important_threshold,
        notification_callback=notify_message
    )
    
    return analyzer.process_message(user_id, email_data, identifiers, message_id) 