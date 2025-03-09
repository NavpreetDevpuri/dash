import uuid
from typing import Callable, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command, interrupt, PregelTask

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.common.utils import safely_check_interrupts
from app.agents.email.prompts import EMAIL_ANALYSIS_PROMPT, IDENTIFIER_EXTRACTION_PROMPT, SUMMARIZATION_PROMPT
from app.common.prompts import PUBLIC_AQL_GENERATION_PROMPT

from app.agents.email.tools import (
    send_email_factory,
    reply_to_email_factory,
    forward_email_factory,
    move_email_factory,
    create_folder_factory,
    private_db_query_factory
)

from app.common.tools import public_db_query_factory, get_current_datetime, human_confirmation_factory, about_me_factory


class EmailAgent:
    """Email agent with memory and tooling to assist in email management tasks."""

    def __init__(
        self,
        checkpointer: BaseCheckpointSaver,
        model: BaseChatModel,
        private_db=None,
        public_db=None,
        confirmation_callback: Callable = None
    ):
        """
        Initialize the Email agent with private and public database connections.
        
        Args:
            model: The LLM model to use
            private_db: ArangoGraph instance for the private database (user-specific private data)
            public_db: ArangoGraph instance for the public database (common data)
            confirmation_callback: Callback function for human confirmation
        """
        self.model = model
        self.checkpointer = checkpointer
        self.confirmation_callback = confirmation_callback
        
        # Check if database connections are provided
        if private_db is None or public_db is None:
            raise ValueError("Both private_db and public_db must be provided")
        
        self.private_db = private_db
        self.public_db = public_db
            
        self.agent_graph = self._create_agent()

    def _create_agent(self):
        """Create the agent with all the necessary tools."""
        system_prompt = SystemMessage(
            """You are a helpful Email assistant that can manage emails, folders, and perform email-related tasks.
            You can send, reply to, and forward emails, as well as organize emails into folders.
            You can also query databases to find information about emails, contacts, and other relevant data.
            
            You have access to two databases:
            1. An email database with your email data, contacts, and email history.
            2. A public database with general information that might be useful for composing emails.
            
            Be concise and specific in your responses. Always report exactly what you've done:
            - State the exact email content you've sent and to whom: "I've sent an email to [recipients] with subject '[subject]'"
            - Include the exact folder name when organizing emails: "I've moved the email to '[folder_name]'"
            - Provide precise details from database queries: "Here are the results from the database: [query results]"
            
            Avoid ambiguity in your responses. Users should know exactly what actions you've performed.

            We don't like to have options until asked specifically, decide what is best.
            If you don't find any answer from database queries, then try again with a different more broad query at least 3 times before giving up.

            * If you write an email, use the human_confirmation tool to confirm with the user before sending only if they haven't already confirmed it.
            * Clearly mention what you are sending when requesting confirmation.
            * Always try to fill up all the details making sure there are no template messages like [Your Name] or [Company Name]. Always try to find information to fill up the template if possible ask the user for it.
            """
        )
        
        # Get user info for Email from DB if available
        user_data = self.private_db.db.collection('me').get('me')
        if not user_data:
            raise ValueError("User data not found in database")
        
        email_address = user_data.get('email')
        user_id = user_data.get('user_id')
        
        if not email_address or not user_id:
            raise ValueError("Missing required user data: email, or user_id")

        # Define all tools using factory pattern
        agent_tools = [
            send_email_factory(user_id),
            reply_to_email_factory(user_id),
            forward_email_factory(user_id),
            move_email_factory(user_id),
            create_folder_factory(user_id),
            get_current_datetime,
            human_confirmation_factory(self.confirmation_callback),
            about_me_factory(self.private_db),
            private_db_query_factory(self.model, self.private_db, EMAIL_ANALYSIS_PROMPT),
            public_db_query_factory(self.model, self.public_db, PUBLIC_AQL_GENERATION_PROMPT)
        ]

        return create_react_agent(
            model=self.model,
            state_modifier=system_prompt,
            tools=agent_tools,
            checkpointer=self.checkpointer
        )

    def call_llm(self, user_message: str, thread_id: Optional[str] = None) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_message: The user's message
            thread_id: Optional thread ID for conversation continuity
        
        Returns:
            The agent's response
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": thread_id}}

        if safely_check_interrupts(self.agent_graph, config):
            inputs = Command(resume={"answer": user_message})
        else:
            inputs = {"messages": [HumanMessage(content=user_message)]}
        
        # Get the final response
        result = self.agent_graph.invoke(inputs, config)
        final_message = result["messages"][-1]
        
        return final_message.content

    def run_interactive(self, thread_id: str, debug=False):
        """
        Run the Email agent in an interactive loop, allowing users to chat with the agent.
        Press Ctrl+C to exit the loop.
        
        Args:
            debug: If True, shows detailed message stream for debugging
        """
        print("Email Agent Interactive Mode")
        print("Type your messages below. Press Ctrl+C to exit.")
        print("-" * 50)
        
        try:
            while True:
                user_input = input("\nYou: ")
                if not user_input.strip():
                    continue
                    
                print("\nProcessing...")
                
                if debug:
                    config = {"configurable": {"thread_id": thread_id}}
                    stream_mode = "values"

                    # Check if there's an ongoing PregelTask that needs user input
                    if safely_check_interrupts(self.agent_graph, config):
                        inputs = Command(resume={"answer": user_input})
                    else:
                        inputs = {"messages": [HumanMessage(content=user_input)]}
                    
                    for stream in self.agent_graph.stream(inputs, config, stream_mode=stream_mode):
                        message = stream["messages"][-1]
                        if isinstance(message, tuple):
                            print(message)
                        else:
                            message.pretty_print()
                    
                    response = stream["messages"][-1].content
                else:
                    response = self.call_llm(user_input, thread_id)
                
                print(f"\nEmail Agent: {response}")
                
        except KeyboardInterrupt:
            print("\n\nExiting Email Agent. Goodbye!")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    from app.common.llm_manager import LLMManager
    from arango import ArangoClient
    from langchain_community.graphs import ArangoGraph
    import sqlite3
    from langgraph.checkpoint.sqlite import SqliteSaver
    
    # Create a direct sqlite connection instead of using SQLAlchemy
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)

    # Create database connections
    db_client = ArangoClient(hosts="http://localhost:8529")
    private_db = ArangoGraph(db_client.db("user_1235", username="root", password="zxcv", verify=True))
    public_db = ArangoGraph(db_client.db("common_db", username="root", password="zxcv", verify=True))
    
    # Create and run the Email agent
    agent = EmailAgent(
        checkpointer=memory,
        model=LLMManager.get_openai_model(model_name="gpt-4o"),
        private_db=private_db,
        public_db=public_db,
        confirmation_callback=lambda x: print("Agent Asked for confirmation: ", x)
    )

    agent.run_interactive(thread_id="123", debug=True)
