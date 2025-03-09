import uuid
from typing import Callable, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.common.utils import safely_check_interrupts
from app.agents.foodorder.prompts import FOOD_AQL_GENERATION_PROMPT, SYSTEM_PROMPT
from app.common.prompts import PUBLIC_AQL_GENERATION_PROMPT

from app.agents.foodorder.tools import (
    place_order_factory,
    public_dish_search_factory,
    private_db_query_factory
)

from app.common.tools import human_confirmation_factory, about_me_factory, public_db_query_factory


class FoodOrderingAgent:
    """Food ordering agent with capabilities to search for dishes and place orders."""

    def __init__(
        self,
        checkpointer: BaseCheckpointSaver,
        model: BaseChatModel,
        private_db=None,
        public_db=None, 
        confirmation_callback: Callable = None
    ):
        """
        Initialize the Food Ordering agent with private and public database connections.
        
        Args:
            model: The LLM model to use
            private_db: ArangoGraph instance for the private database (user-specific data)
            public_db: ArangoGraph instance for the public database (common dish data)
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
        system_prompt = SystemMessage(content=SYSTEM_PROMPT)
        
        # Get user info from DB if available
        user_data = self.private_db.db.collection('me').get('me')
        if not user_data:
            raise ValueError("User data not found in database")
        
        user_id = user_data.get('user_id')
        
        if not user_id:
            raise ValueError("Missing required user data: user_id")
        
        # Create agent tools
        tools = [
            # Ordering tool
            place_order_factory(user_id),
            human_confirmation_factory(self.confirmation_callback),
            about_me_factory(self.private_db),
            
            # Connect to public database for dish information
            public_db_query_factory(
                self.model, 
                self.public_db, 
                PUBLIC_AQL_GENERATION_PROMPT
            ),
            
            # More specific dish search tool
            public_dish_search_factory(
                user_id,
                self.model,
                self.public_db,
                FOOD_AQL_GENERATION_PROMPT
            ),
            
            # Query private database for user preferences and order history
            private_db_query_factory(
                self.model, 
                self.private_db, 
                FOOD_AQL_GENERATION_PROMPT
            )
        ]
        
        # Create a ReAct agent using LangGraph
        return create_react_agent(
            model=self.model,
            state_modifier=system_prompt,
            tools=tools,
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
        Run the Food Ordering agent in an interactive loop, allowing users to chat with the agent.
        Press Ctrl+C to exit the loop.
        
        Args:
            debug: If True, shows detailed message stream for debugging
        """
        print("Food Ordering Agent Interactive Mode")
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
                
                print(f"\nFood Ordering Agent: {response}")
                
        except KeyboardInterrupt:
            print("\n\nExiting Food Ordering Agent. Goodbye!")
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
    
    # Initialize the agent
    agent = FoodOrderingAgent(
        model=LLMManager.get_openai_model(model_name="gpt-4o"),
        private_db=private_db,
        public_db=public_db, 
        checkpointer=memory
    )   

    # Run the agent in interactive mode
    agent.run_interactive(thread_id=uuid.uuid4()) 