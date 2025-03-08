# AI-Powered Chat System – Product Requirements Document (PRD)

## 1. Overview

### 1.1 Purpose  
The system is an AI-powered chat platform designed to blend natural language conversations with dynamic knowledge graph interactions. It provides a modern, real-time conversational experience while integrating advanced multi-agent reasoning, graph database querying, and automated ingestion of external data sources (emails, Slack, WhatsApp, etc.). The solution is composed of a ReactJS/Material UI front end and a Flask back end using LangGraph for orchestrating various agent flows. Additionally, the system supports full migrations (creating necessary schemas and an initial admin user) and provides a unique admin simulation interface based on Blockly.

### 1.2 Goals  
- **Conversational AI with Memory & Action Capabilities:**  
  - Support multi-turn conversations using interchangeable LLMs managed via an LLM Manager.  
  - Allow agents to answer queries and also take actions like ordering dishes, booking restaurants, sending emails (with draft confirmation), saving contacts, and proactively suggesting reminders (e.g., “Your uncle’s birthday is coming up…”).
- **Knowledge Graph Integration:**  
  - Translate natural language queries into secure AQL queries via LangChain’s ArangoGraphQAChain against an ArangoDB graph.  
  - Each user is provisioned with a dedicated private database (`user_{user_id}`) for personal data (read-write) alongside a shared, read-only `common_db`.
- **Real-Time Interaction:**  
  - Deliver real-time updates and “thinking” indicators via WebSockets.
- **Consumer Agents for External Data:**  
  - Use Celery-based consumer agents to monitor a queue for incoming messages from external channels (emails, Slack, WhatsApp, etc.).  
  - Each agent extracts identifiers from external messages (using LLM prompts), consults a cache, and updates the graph.  
  - Agents also send clarification requests to users if ambiguities are detected.
- **Admin Simulation Interface (Blockly):**  
  - Provide an admin-only UI page that uses Google Blockly to simulate external events.  
  - Blocks represent external sources (email, Slack, calendar events), include “sleep” blocks with adjustable delays, and feature input blocks for additional data (like email CC, event attendees, etc.).  
  - A “Generate Sample” option is available where the admin provides a text prompt describing what they want to simulate; an AI generates the complete simulated event (an array of objects) which is then rendered as Blockly blocks.
- **Rapid Development & Deployment:**  
  - Use ReactJS/Material UI and Flask with extensive package usage to speed up development.  
  - Deploy the system in Docker containers (targeting cloud providers like AWS) with simple migration strategies.

---

## 2. System Architecture

### 2.1 High-Level Components

- **Frontend (ReactJS + Material UI):**  
  - **Chat Interface:**  
    - Displays conversation messages with support for custom types (e.g., lists of dishes, restaurant details).  
    - Includes real-time “thinking” indicators sent via WebSockets.
  - **Notification Bar:**  
    - Pinned notifications and recent conversations.
  - **Settings Page:**  
    - Manage API keys, memories, contacts, and agent configuration.
  - **Admin Simulation Interface (Blockly):**  
    - Exclusive page for the admin user that displays a Blockly workspace.  
    - Admin can simulate external events by dragging and dropping blocks that represent sources (email, Slack, calendar), delays (sleep blocks with adjustable seconds), and input fields (e.g., CC, event attendees).  
    - A “Generate Sample” option allows the admin to provide a text prompt; the AI then generates a complete sample event (e.g., an email or calendar invitation) that is rendered as an array of Blockly blocks.
  - **Search Functionality:**  
    - Search bar to filter conversation history and highlight matching messages.

- **Backend (Flask + LangGraph):**  
  - **API Endpoints & WebSocket Server:**  
    - Secure JWT-based endpoints for registration, login, conversation management, settings, and notifications.
  - **LangGraph Agent:**  
    - Core conversational engine that uses an agent graph to route incoming messages through various nodes.  
    - Nodes include LLM calls, AQL query tools (via ArangoGraphQAChain), and action agents.
  - **Consumer Agents:**  
    - Celery workers that monitor an external message queue.  
    - They extract identifiers from external messages using prompt-based LLM queries, update the graph (using sandboxed tools and caching), and send clarification or urgent notifications.
  - **Action Agents:**  
    - Specialized agents that can perform tasks such as ordering dishes, booking restaurants, sending email drafts (with user confirmation), and saving or retrieving contact details.  
    - They also proactively suggest actions (e.g., reminders for birthdays or anniversaries) based on conversation context.

- **ArangoDB Databases:**  
  - **common_db (Read-Only):**  
    - Shared knowledge graph containing collections and graph schemas (e.g., restaurants, cuisines, common contacts).
  - **user_{user_id} (Read-Write):**  
    - Dedicated per-user databases created upon registration for personal data, conversation history, and consumer agent updates.

- **LLM Provider APIs:**  
  - **LLM Manager:**  
    - Abstracts access to interchangeable LLM providers (e.g., OpenAI, Anthropic) via LangChain wrappers.

- **Migration & Administration:**  
  - **Initial Migrations:**  
    - Scripts to create necessary database schemas, collections, and graphs in ArangoDB.  
    - Create an initial admin user and any required default configuration data.
  - **Admin Simulation Interface (Blockly):**  
    - Enables simulation of external messages/events.  
    - “Generate Sample” option: Admin provides a text prompt, and the AI generates a complete simulated event payload, which is then rendered as Blockly blocks.

### 2.2 Data Flow Overview

1. **User Interaction Flow:**  
   - The user sends a chat message via the React UI.  
   - The message is routed through the Flask API (using REST or WebSocket) to the LangGraph agent, which may invoke the LLM, run an AQL query against ArangoDB (either on `common_db` or `user_{user_id}`), or trigger an action agent.  
   - Real-time “thinking” and final responses are streamed back over WebSocket and rendered in the chat interface.

2. **External Data Ingestion Flow (Consumer Agents):**  
   - External sources push messages into the Celery queue.  
   - Consumer agents pick up the messages, extract identifiers via LLM prompts, consult a cache to avoid duplicates, and update the ArangoDB graph.  
   - If ambiguity is detected (e.g., multiple matching identifiers), the agent sends a clarification request to the user via WebSocket.

3. **Admin Simulation Flow:**  
   - The admin accesses the dedicated simulation page and uses Blockly to create simulation scenarios.  
   - Admin may manually arrange blocks or use the “Generate Sample” option by providing a text prompt.  
   - The AI then generates a full simulated event (an array of objects representing an email, Slack message, etc.), which is rendered as Blockly blocks in the interface.  
   - The simulation can then be “run,” injecting the event into the system for testing consumer agents and overall data ingestion.

---

## 3. Detailed Component Design

### 3.1 Frontend Design (ReactJS & Material UI)

#### Chat Interface & Real-Time UX  
- **Conversation Area:**  
  - Render chat messages with components that differentiate message types.  
  - Support interactive elements (e.g., clickable buttons for ordering or booking).
- **Input & Voice-to-Text:**  
  - Provide a text input with an integrated voice-to-text option.
- **Notification Bar:**  
  - A side panel showing pinned notifications and recent conversations.
- **Search Functionality:**  
  - A search bar filters messages and highlights matches.
- **Admin Simulation Interface (Blockly):**  
  - Accessible only to the admin user.  
  - Uses the Google Blockly library to create a workspace with blocks representing:
    - **Source Blocks:** Email, Slack, Calendar event.
    - **Sleep Blocks:** Delay blocks with adjustable seconds.
    - **Input Blocks:** For email CC, event attendees, subjects, message content, etc.
  - **Generate Sample Option:**  
    - Admin inputs a text prompt describing the desired simulated event (e.g., “Generate an email invitation for a birthday party with CC to my manager”).  
    - The AI processes the prompt and returns a complete simulated event payload (an array of JSON objects).  
    - This payload is rendered as a series of Blockly blocks in the workspace, allowing further manipulation before injection into the system.
  
#### State Management and Integration  
- **Global State:**  
  - Use React Context or Redux for managing authentication, conversation state, and admin simulation state.
- **WebSocket Integration:**  
  - Use a library (e.g., socket.io-client) to maintain a WebSocket connection for real-time updates.
- **Material UI Theming:**  
  - Utilize Material UI’s theming system to provide a modern, responsive interface.

---

### 3.2 Backend Design (Flask, LangGraph, & Celery)

#### API Endpoints  
- **User & Authentication:**  
  - `POST /api/register`: Register a new user, trigger migration scripts to create `user_{user_id}`, and return a JWT.
  - `POST /api/login`: Authenticate user and issue a JWT.
- **Conversation Management:**  
  - `GET /api/conversations`: Retrieve conversation list.
  - `POST /api/conversations/{id}/messages`: Submit a new message to be processed by the LangGraph agent.
  - `GET /api/search`: Search conversation history.
- **Settings:**  
  - `POST /api/settings`: Update user settings (API keys, memories, contacts, etc.).
- **Notifications:**  
  - `GET /api/notifications`: Retrieve system notifications.
- **Admin & Migrations:**  
  - An endpoint or CLI command to run initial migrations (creating schemas, collections, graphs, and an admin user).
  - `GET /api/admin`: (Admin-only) Access admin configuration data and simulation controls.
- **Simulation Injection:**  
  - An endpoint to accept simulated events from the admin simulation interface (e.g., POST simulated event payload).

#### LangGraph Agent and Action Agents  
- **Core Agent (Gateway Agent):**  
  - Receives the user message, extracts metadata (using a schema like `GatewayMetaSchema`), and routes the message to specialized agents.
- **Action Agents:**  
  - **Order Dishes:** Processes food orders and confirms with the user.
  - **Book Restaurant:** Manages restaurant booking inquiries.
  - **Send Email:** Drafts emails and waits for user confirmation before sending.
  - **Save Contact:** Updates or creates contact entries.
  - **Proactive Suggestion Agent:** Suggests reminders or related actions (e.g., “Your uncle’s birthday is next month—should we plan a celebration?”).

#### Database Integration (ArangoDB)  
- **ArangoGraphQAChain:**  
  - Configured for secure query execution against `common_db` and `user_{user_id}`.
  - Example initialization:
    ```python
    chain = ArangoGraphQAChain.from_llm(
        llm=llm_instance,
        graph=arango_graph,
        verbose=True,
        allow_dangerous_requests=False
    )
    ```
- **Migrations:**  
  - Initial migration scripts create the necessary database schemas, collections, graphs, and indexes.  
  - Create an initial admin user and populate default data.
  - Migration scripts are versioned and idempotent.

#### Consumer Agents (Celery Tasks)  
- **Celery Workers:**  
  - Monitor a message queue for external data (emails, Slack messages, etc.).
  - Process each message by:
    - Using an LLM prompt to extract identifiers.
    - Checking a cache (or Redis store) for duplicates.
    - Inserting or updating nodes and edges in the graph.
    - Triggering clarifications via WebSocket if needed.
- **Sample Consumer Task:**
  ```python
  from celery import Celery
  celery_app = Celery('consumer_agents', broker='redis://localhost:6379/0')

  @celery_app.task
  def process_external_message(channel, raw_message, user_id):
      from langchain_openai import ChatOpenAI
      llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
      prompt = f"Extract unique identifiers (emails, names, keywords) from this message:\n{raw_message}"
      extraction = llm.invoke([{"role": "user", "content": prompt}])
      identifiers = extraction.get("identifiers", [])
      
      cache_key = f"{user_id}_{channel}_identifiers"
      cached_ids = cache.get(cache_key, [])
      new_ids = [i for i in identifiers if i not in cached_ids]
      if new_ids:
          cache.set(cache_key, identifiers)
          for identifier in new_ids:
              safe_insert_identifier(user_id, identifier, channel)
              notify_user(user_id, f"Clarification needed for identifier: {identifier}")
      return {"status": "processed", "new_identifiers": new_ids}
  ```
  
#### WebSocket Integration  
- **Real-Time Updates:**  
  - Use Flask-SocketIO to emit events (e.g., “thinking”, tool usage, final responses, notifications) to clients.
  - Example:
    ```python
    from flask_socketio import SocketIO, emit, join_room
    socketio = SocketIO(app)

    @socketio.on('connect')
    def handle_connect():
        token = request.args.get('token')
        user_id = verify_token(token)
        join_room(user_id)
        emit('status', {'message': 'Connected'})
    
    def notify_user(user_id, message):
        socketio.emit('notification', {'message': message}, room=user_id)
    ```

---

### 3.3 Migrations and Initial Setup

#### Database Migrations  
- **Migration Scripts:**  
  - Run at application startup or via a CLI command.  
  - Create the `common_db` schema with its collections and graph definitions.  
  - Create per-user databases (`user_{user_id}`) upon registration.
  - Create an initial admin user.
  - Example pseudo-code:
    ```python
    def run_migrations():
        arango_client.create_database("common_db", if_not_exists=True)
        common_db = arango_client.db("common_db", username="admin", password="admin_pwd")
        # Create collections, indexes, and graphs here...
        
        if not admin_exists("admin"):
            create_admin_user("admin", "admin@example.com", hashed_password("password"))
        
        print("Migrations completed.")
    ```
  
#### Admin User & Interface  
- **Admin User:**  
  - Created during migrations; this user has access to a dedicated admin UI.
- **Blockly Simulation Interface:**  
  - Provides a visual Blockly workspace where simulation blocks are available.
  - **Generate Sample Option:**  
    - Admin inputs a text prompt describing the simulated event (e.g., “Generate an email invitation for a birthday party with CC to my manager”).
    - The system calls an AI service which returns a JSON payload representing the event.
    - The generated sample is rendered as a series of Blockly blocks, which the admin can then arrange or modify before running the simulation.
  - Simulation blocks include:
    - **Source Blocks:** Email, Slack, Calendar, etc.
    - **Sleep Blocks:** Delay blocks with an adjustable number of seconds.
    - **Input Blocks:** Custom fields for email CC, event attendees, subject, message content, etc.
  - When “Run Simulation” is triggered, the simulated event is injected into the system (via an API endpoint or directly into the Celery queue) for processing by consumer agents.

---

## 4. Security Considerations

- **Authentication:**  
  - All endpoints and WebSocket connections require JWT tokens.
- **Database Isolation:**  
  - Each user’s data is isolated in a dedicated ArangoDB database (`user_{user_id}`).
- **Sandboxed Execution:**  
  - Advanced queries (e.g., those using nx_arangodb) are executed in a sandbox with restricted access.
- **Injection Prevention:**  
  - LangChain and LangGraph tools are configured with `allow_dangerous_requests=False`.
- **Network Security:**  
  - Communications are secured over HTTPS/WSS with strict CORS.
- **Logging & Monitoring:**  
  - All actions are logged for audit and debugging purposes.

---

## 5. Deployment & Scaling

### 5.1 Containerization  
- **Docker:**  
  - Separate containers for the React front end, Flask back end (including LangGraph and WebSocket server), ArangoDB, and Celery workers.
  - Docker Compose for local development.

### 5.2 Deployment Environment  
- **Cloud Provider (e.g., AWS):**  
  - Deploy using AWS ECS/EKS or Fargate, with ArangoDB running in a secure VPC.
  
### 5.3 Scaling  
- Horizontal scaling is not required for version 1 but components are designed modularly for future scaling.

---

## 6. Example Use-Case Flows

### 6.1 End-to-End User Conversation  
1. **User Registration & Login:**  
   - A new user registers via `POST /api/register`; a new `user_{user_id}` is created and a JWT issued.
   - The user logs in via `POST /api/login`.
2. **Conversational Query:**  
   - The user types: “Order me a pepperoni pizza from my favorite restaurant.”
   - The LangGraph agent processes the message:
     - It calls the LLM to interpret intent.
     - Runs an AQL query via ArangoGraphQAChain to determine the restaurant from `common_db` or `user_{user_id}`.
     - Routes to the Order Dishes Agent which drafts an order and asks the user for confirmation.
   - Updates (“Agent is thinking…”) are streamed via WebSocket, and the final response is rendered interactively.
3. **Proactive Action Suggestion:**  
   - The user mentions, “My uncle is traveling next month.”
   - The agent retrieves related information (e.g., uncle’s birthday) and suggests: “Your uncle’s birthday is next month—should we plan a family dinner or send a congratulatory email?”

### 6.2 External Data Ingestion via Consumer Agents  
1. **External Event Arrival:**  
   - An email arrives and is pushed into the Celery queue.
2. **Processing:**  
   - A consumer agent extracts identifiers (emails, names, keywords) using an LLM prompt.
   - Checks the cache and updates the ArangoDB graph accordingly.
   - If ambiguity exists, a clarification request is sent to the user via WebSocket.

### 6.3 Admin Simulation Using Blockly  
1. **Access Simulation Interface:**  
   - The admin logs in and navigates to the simulation page.
2. **Generate Sample:**  
   - The admin enters a text prompt such as “Generate an email invitation for a birthday party with CC to my manager.”
   - The AI returns a simulated event payload, which is rendered as Blockly blocks in the workspace.
3. **Simulation & Injection:**  
   - The admin can rearrange the blocks, add sleep blocks (delays), and input custom fields.
   - When satisfied, the admin clicks “Run Simulation,” which injects the event into the system (via an API or direct Celery queue insertion) for processing.

---

## 7. Low-Level Code Examples

### Flask JWT Middleware
```python
import jwt
from datetime import datetime, timedelta
from flask import request, jsonify

JWT_SECRET = "supersecretkey"

def create_jwt(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def jwt_required(fn):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            try:
                token = auth_header.split()[1]
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                request.user_id = payload["user_id"]
            except Exception as e:
                return jsonify({"error": "Invalid token"}), 401
        else:
            return jsonify({"error": "Missing token"}), 401
        return fn(*args, **kwargs)
    return wrapper
```

### Celery Consumer Task (Excerpt)
```python
from celery import Celery
celery_app = Celery('consumer_agents', broker='redis://localhost:6379/0')

@celery_app.task
def process_external_message(channel, raw_message, user_id):
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    prompt = f"Extract unique identifiers (emails, names, keywords) from this message:\n{raw_message}"
    extraction = llm.invoke([{"role": "user", "content": prompt}])
    identifiers = extraction.get("identifiers", [])
    
    cache_key = f"{user_id}_{channel}_identifiers"
    cached_ids = cache.get(cache_key, [])
    new_ids = [i for i in identifiers if i not in cached_ids]
    if new_ids:
        cache.set(cache_key, identifiers)
        for identifier in new_ids:
            safe_insert_identifier(user_id, identifier, channel)
            notify_user(user_id, f"Clarification needed for identifier: {identifier}")
    return {"status": "processed", "new_identifiers": new_ids}
```

### Admin Blockly Simulation Overview  
- **Blockly Workspace:**  
  - The admin UI page loads a Blockly workspace with a custom toolbox.  
  - Blocks include source blocks (Email, Slack, Calendar), sleep blocks (with adjustable delay), and input blocks (for CC, attendees, etc.).  
- **Generate Sample:**  
  - A “Generate Sample” button collects a text prompt from the admin (e.g., “Generate an email invitation for a birthday party with CC to my manager”).  
  - This prompt is sent to an AI service, which returns a JSON payload representing the simulated event.  
  - The JSON is then parsed and rendered as a series of Blockly blocks in the workspace.
- **Run Simulation:**  
  - Once the simulation blocks are arranged, clicking “Run Simulation” injects the event into the system (via an API endpoint or direct push to the Celery queue).

---

## 8. Conclusion

This comprehensive PRD defines a robust, multi-agent AI chat system that:
- Provides interactive, real-time conversation with context, memory, and proactive suggestions.
- Integrates secure, dynamic querying of a knowledge graph via ArangoDB using LangChain and LangGraph.
- Ingests external data through consumer agents that monitor a Celery queue, extracting identifiers and updating the graph.
- Supports action-oriented tasks (ordering, booking, emailing, saving contacts) and proactive notifications.
- Includes a full migration process to initialize databases (with an initial admin user) and an exclusive admin interface featuring a Blockly Simulation Interface. The simulation interface allows the admin to generate sample events via AI by providing an input prompt, which is then rendered as Blockly blocks for simulation and testing.
- Is built using rapid development frameworks (ReactJS with Material UI, Flask) and containerized for deployment in cloud environments.

This design meets current requirements and is structured to allow future enhancements while ensuring a secure, scalable, and user-friendly system.

