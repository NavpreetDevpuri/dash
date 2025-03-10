import uuid
from typing import Callable, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command, interrupt
from langgraph.checkpoint.base import BaseCheckpointSaver
import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")


import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.common.utils import safely_check_interrupts
from app.agents.whatsapp.prompts import PRIVATE_AQL_GENERATION_PROMPT
from app.common.prompts import PUBLIC_AQL_GENERATION_PROMPT

from app.agents.whatsapp.tools import (
    save_contact_factory, 
    send_message_factory, 
    create_group_factory, 
    leave_group_factory, 
    add_to_group_factory, 
    remove_from_group_factory,
)

from app.common.tools import public_db_query_factory, get_current_datetime, human_confirmation_factory, about_me_factory, private_db_query_factory, text_to_nx_algorithm_for_public_db_factory

# Additional imports for MainAgent
from app.agents.foodorder.tools import place_order_factory, public_dish_search_factory
from app.agents.dineout.tools import book_dineout_factory
from app.agents.email_agent.tools import (
    send_email_factory,
    reply_to_email_factory,
    forward_email_factory,
    create_folder_factory,
    move_email_factory
)
from app.agents.slack.tools import (
    create_channel_factory,
    leave_channel_factory,
    add_to_channel_factory,
    remove_from_channel_factory,
    set_channel_topic_factory,
    send_message_factory as slack_send_message_factory,
    set_status_factory,
    set_status_with_time_factory
)

# Import prompts for different agents
from app.agents.foodorder.prompts import FOOD_AQL_GENERATION_PROMPT as FOOD_PRIVATE_AQL_PROMPT
from app.agents.dineout.prompts import RESTAURANT_AQL_GENERATION_TEMPLATE as DINEOUT_PRIVATE_AQL_PROMPT
from app.agents.email_agent.prompts import EMAIL_ANALYSIS_PROMPT as EMAIL_PRIVATE_AQL_PROMPT
from app.agents.slack.prompts import PRIVATE_AQL_GENERATION_PROMPT as SLACK_PRIVATE_AQL_PROMPT

# Prompts for AQL generatio
class MainAgent:
    """Main agent with combined tools from all specialized agents."""

    def __init__(
        self,
        checkpointer: BaseCheckpointSaver,
        model: BaseChatModel,
        private_db=None,
        public_db=None,
        confirmation_callback: Callable = None
    ):
        """
        Initialize the main agent with all tools from specialized agents.
        
        Args:
            model: The LLM model to use
            checkpointer: The checkpointer to use for conversation history
            private_db: ArangoGraph instance for the private database (user-specific data)
            public_db: ArangoGraph instance for the public database (common data)
            confirmation_callback: Optional callback for human confirmation
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
        """Create the agent with all the necessary tools from all specialized agents."""
        system_prompt = SystemMessage(
            """You are a powerful assistant that can handle various tasks including:
            
            1. WhatsApp messaging, contacts, and group management
            2. Food ordering from restaurants
            3. Booking restaurant reservations for dining out
            4. Managing emails (sending, replying, forwarding, organizing)
            5. Slack messaging, channel management, and status updates
            
            You can also query databases to find information related to any of these domains.
            
            You have access to two databases:
            1. A private database with user-specific data like contacts, messages, emails, Slack history, food preferences, etc.
            2. A public database with information about restaurants, food delivery options, and more.
            
            Be concise and specific in your responses. Always report exactly what you've done:
            - When sending messages (WhatsApp/Slack/Email): "I've sent the message '[message content]' to [recipient]"
            - When booking reservations: "I've booked a table at [restaurant] for [time] for [party size] people"
            - When placing food orders: "I've ordered [dishes] from [restaurant] to be delivered to [address]"
            - When managing contacts/channels/folders: "I've created/modified [item] with [details]"
            
            Avoid ambiguity in your responses related to actions you've performed. Users should know exactly what actions you've performed.

            If you don't find any answer from database queries, try again with a different more broad query at least 3 times before giving up.

            We don't like to have options until asked specifically, decide what is best.
            Always end your response with a question to the user or a suggestion for what to do next or best wishes.
            """
        )

        # Get user info from DB if available
        user_data = self.private_db.db.collection('me').get('me')
        if not user_data:
            raise ValueError("User data not found in database")
        
        # Extract user info for various platforms
        user_id = user_data.get('user_id')
        
        # WhatsApp info
        whatsapp_username = user_data.get('whatsapp_username') or "default_whatsapp_username"
        whatsapp_number = user_data.get('whatsapp_number') or "default_whatsapp_number"
        
        # Slack info
        slack_username = user_data.get('slack_username') or "default_slack_username"
        
        # Email info
        email_address = user_data.get('email_address') or "default_email_address"
        
        if not user_id:
            raise ValueError("Missing required user_id in user data")

        # Define all tools using factory pattern
        agent_tools = [
            # Common tools
            get_current_datetime,
            human_confirmation_factory(self.confirmation_callback),
            about_me_factory(self.private_db),
            public_db_query_factory(self.model, self.public_db, PUBLIC_AQL_GENERATION_PROMPT),
            
            # WhatsApp tools
            save_contact_factory(user_id),
            send_message_factory(user_id, whatsapp_number),
            create_group_factory(user_id),
            leave_group_factory(user_id),
            add_to_group_factory(user_id),
            remove_from_group_factory(user_id),
            private_db_query_factory(self.model, self.private_db, PRIVATE_AQL_GENERATION_PROMPT),
            
            # Food ordering tools
            place_order_factory(user_id),
            public_dish_search_factory(user_id, self.model, self.public_db, FOOD_PRIVATE_AQL_PROMPT),
            
            # Dineout tools
            book_dineout_factory(user_id),
            
            # Email tools
            send_email_factory(user_id),
            reply_to_email_factory(user_id),
            forward_email_factory(user_id),
            create_folder_factory(user_id),
            move_email_factory(user_id),
            
            # Slack tools
            create_channel_factory(user_id),
            leave_channel_factory(user_id),
            add_to_channel_factory(user_id),
            remove_from_channel_factory(user_id),
            set_channel_topic_factory(user_id),
            slack_send_message_factory(user_id, slack_username),
            set_status_factory(user_id),
            set_status_with_time_factory(user_id),
            text_to_nx_algorithm_for_public_db_factory(self.model, self.public_db.db, self.public_db.db.graph("restaurants"), self.public_db.schema)
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
        Run the Slack agent in an interactive loop, allowing users to chat with the agent.
        Press Ctrl+C to exit the loop.
        
        Args:
            debug: If True, shows detailed message stream for debugging
        """
        import markdown
        from rich.console import Console
        from rich.markdown import Markdown
        
        console = Console()
        
        console.print(Markdown("# AI Assistant Interactive Mode"))
        console.print(Markdown("Type your messages below. Press Ctrl+C to exit."))
        console.print(Markdown("---"))
        
        try:
            while True:
                user_input = input("\nYou: ")
                if not user_input.strip():
                    continue
                    
                console.print("Processing...", style="italic")
                
                if debug:
                    config = {"configurable": {"thread_id": thread_id}}
                    stream_mode = "values"

                    # # Check if there's an ongoing PregelTask that needs user input
                    if safely_check_interrupts(self.agent_graph, config):
                        inputs = Command(resume={"answer": user_input})
                    else:
                        inputs = {"messages": [HumanMessage(content=user_input)]}
                    
                    for stream in self.agent_graph.stream(inputs, config, stream_mode=stream_mode):
                        message = stream["messages"][-1]
                        if isinstance(message, tuple):
                            console.print(str(message))
                        else:
                            message.pretty_print()
                    
                    response = stream["messages"][-1].content
                else:
                    response = self.call_llm(user_input, thread_id)
                
                console.print("\nAssistant:", style="bold")
                console.print(Markdown(response))
                
        except KeyboardInterrupt:
            console.print("\n\nExiting Assistant. Goodbye!", style="bold green")
        except Exception as e:
            console.print(f"\nAn error occurred: {str(e)}", style="bold red")

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
    
    # Create and run the WhatsApp agent
    agent = MainAgent(
        model=LLMManager.get_openai_model(model_name="gpt-4o"),
        private_db=private_db,
        public_db=public_db,
        checkpointer=memory,
        confirmation_callback=lambda x: print("Agent Asked for confirmation: ", x)
    )
    agent.run_interactive(thread_id=str(uuid.uuid4()), debug=True)
