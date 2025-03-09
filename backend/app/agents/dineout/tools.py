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
    

def book_dineout_factory(user_id: str):
    """Factory function to create a restaurant booking tool"""
    
    @tool
    def book_dineout(restaurant_name: str, booking_time: str, party_size: Optional[int] = 2, special_requests: Optional[str] = None) -> str:
        """
        Book a reservation at a restaurant.
        
        Args:
            restaurant_name: The name of the restaurant to book
            booking_time: The date and time for the reservation (e.g., "2023-05-20 19:00")
            party_size: Number of people in the party (default: 2)
            special_requests: Any special requests for the reservation (optional)
                
        Returns:
            Confirmation message for the booking
        """
        print(f"TOOL EXECUTION - BOOK DINEOUT:")
        print(f"USER ID: {user_id}")
        print(f"RESTAURANT: {restaurant_name}")
        print(f"TIME: {booking_time}")
        print(f"PARTY SIZE: {party_size}")
        print(f"SPECIAL REQUESTS: {special_requests}")
        
        # Generate a mock confirmation number
        import random
        confirmation_code = f"DINEOUT-{random.randint(10000, 99999)}"
        
        # Create a response with the booking details
        booking_details = {
            "status": "confirmed",
            "restaurant_name": restaurant_name,
            "booking_time": booking_time,
            "party_size": party_size,
            "special_requests": special_requests,
            "confirmation_code": confirmation_code,
            "user_id": user_id
        }
        
        return f"Your reservation at {restaurant_name} for {party_size} people on {booking_time} has been confirmed. Confirmation code: {confirmation_code}"
    
    return book_dineout 


def private_db_query_factory(model, arango_graph, aql_generation_prompt):
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
        It have user likes and dislikes about restaurants.
        """
        result = chain.invoke(query)
        return result
    
    return private_db_query
