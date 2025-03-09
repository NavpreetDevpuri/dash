import os
import sys

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.agents.email_agent.user_facing_agent import EmailAgent
from app.agents.foodorder.food_ordering_agent import FoodOrderingAgent
from app.agents.dineout.restaurant_agent import RestaurantAgent 
from app.agents.whatsapp.user_facing_agent import WhatsAppAgent
from app.agents.slack.user_facing_agent import SlackAgent

from app.common.llm_manager import LLMManager
from langchain_community.graphs import ArangoGraph
from arango import ArangoClient
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
import uuid

model = LLMManager.get_openai_model(model_name="gpt-4o")


# Create a direct sqlite connection instead of using SQLAlchemy
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

db_client = ArangoClient(hosts="http://localhost:8529")
private_db = ArangoGraph(db_client.db("user_1235", username="root", password="zxcv", verify=True))
public_db = ArangoGraph(db_client.db("common_db", username="root", password="zxcv", verify=True))

email_agent = EmailAgent(checkpointer=memory, model=model, private_db=private_db, public_db=public_db)
food_ordering_agent = FoodOrderingAgent(checkpointer=memory, model=model, private_db=private_db, public_db=public_db)
restaurant_agent = RestaurantAgent(checkpointer=memory, model=model, private_db=private_db, public_db=public_db)
whatsapp_agent = WhatsAppAgent(checkpointer=memory, model=model, private_db=private_db, public_db=public_db)
slack_agent = SlackAgent(checkpointer=memory, model=model, private_db=private_db, public_db=public_db)  

email_agent_as_tool = email_agent.agent_graph.as_tool(
    name="email_agent", 
    description="Email agent that can send emails, reply to emails, forward emails, create folders, move emails between folders, and query your email database. Use this for any email-related tasks including composing new messages, organizing your inbox, or searching through past correspondence."
)

food_ordering_agent_as_tool = food_ordering_agent.agent_graph.as_tool(
    name="food_ordering_agent", 
    description="Food ordering agent that can place food delivery orders from restaurants, search for dishes by name, ingredients, cuisine, or dietary preferences, and access your order history and food preferences. Use this for ordering meals for delivery to your location."
)

restaurant_agent_as_tool = restaurant_agent.agent_graph.as_tool(
    name="restaurant_agent", 
    description="Restaurant agent that can book reservations at restaurants, specify party size and special requests, and query your restaurant preferences and dining history. Use this when you want to make a reservation for dining out."
)

whatsapp_agent_as_tool = whatsapp_agent.agent_graph.as_tool(
    name="whatsapp_agent", 
    description="WhatsApp agent that can save contacts, send messages to individuals or groups, create new groups, leave groups, add or remove participants from groups, and search through your WhatsApp message history. Use this for any WhatsApp messaging needs."
)

slack_agent_as_tool = slack_agent.agent_graph.as_tool(
    name="slack_agent", 
    description="Slack agent that can create channels, leave channels, add or remove members from channels, set channel topics, send messages to channels or users, set your status with or without expiration times, and search through your Slack message history. Use this for any Slack-related communication tasks."
)


main_agent = create_react_agent(
    model=model,
    tools=[email_agent_as_tool, food_ordering_agent_as_tool, restaurant_agent_as_tool, whatsapp_agent_as_tool, slack_agent_as_tool],
    state_modifier="You are a helpful assistant that can help with email, food ordering, restaurant, whatsapp, and slack tasks.",
    checkpointer=memory
)



while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    inputs = {"messages": [HumanMessage(content=user_input)]}
    for stream in main_agent.stream(inputs, config, stream_mode="values"):
        message = stream["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
