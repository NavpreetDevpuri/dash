import os
import sys
from typing import List, Dict, Any, Optional, Callable
import datetime
import json
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.whatsapp.schemas import AnalysisResult
from app.common.llm_manager import LLMManager
from app.common.base_consumer import BaseGraphConsumer

# Initialize Celery app
celery_app = Celery('whatsapp_analyzer', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

ANALYSIS_COLLECTION = "analysis"
WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION = "whatsapp_message__analysis"

class WhatsAppAnalyzer(BaseGraphConsumer):
    """
    A Celery consumer that analyzes WhatsApp messages for spam, urgency, and importance.
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
            model_provider: The LLM provider to use.
            model_name: The model name to use.
            temperature: The temperature for the model.
            spam_threshold: Threshold for flagging messages as spam (0-1).
            urgent_threshold: Threshold for flagging messages as urgent (0-1).
            important_threshold: Threshold for flagging messages as important (0-1).
            notification_callback: Optional callback for notifications.
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
    
    def analyze_message(self, message_payload: str, identifiers: List[str]) -> AnalysisResult:
        """
        Use an LLM to analyze a message for spam, urgency, and importance.
        
        Args:
            message_payload: The payload of the WhatsApp message.
            identifiers: List of extracted identifiers from the message.
            
        Returns:
            An AnalysisResult object with scores and reasoning.
        """
        prompt = f"""
        Analyze this WhatsApp message for:
        1. Spam likelihood (scale 0-1)
        2. Urgency (scale 0-1)
        3. Importance (scale 0-1)

        Consider these extracted identifiers: {', '.join(identifiers)}
        
        Message:
        {message_payload}
        
        Provide scores and reasoning in your response.
        """
        response = self.llm.invoke([{"role": "user", "content": prompt}])
        return response
    
    def _add_analysis_identifier(self, db, analysis_type: str, analysis_data: Dict[str, Any]) -> str:
        """
        Add an analysis result to the database.
        
        Args:
            db: Database connection.
            analysis_type: Type of analysis (spam, urgent, important).
            analysis_data: Analysis data including score and reasoning.
            
        Returns:
            The ID of the inserted analysis.
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
        
        Args:
            db: Database connection.
            from_id: The ID of the from vertex.
            to_id: The ID of the to vertex.
            collection_name: The name of the edge collection.
            data: Additional data to store on the edge.
            
        Returns:
            The ID of the edge.
        """
        if not db.has_collection(collection_name):
            return None
        
        # Using Python formatter for AQL with {collection_name}
        aql = f"""
        FOR edge IN {collection_name}
            FILTER edge._from == @from_id AND edge._to == @to_id
            RETURN edge._id
        """
        cursor = db.execute_query(aql, {"from_id": from_id, "to_id": to_id})
        edge_ids = list(cursor)
        if edge_ids:
            return edge_ids[0]
        
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
        Process and analyze a WhatsApp message.
        
        Args:
            user_id: The ID of the user.
            message_data: WhatsApp message data.
            identifiers: List of extracted identifiers.
            message_id: Optional ID of an existing message.
            
        Returns:
            A dictionary with the results of analysis.
        """
        try:
            db = get_user_db(user_id)
            if not db:
                return {"status": "error", "message": "Failed to connect to database"}
            
            # Retrieve the text from the message data.
            text = message_data.get("text", "")
            if not text or not text.strip():
                return {"status": "error", "message": "Message text is empty"}
        
            message_doc_id = message_id
            
            analysis_result = self.analyze_message(text, identifiers)
            
            spam_analysis_id = self._add_analysis_identifier(db, "spam", {
                "score": analysis_result.spam_score,
                "reason": analysis_result.summary or ""
            })
            urgent_analysis_id = self._add_analysis_identifier(db, "urgent", {
                "score": analysis_result.urgency_score,
                "reason": analysis_result.summary or ""
            })
            important_analysis_id = self._add_analysis_identifier(db, "important", {
                "score": analysis_result.importance_score,
                "reason": analysis_result.summary or ""
            })
            
            if spam_analysis_id:
                self._add_edge(
                    db,
                    message_doc_id,
                    f"{ANALYSIS_COLLECTION}/{spam_analysis_id}",
                    WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION,
                    {"type": "spam"}
                )
            if urgent_analysis_id:
                self._add_edge(
                    db,
                    message_doc_id,
                    f"{ANALYSIS_COLLECTION}/{urgent_analysis_id}",
                    WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION,
                    {"type": "urgent"}
                )
            if important_analysis_id:
                self._add_edge(
                    db,
                    message_doc_id,
                    f"{ANALYSIS_COLLECTION}/{important_analysis_id}",
                    WHATSAPP_MESSAGE_ANALYSIS_EDGE_COLLECTION,
                    {"type": "important"}
                )
            
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
                "summary": analysis_result.summary
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
            return {
                "status": "error",
                "message": f"Error analyzing message: {str(e)}",
                "error": str(e)
            }
    
def notify_message(user_id: str, message_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Default notification function for WhatsApp message analysis.
    
    Args:
        user_id: The ID of the user.
        message_data: WhatsApp message data.
        analysis: Analysis results.
    """
    notification = ["WhatsApp Message Analysis:"]
    sender = message_data.get("name", "Unknown contact")
    notification.append(f"From: {sender}")
    is_urgent = analysis["urgency_score"] >= analysis["urgent_threshold"]
    is_important = analysis["importance_score"] >= analysis["important_threshold"]
    if is_urgent:
        notification.append("🔴 URGENT MESSAGE")
    if is_important:
        notification.append("⭐ IMPORTANT MESSAGE")
    # Retrieve text instead of content
    text = message_data.get("text", "")
    preview = text[:100] + "..." if len(text) > 100 else text
    notification.append(f"Message: {preview}")
    notification.append(f"Urgency score: {analysis['urgency_score']:.2f}")
    notification.append(f"Importance score: {analysis['importance_score']:.2f}")
    print("\n".join(notification))

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
        user_id: The ID of the user.
        message_data: Message data including payload.
        identifiers: List of extracted identifiers.
        message_id: Optional ID of an existing message.
        spam_threshold: Threshold for flagging messages as spam (0-1).
        urgent_threshold: Threshold for flagging messages as urgent (0-1).
        important_threshold: Threshold for flagging messages as important (0-1).
        
    Returns:
        Analysis results.
    """
    analyzer = WhatsAppAnalyzer(
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

# Test code
if __name__ == "__main__":
    test_user_id = "1270834"
    test_message = {
        "from": "john_doe",
        "to": "nav",
        "is_group": False,
        "text": "Hi, I'm working on the dashboard project for Acme Inc. Please contact john.doe@example.com for details.",
        "timestamp": str(datetime.datetime.utcnow())
    }
    test_identifiers = ["urgent", "dashboard project", "acme inc", "tomorrow", "asap"]
    
    result = analyze_whatsapp_message(
        test_user_id, 
        test_message,
        test_identifiers,
        spam_threshold=0.4,
        urgent_threshold=0.6,
        important_threshold=0.6
    )
    
    print("Analysis result:")
    print(result)