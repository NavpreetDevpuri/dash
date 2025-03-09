import json
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from app.common.arangodb import ArangoGraphQAChain
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.db import get_system_db, get_user_db
from app.agents.foodorder.schemas import Dish

def place_order_factory(user_id: str):
    """Factory function to create a food ordering tool"""
    
    @tool
    def place_order(restaurant_name: str, dish_names: List[str], delivery_address: str, delivery_time: Optional[str] = None, payment_method: Optional[str] = "Credit Card", special_instructions: Optional[str] = None) -> str:
        """
        Place an order for food delivery from a restaurant.
        
        Args:
            restaurant_name: The name of the restaurant to order from
            dish_names: List of dish names to order
            delivery_address: The address for delivery
            delivery_time: Optional time for delivery (use "ASAP" for immediate delivery)
            payment_method: Payment method (default: "Credit Card")
            special_instructions: Any special instructions for the order or delivery
                
        Returns:
            Confirmation message for the order
        """
        print(f"TOOL EXECUTION - PLACE ORDER:")
        print(f"USER ID: {user_id}")
        print(f"RESTAURANT: {restaurant_name}")
        print(f"DISHES: {dish_names}")
        print(f"DELIVERY ADDRESS: {delivery_address}")
        print(f"DELIVERY TIME: {delivery_time or 'ASAP'}")
        print(f"PAYMENT METHOD: {payment_method}")
        print(f"SPECIAL INSTRUCTIONS: {special_instructions}")
        
        # Generate a mock order number
        import random
        order_number = f"ORDER-{random.randint(10000, 99999)}"
        
        # Create a response with the order details
        order_details = {
            "status": "confirmed",
            "restaurant_name": restaurant_name,
            "dishes": dish_names,
            "delivery_address": delivery_address,
            "delivery_time": delivery_time or "ASAP",
            "payment_method": payment_method,
            "special_instructions": special_instructions,
            "order_number": order_number,
            "user_id": user_id
        }
        
        dishes_str = ", ".join(dish_names)
        return f"Your order from {restaurant_name} for {dishes_str} has been confirmed. The food will be delivered to {delivery_address} {delivery_time or 'as soon as possible'}. Order number: {order_number}"
    
    return place_order


def public_dish_search_factory(model, arango_graph, aql_generation_prompt):
    """Factory function to create a tool for searching the public dish database"""
    chain = ArangoGraphQAChain.from_llm(
        llm=model,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=True,
        return_aql_result=True,
        perform_qa=False,
        top_k=5,
        aql_generation_prompt=aql_generation_prompt
    )
    
    @tool
    def public_dish_search(query: str) -> List[Dish]:
        """
        Search for dishes in the public database by name, ingredients, cuisine, dietary preferences, etc.
        
        Args:
            query: A descriptive query about the dishes to search for
                
        Returns:
            Information about matching dishes
        """
        result = chain.invoke(query)
        return result
    
    return public_dish_search


def private_db_query_factory(model, arango_graph, aql_generation_prompt):
    """Factory function to create a tool for querying the private user database"""
    chain = ArangoGraphQAChain.from_llm(
        llm=model,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=True,
        return_aql_result=True,
        perform_qa=False,
        top_k=5,
        aql_generation_prompt=aql_generation_prompt
    )
    
    @tool
    def private_db_query(query: str) -> str:
        """
        Query the private database for user preferences, order history, and past ratings.
        Use this to get information about the user's food preferences and order patterns.
        """
        result = chain.invoke(query)
        return result
    
    return private_db_query 