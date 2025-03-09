import os
import sys
from time import sleep
from typing import List, Dict, Any, Optional
import datetime
from celery import Celery

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.agents.email_agent.analyser_agent import analyze_email_message
from app.db import get_system_db, get_user_db
from app.agents.email_agent.schemas import Identifiers, AttachmentInfo
from app.common.llm_manager import LLMManager
from app.agents.email_agent.tools import extract_email_parts, extract_email_metadata, extract_thread_info
from arango.database import StandardDatabase

# Initialize Celery app
celery_app = Celery('email', broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))

# Collection names for our graph
CONTACTS_COLLECTION = "contacts"
EMAIL_FOLDERS_COLLECTION = "email_folders"
EMAIL_MESSAGES_COLLECTION = "email_messages"
EMAIL_ATTACHMENTS_COLLECTION = "email_attachments"
IDENTIFIERS_COLLECTION = "identifiers"
CONTACT_FOLDER_EDGE_COLLECTION = "contact__email_folder"
IDENTIFIER_MESSAGE_EDGE_COLLECTION = "identifier__email_message"
CONTACT_MESSAGE_EDGE_COLLECTION = "contact__email_message"
FOLDER_MESSAGE_EDGE_COLLECTION = "folder__email_message"
MESSAGE_ATTACHMENT_EDGE_COLLECTION = "email_message__attachment"

class EmailConsumer:
    """
    A consumer that processes email messages:
    - Extracts identifiers using LLM
    - Stores email metadata, content, and attachments
    - Creates graph connections between entities
    """
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o-mini", temperature: float = 0):
        # Initialize the LLM with structured output to extract identifiers.
        self.llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(Identifiers)
        
        # Initialize the LLM for attachment analysis
        self.attachment_llm = LLMManager.get_model(
            provider=model_provider,
            model_name=model_name,
            temperature=temperature
        ).with_structured_output(AttachmentInfo)
    
    def extract_identifiers(self, email_content: str) -> List[str]:
        """
        Use an LLM to extract identifiers from the email content.
        
        Args:
            email_content: The text content of the email
            
        Returns:
            A list of identifier strings
        """
        # Import here to avoid circular imports
        from app.agents.email_agent.prompts import IDENTIFIER_EXTRACTION_PROMPT
        
        try:
            # Create a prompt with the email content
            prompt = IDENTIFIER_EXTRACTION_PROMPT.format(email_content=email_content)
            
            # Process with LLM
            result = self.llm.invoke(prompt)
            
            return result.identifiers
        except Exception as e:
            print(f"Error extracting identifiers: {str(e)}")
            return []
    
    def analyze_attachment(self, attachment_info: Dict[str, Any], email_content: str) -> Dict[str, Any]:
        """
        Use an LLM to analyze an email attachment.
        
        Args:
            attachment_info: Information about the attachment
            email_content: The text content of the email for context
            
        Returns:
            Enhanced attachment information with analysis
        """
        # Import here to avoid circular imports
        from app.agents.email_agent.prompts import ATTACHMENT_ANALYSIS_PROMPT
        
        try:
            # Create a prompt with the attachment info and email content
            prompt = ATTACHMENT_ANALYSIS_PROMPT.format(
                attachment_info=str(attachment_info),
                email_content=email_content
            )
            
            # Process with LLM
            result = self.attachment_llm.invoke(prompt)
            
            # Add analysis to attachment info
            attachment_info.update({
                "file_type": result.file_type,
                "description": result.description,
                "size_bytes": result.size_bytes or attachment_info.get("size", 0)
            })
            
            return attachment_info
        except Exception as e:
            print(f"Error analyzing attachment: {str(e)}")
            return attachment_info
    
    def _add_contact(self, db: StandardDatabase, email_address: str, name: Optional[str] = None) -> Optional[str]:
        """
        Add a contact to the database if it doesn't exist.
        
        Args:
            db: The database instance
            email_address: The email address of the contact
            name: Optional name of the contact
            
        Returns:
            The contact document ID
        """
        collection = db.collection(CONTACTS_COLLECTION)
        
        # Check if contact already exists
        query = f"""
        FOR c IN {CONTACTS_COLLECTION}
        FILTER c.email_address == @email_address
        RETURN c
        """
        cursor = db.aql.execute(query, bind_vars={"email_address": email_address})
        
        existing_contacts = [doc for doc in cursor]
        if existing_contacts:
            return existing_contacts[0]["_id"]
        
        # Create new contact
        contact_doc = {
            "email_address": email_address,
            "name": name or "",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = collection.insert(contact_doc)
        return f"{CONTACTS_COLLECTION}/{result['_key']}"
    
    def _add_folder(self, db: StandardDatabase, folder_name: str, folder_type: str = "CUSTOM") -> Optional[str]:
        """
        Add an email folder to the database if it doesn't exist.
        
        Args:
            db: The database instance
            folder_name: The name of the folder
            folder_type: The type of folder (INBOX, SENT, DRAFTS, etc.)
            
        Returns:
            The folder document ID
        """
        collection = db.collection(EMAIL_FOLDERS_COLLECTION)
        
        # Check if folder already exists
        query = f"""
        FOR f IN {EMAIL_FOLDERS_COLLECTION}
        FILTER f.name == @folder_name
        RETURN f
        """
        cursor = db.aql.execute(query, bind_vars={"folder_name": folder_name})
        
        existing_folders = [doc for doc in cursor]
        if existing_folders:
            return existing_folders[0]["_id"]
        
        # Create new folder
        folder_doc = {
            "name": folder_name,
            "type": folder_type,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = collection.insert(folder_doc)
        return f"{EMAIL_FOLDERS_COLLECTION}/{result['_key']}"
    
    def _add_message(self, db: StandardDatabase, email_data: Dict[str, Any],
                    sender_id: Optional[str] = None, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Add an email message to the database.
        
        Args:
            db: The database instance
            email_data: Email message data
            sender_id: Optional ID of the sender contact
            folder_id: Optional ID of the folder
            
        Returns:
            The message document ID
        """
        collection = db.collection(EMAIL_MESSAGES_COLLECTION)
        
        # Extract email parts and metadata
        text_content, attachments = extract_email_parts(email_data)
        metadata = extract_email_metadata(email_data)
        thread_info = extract_thread_info(email_data)
        
        # Create message document
        message_doc = {
            "subject": metadata.get("subject", ""),
            "body": text_content,
            "timestamp": metadata.get("date") or datetime.datetime.utcnow().isoformat(),
            "sender_id": sender_id,
            "folder_id": folder_id,
            "recipients": metadata.get("recipients", []),
            "cc": metadata.get("cc", []),
            "bcc": metadata.get("bcc", []),
            "message_id": metadata.get("message_id", ""),
            "in_reply_to": metadata.get("in_reply_to", ""),
            "references": metadata.get("references", []),
            "is_reply": thread_info.get("is_reply", False),
            "thread_depth": thread_info.get("thread_depth", 0),
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = collection.insert(message_doc)
        return f"{EMAIL_MESSAGES_COLLECTION}/{result['_key']}"
    
    def _add_attachment(self, db: StandardDatabase, attachment_data: Dict[str, Any], email_content: str) -> Optional[str]:
        """
        Add an email attachment to the database.
        
        Args:
            db: The database instance
            attachment_data: Attachment data
            email_content: Email content for context in analysis
            
        Returns:
            The attachment document ID
        """
        collection = db.collection(EMAIL_ATTACHMENTS_COLLECTION)
        
        # Analyze the attachment
        enhanced_attachment = self.analyze_attachment(attachment_data, email_content)
        
        # Create attachment document (excluding binary data to save space)
        attachment_doc = {
            "filename": enhanced_attachment.get("filename", ""),
            "content_type": enhanced_attachment.get("content_type", ""),
            "size": enhanced_attachment.get("size", 0),
            "description": enhanced_attachment.get("description", ""),
            "file_type": enhanced_attachment.get("file_type", ""),
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = collection.insert(attachment_doc)
        return f"{EMAIL_ATTACHMENTS_COLLECTION}/{result['_key']}"
    
    def _add_identifier(self, db: StandardDatabase, identifier: str) -> Optional[str]:
        """
        Add an identifier to the database if it doesn't exist.
        
        Args:
            db: The database instance
            identifier: The identifier string
            
        Returns:
            The identifier document ID
        """
        collection = db.collection(IDENTIFIERS_COLLECTION)
        
        # Check if identifier already exists
        query = f"""
        FOR i IN {IDENTIFIERS_COLLECTION}
        FILTER i.value == @identifier
        RETURN i
        """
        cursor = db.aql.execute(query, bind_vars={"identifier": identifier})
        
        existing_identifiers = [doc for doc in cursor]
        if existing_identifiers:
            return existing_identifiers[0]["_id"]
        
        # Create new identifier
        identifier_doc = {
            "value": identifier,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        result = collection.insert(identifier_doc)
        return f"{IDENTIFIERS_COLLECTION}/{result['_key']}"
    
    def _add_edge(self, db: StandardDatabase, from_id: str, to_id: str, 
                 collection_name: str, data: Dict[str, Any] = None) -> Optional[str]:
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
    
    def process_message(self, user_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an email message from start to finish:
        - Store email metadata and content
        - Extract and store identifiers
        - Create graph connections
        
        Args:
            user_id: The ID of the user
            email_data: Email message data
            
        Returns:
            A dictionary with processing results
        """
        try:
            db = get_user_db(user_id)
            
            # Extract email content for identifier extraction
            email_content, attachments = extract_email_parts(email_data)
            if not email_content:
                return {"status": "error", "message": "Could not extract email content"}
            
            # Extract metadata
            metadata = extract_email_metadata(email_data)
            
            # Add sender to contacts
            sender_id = None
            if metadata.get("sender"):
                sender_id = self._add_contact(db, metadata["sender"])
            
            # Add email to appropriate folder (default to INBOX)
            folder_name = email_data.get("folder", "INBOX")
            folder_id = self._add_folder(db, folder_name)
            
            # Add the email message
            message_id = self._add_message(db, email_data, sender_id, folder_id)
            if not message_id:
                return {"status": "error", "message": "Failed to add email message"}
            
            # Connect sender to message
            if sender_id:
                self._add_edge(db, sender_id, message_id, CONTACT_MESSAGE_EDGE_COLLECTION)
            
            # Connect folder to message
            if folder_id:
                self._add_edge(db, folder_id, message_id, FOLDER_MESSAGE_EDGE_COLLECTION)
            
            # Extract identifiers
            identifiers = self.extract_identifiers(email_content)
            
            # Add identifiers and connect to message
            for identifier in identifiers:
                identifier_id = self._add_identifier(db, identifier)
                if identifier_id:
                    self._add_edge(db, identifier_id, message_id, IDENTIFIER_MESSAGE_EDGE_COLLECTION)
            
            # Process attachments
            attachment_ids = []
            for attachment_data in attachments:
                attachment_id = self._add_attachment(db, attachment_data, email_content)
                if attachment_id:
                    attachment_ids.append(attachment_id)
                    self._add_edge(db, message_id, attachment_id, MESSAGE_ATTACHMENT_EDGE_COLLECTION)
            
            return {
                "status": "success",
                "message_id": message_id,
                "identifiers": identifiers,
                "attachments": attachment_ids
            }
            
        except Exception as e:
            print(f"Error processing email message: {str(e)}")
            return {"status": "error", "message": str(e)}


@celery_app.task(name="email.process_message")
def process_email_message(user_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to process an email message.
    
    Args:
        user_id: The ID of the user
        email_data: Email message data
        
    Returns:
        A dictionary with processing results
    """
    consumer = EmailConsumer()
    return consumer.process_message(user_id, email_data)


@celery_app.task(name="email.process_folder_action")
def process_email_folder_action(user_id: str, folder_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to process an email folder action (create/update/delete).
    
    Args:
        user_id: The ID of the user
        folder_data: Email folder data
        
    Returns:
        A dictionary with processing results
    """
    try:
        db = get_user_db(user_id)
        consumer = EmailConsumer()
        
        # Get folder information
        folder_name = folder_data.get("name", "")
        folder_type = folder_data.get("type", "CUSTOM")
        action = folder_data.get("action", "create")
        
        if action == "create" or action == "update":
            folder_id = consumer._add_folder(db, folder_name, folder_type)
            return {"status": "success", "folder_id": folder_id}
        elif action == "delete":
            collection = db.collection(EMAIL_FOLDERS_COLLECTION)
            query = f"""
            FOR f IN {EMAIL_FOLDERS_COLLECTION}
            FILTER f.name == @folder_name
            REMOVE f IN {EMAIL_FOLDERS_COLLECTION}
            RETURN OLD
            """
            cursor = db.aql.execute(query, bind_vars={"folder_name": folder_name})
            deleted = [doc for doc in cursor]
            
            if deleted:
                return {"status": "success", "deleted": len(deleted)}
            else:
                return {"status": "error", "message": "Folder not found"}
        else:
            return {"status": "error", "message": "Invalid action"}
            
    except Exception as e:
        print(f"Error processing folder action: {str(e)}")
        return {"status": "error", "message": str(e)} 