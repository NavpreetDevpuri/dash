import os
import sys
from typing import List, Dict, Any, Optional, Callable
import datetime
import json
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.slack.schemas import AnalysisResult
from app.common.llm_manager import LLMManager
from app.common.base_consumer import BaseGraphConsumer

# Initialize Celery app
celery_app = Celery('slack', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Updated collection and edge names for our simplified graph plus extra analysis nodes
CONTACTS_COLLECTION = "contacts"
CHANNELS_COLLECTION = "slack_channels"              # Previously: slack_conversations
SLACK_MESSAGES_COLLECTION = "slack_messages"
IDENTIFIERS_COLLECTION = "identifiers"
ANALYSIS_COLLECTION = "analysis"

SLACK_MESSAGE_ANALYSIS_EDGE_COLLECTION = "slack_message_analysis"  # Edge linking message to analysis

class SlackAnalyzer(BaseGraphConsumer):
    """
    A Celery consumer that analyzes Slack messages for spam, urgency, and importance.
    It reuses our graph nodes (contacts, slack_channels, slack_messages, identifiers)
    and adds extra analysis nodes.
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
        self.notification_callback = notification_callback or notify_message
    
    def analyze_message(self, message_content: str, identifiers: List[str]) -> AnalysisResult:
        """
        Use an LLM to analyze a message for spam, urgency, and importance.
        """
        prompt = f"""
Analyze this Slack message for:
1. Spam likelihood (scale 0-1)
2. Urgency (scale 0-1)
3. Importance (scale 0-1)

Consider these extracted identifiers: {', '.join(identifiers)}

Message:
{message_content}

Provide scores and reasoning in your response.
"""
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        return response
    
    def _add_analysis_identifier(self, db, analysis_type: str, analysis_data: Dict[str, Any]) -> str:
        """
        Add an analysis result document to the database.
        """
        if not db.has_collection(ANALYSIS_COLLECTION):
            return None
        
        analysis_doc = {
            "type": analysis_type,
            "score": analysis_data.get("score", 0),
            "reason": analysis_data.get("reason", ""),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        result = db.collection(ANALYSIS_COLLECTION).insert(analysis_doc)
        return result["_id"]
    
    def _add_edge(self, db, from_id: str, to_id: str, collection_name: str, data: Dict[str, Any] = None) -> str:
        """
        Add an edge between two vertices if it doesn't already exist.
        """
        if not db.has_collection(collection_name):
            return None
        
        # Ensure from_id and to_id are in the correct "<collection>/<key>" format.
        if "/" not in from_id or "/" not in to_id:
            return None
        
        aql = f"""
        FOR edge IN {collection_name}
          FILTER edge._from == @from_id AND edge._to == @to_id
          RETURN edge._id
        """
        cursor = db.aql.execute(aql, bind_vars={"from_id": from_id, "to_id": to_id})
        edge_id = cursor.next() if cursor.has_more() else None
        
        if edge_id:
            return edge_id
        
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "created_at": datetime.datetime.now().isoformat()
        }
        if data:
            edge_doc.update(data)
        
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
        Process and analyze a Slack message.
        """
        try:
            db = get_user_db(user_id)
            if not db:
                return {"status": "error", "message": "Failed to connect to database"}
            
            content = message_data.get("text", "")
            if not content or not content.strip():
                return {"status": "error", "message": "Message content is empty"}
            
            
            # Analyze the message.
            analysis_result = self.analyze_message(content, identifiers)
            
            # Add analysis results to the database.
            spam_analysis_id = self._add_analysis_identifier(db, "spam", {
                "score": analysis_result.spam_score,
                "reason": analysis_result.reason
            })
            urgent_analysis_id = self._add_analysis_identifier(db, "urgent", {
                "score": analysis_result.urgency_score,
                "reason": analysis_result.reason
            })
            important_analysis_id = self._add_analysis_identifier(db, "important", {
                "score": analysis_result.importance_score,
                "reason": analysis_result.reason
            })
            
            # Link analyses to the message.
            if spam_analysis_id:
                self._add_edge(
                    db,
                    message_id,
                    f"{spam_analysis_id}",
                    SLACK_MESSAGE_ANALYSIS_EDGE_COLLECTION,
                    {"type": "spam"}
                )
            if urgent_analysis_id:
                self._add_edge(
                    db,
                    message_id,
                    f"{urgent_analysis_id}",
                    SLACK_MESSAGE_ANALYSIS_EDGE_COLLECTION,
                    {"type": "urgent"}
                )
            if important_analysis_id:
                self._add_edge(
                    db,
                    message_id,
                    f"{important_analysis_id}",
                    SLACK_MESSAGE_ANALYSIS_EDGE_COLLECTION,
                    {"type": "important"}
                )
            
            # Determine notification conditions.
            is_spam = analysis_result.spam_score >= self.spam_threshold
            is_urgent = analysis_result.urgency_score >= self.urgent_threshold
            is_important = analysis_result.importance_score >= self.important_threshold
            
            analysis_dict = {
                "is_spam": is_spam,
                "is_urgent": is_urgent,
                "is_important": is_important,
                "spam_score": analysis_result.spam_score,
                "urgency_score": analysis_result.urgency_score,
                "importance_score": analysis_result.importance_score,
                "spam_threshold": self.spam_threshold,
                "urgent_threshold": self.urgent_threshold,
                "important_threshold": self.important_threshold,
                "reason": analysis_result.reason
            }
            
            if self.notification_callback and (is_urgent or is_important) and not is_spam:
                self.notification_callback(user_id, message_data, analysis_dict)
            
            return {
                "status": "success",
                "message": "Message analyzed successfully",
                "message_id": message_id,
                "analysis": analysis_dict
            }
            
        except Exception as e:
            import traceback
            error_stack = traceback.format_exc()
            print(f"Error analyzing Slack message: {str(e)}")
            print(f"Stack trace: {error_stack}")
            return {
                "status": "error",
                "message": f"Error analyzing message: {str(e)}",
                "error": str(e)
            }
    

def notify_message(user_id: str, message_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Default notification function for Slack message analysis.
    
    Args:
        user_id: The ID of the user
        message_data: Slack message data
        analysis: Analysis results
    """
    # Build notification message
    notification = ["Slack Message Analysis:"]
    
    # Add sender info
    sender = message_data.get("username", "Unknown user")
    notification.append(f"From: {sender}")
    
    # Add urgency and importance info
    is_urgent = analysis["urgency_score"] >= analysis["urgent_threshold"]
    is_important = analysis["importance_score"] >= analysis["important_threshold"]
    
    if is_urgent:
        notification.append("🔴 URGENT MESSAGE")
    
    if is_important:
        notification.append("⭐ IMPORTANT MESSAGE")
    
    # Add message preview
    content = message_data.get("content", "")
    preview = content[:100] + "..." if len(content) > 100 else content
    notification.append(f"Message: {preview}")
    
    # Add scores
    notification.append(f"Urgency score: {analysis['urgency_score']:.2f}")
    notification.append(f"Importance score: {analysis['importance_score']:.2f}")
    
    # Print notification (in production this would send to notification service)
    print("\n".join(notification))

@celery_app.task(name="slack.analyze_message")
def analyze_slack_message(
    user_id: str, 
    message_data: Dict[str, Any],
    identifiers: List[str],
    message_id: Optional[str] = None,
    spam_threshold: float = 0.5,
    urgent_threshold: float = 0.7,
    important_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Celery task to analyze a Slack message.
    """
    analyzer = SlackAnalyzer(
        spam_threshold=spam_threshold,
        urgent_threshold=urgent_threshold,
        important_threshold=important_threshold
    )
    
    result = analyzer.process_message(
        user_id=user_id,
        message_data=message_data,
        identifiers=identifiers,
        message_id=message_id
    )
    
    return result
