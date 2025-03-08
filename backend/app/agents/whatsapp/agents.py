import uuid
from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.language_models.chat_models import BaseChatModel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from prompts import (
    PRIVATE_AQL_GENERATION_PROMPT,
    PUBLIC_AQL_GENERATION_PROMPT
)

from tools import (
    save_contact,
    send_message,
    create_group,
    leave_group,
    add_to_group,
    remove_from_group,
    get_current_datetime,
    private_db_query_factory,
)

from app.common.tools import public_db_query_factory

class WhatsAppAgent:
    def __init__(
        self,
        model: BaseChatModel,
        private_db=None,
        public_db=None
    ):
        """
        Initialize the WhatsApp agent with private and public database connections.
        
        Args:
            model: The LLM model to use
            temperature: The temperature setting for the LLM
            private_db: ArangoGraph instance for the private database (user-specific data)
            public_db: ArangoGraph instance for the public database (common restaurant data)
        """
        self.model = model
        self.checkpointer = MemorySaver()
        
        # Check if database connections are provided
        if private_db is None or public_db is None:
            raise ValueError("Both private_db and public_db must be provided")
        
        self.private_db = private_db
        self.public_db = public_db
            
        self.agent_graph = self._create_agent()

    def _create_agent(self):
        """Create the agent with all the necessary tools."""
        system_prompt = SystemMessage(
            """You are a helpful WhatsApp assistant that can manage contacts, messages, and groups.
            You can also query databases to find information about contacts, messages, groups, and restaurant information.
            
            You have access to two databases:
            1. A private database with your WhatsApp data, dineout history, and food preferences.
            2. A public database with information about dine-out restaurants and online food ordering options.
            
            Be concise and specific in your responses. Always report exactly what you've done:
            - State the exact message content you've sent and to whom: "I've sent the message '[message content]' to [recipient name/number]"
            - Specify the exact contact name and number you've saved: "I've saved the contact '[name]' with phone number '[phone_number]'"
            - Include the exact group name and participants when creating or modifying groups: "I've created/modified the group '[group_name]' with participants: [participant list]"
            - Provide precise details from database queries: "Here are the results from the database: [query results]"
            
            Avoid ambiguity in your responses. Users should know exactly what actions you've performed.

            We don't like to have options until asked specifically, decide what is best.
            If you don't find any answer from aql queries, then try again with a different more broad query atleast 3 times before giving up.
            """
        )

        # Define all tools
        agent_tools = [
            save_contact,
            send_message,
            create_group,
            leave_group,
            add_to_group,
            remove_from_group,
            get_current_datetime,
            private_db_query_factory(self.model, self.private_db, PRIVATE_AQL_GENERATION_PROMPT),
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
            
        inputs = {"messages": [HumanMessage(content=user_message)]}
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get the final response
        result = self.agent_graph.invoke(inputs, config)
        final_message = result["messages"][-1]
        
        return final_message.content


    def run_interactive(self, debug=False):
        """
        Run the WhatsApp agent in an interactive loop, allowing users to chat with the agent.
        Press Ctrl+C to exit the loop.
        
        Args:
            debug: If True, shows detailed message stream for debugging
        """
        print("WhatsApp Agent Interactive Mode")
        print("Type your messages below. Press Ctrl+C to exit.")
        print("-" * 50)
        
        thread_id = str(uuid.uuid4())
        
        try:
            while True:
                user_input = input("\nYou: ")
                if not user_input.strip():
                    continue
                    
                print("\nProcessing...")
                
                if debug:
                    inputs = {"messages": [HumanMessage(content=user_input)]}
                    config = {"configurable": {"thread_id": thread_id}}
                    
                    for stream in self.agent_graph.stream(inputs, config, stream_mode="values"):
                        message = stream["messages"][-1]
                        if isinstance(message, tuple):
                            print(message)
                        else:
                            message.pretty_print()
                    
                    response = stream["messages"][-1].content
                else:
                    response = self.call_llm(user_input, thread_id)
                
                print(f"\nWhatsApp Agent: {response}")
                
        except KeyboardInterrupt:
            print("\n\nExiting WhatsApp Agent. Goodbye!")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    from app.common.llm_manager import LLMManager
    from arango import ArangoClient
    from langchain_community.graphs import ArangoGraph

    # Create database connections
    db_client = ArangoClient(hosts="http://localhost:8529")
    private_db = ArangoGraph(db_client.db("user_1235", username="root", password="zxcv", verify=True))
    public_db = ArangoGraph(db_client.db("common_db", username="root", password="zxcv", verify=True))
    
    # Create and run the WhatsApp agent
    agent = WhatsAppAgent(
        model=LLMManager.get_openai_model(model_name="gpt-4o"),
        private_db=private_db,
        public_db=public_db
    )
    agent.run_interactive(debug=True)
