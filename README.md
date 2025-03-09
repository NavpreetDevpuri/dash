# Dash - AI-Powered Personal Agent System

> The future is personal agents, and Dash is one of them. It gives you an AI assistant that books restaurants, orders food, and manages communications by filtering spam and prioritizing urgent messages.

An AI-powered platform where each user gets their own personalized agents, designed to blend natural language conversations with dynamic knowledge graph interactions. Each user's personal agent provides a modern, real-time conversational experience while integrating advanced multi-agent reasoning, graph database querying, and automated ingestion of external data sources.

## 📌 Project Overview

### Inspiration

In today's digital world, we're drowning in information across dozens of platforms while juggling countless tasks. What if everyone had their own personal AI agent - not just another chatbot, but a truly personalized assistant that remembers everything about you, learns your preferences, and takes meaningful actions on your behalf? Dash was born from this vision of AI that works for you, understands you, and evolves with you - creating a future where personal agents transform how we interact with technology and manage our digital lives.

### What it does

Dash provides each user with their own personalized AI agent with powerful capabilities:

- **Personalized Memory & Understanding**: Each agent maintains a persistent memory of user preferences and past interactions using a private knowledge graph database.

- **Intelligent Communication Management**: Dash monitors incoming messages across email, WhatsApp, and Slack, automatically categorizing them as spam, important, or urgent, and sending appropriate notifications.

- **Action-Taking Capabilities**: Agents can perform tasks through integrated services, such as booking restaurants through Dineout, ordering food from delivery services, and sending emails (with draft confirmation).

*Note: Currently, all API integrations (WhatsApp, Slack, email, Dineout, food ordering) are implemented as mock services for development purposes, not connected to real external APIs.*

## 🚀 Features

- **Personalized AI Agents for Each User**
  - Every user gets their own dedicated AI assistant
  - Personal agents with user-specific memory and preferences
  - Action-taking capabilities through mock service integrations

- **Conversational AI with Memory & Action Capabilities**
  - Multi-turn conversations using interchangeable LLMs
  - Support for both question answering and action-taking
  - Context-aware responses with historical conversation tracking
  
- **Knowledge Graph Integration**
  - Natural language queries translate to secure AQL queries
  - Per-user private database alongside a shared, read-only common DB
  - Dynamic relationship mapping between entities
  
- **Real-Time Interaction**
  - WebSocket-based real-time updates and "thinking" indicators
  - Low-latency bidirectional communication
  
- **Intelligent Message Prioritization**
  - Automatic detection of spam, important, and urgent messages/emails
  - Smart notification system based on message priority
  - User-configurable priority thresholds and notification preferences
  
- **Consumer Agents for External Data**
  - Monitor external message sources (emails, Slack, WhatsApp, etc.)
  - Automated data ingestion and processing
  
- **Admin Simulation Interface (Blockly)**
  - Simulate external events using a graphical interface
  - Test system behavior with controlled inputs

## 🔄 Current API Integrations

The system currently uses dummy/mock implementations for the following service integrations:

- **Messaging Services**: WhatsApp, Slack, Email (simulated communication)
- **Food Services**: Restaurant bookings (Dineout), Food ordering
- **Productivity**: Calendar, Contacts, Email drafting
- **Notifications**: Push notifications, Priority alerts, Message categorization

These simulated integrations allow for development and testing of the agent logic without requiring actual connections to external services.

## 🛠️ Technical Stack

- **Frontend**: 
  - ReactJS with Material UI (in progress)
  - WebSocket client for real-time updates
  - Responsive design for multiple device types

- **Backend**: 
  - Flask Python framework
  - LangChain and LangGraph for AI agent orchestration
  - Flask-SocketIO for WebSocket communication

- **Database**: 
  - ArangoDB for graph-based data storage
  - Separate database environments for development, testing, and production

- **Testing**:
  - Comprehensive Python test suite
  - End-to-end testing for critical user flows

## 🧩 How I Built It

- **Agent Framework**: Core intelligence uses LangChain and LangGraph to orchestrate complex reasoning flows, allowing the agent to determine when to query databases and when to take actions.

- **Knowledge Storage**: I implemented ArangoDB as a graph database, with each user getting their own private database (`user_{user_id}`) alongside access to a shared, read-only `common_db`. This architecture provides a secure way to have multiple users while ensuring they can't access each other's data.

- **Consumer Agents**: Specialized Celery-based agents monitor external message sources, using LLMs to extract relevant identifiers and update the knowledge graph. These agents also analyze messages to classify them as spam, important, or urgent, sending appropriate notifications to users.

## 🧗 Challenges I Ran Into

1. **Getting data for the agent**
   - Solution: Obtained sample restaurant data from www.foodspark.io after contacting them.

2. **How to have ArangoDB database sharing by all users while maintaining data privacy**
   - Solution: Created a private database and user in ArangoDB for each Dash user. Like password hashes, I store these DB credentials in the _system database which only my backend can access. Additionally, I have a common database with read access for everyone containing restaurant data, dishes, prices, and ratings.

3. **Limited support for defining custom nodes and edges when importing data**
   - Solution: Wrote a custom importer with parallelization to import exponentially faster while maintaining proper node types and connections.

4. **Lack of resources for low-level design of personal agent systems**
   - Solution: After creative thinking, developed a design using LangChain, LangGraph, and Celery. Determined which prompts work effectively and how a personal agent should be implemented to be flexible for extensions and scalable.

5. **UI development challenges as a backend developer**

6. **Finding the most cost-effective and scalable agent implementation**
   - Solution: Kept prompts concise and removed unnecessary LLM calls. Modified ArangoGraphQAChain to support turning off LLM QA generation when only raw AQL query output is needed.

7. **Running LLM-generated code securely and efficiently**
   - Solution: Implemented a sandbox execution environment using Docker with Jupyter notebooks, with one cell loading the database into NetworkX and another cell for model-generated code.

8. **Limiting events and tools to the user level**
   - Solution: Implemented a factory design pattern where all tools and agents are generated for each user based on user ID, providing access only to that user's private database.

## 🏆 Accomplishments

I'm proud of my creative problem-solving approach, finding innovative solutions to challenging technical problems. From database isolation techniques to secure code execution, I've developed a robust architecture that separates user data while maintaining shared knowledge. My optimization of LLM usage and custom importers demonstrates my commitment to building not just a functional system, but one that can scale efficiently.

## 📚 What I Learned

Through developing Dash, I gained deep expertise in agentic frameworks like LangChain and LangGraph, effective prompt engineering techniques, and UI development basics. Most importantly, I discovered the power of ArangoDB as a graph database solution, which has become my favorite database technology for its flexibility and performance in knowledge graph applications.

## 📋 Requirements

- Python 3.9+
- Node.js 16+
- ArangoDB 3.9+
- Docker and Docker Compose (optional, but recommended)

## 🚀 Getting Started

### Using Docker (Recommended)

1. Clone the repository:
   ```
   git clone <repository-url>
   cd dash
   ```

2. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ARANGO_URL=http://localhost:8529
   ARANGO_DB_NAME=dash
   ARANGO_USERNAME=root
   ARANGO_PASSWORD=your_password
   ```

3. Start the application using Docker Compose:
   ```
   cd backend
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up ArangoDB:
   - Install ArangoDB from [official website](https://www.arangodb.com/download/)
   - Create a database named "dash"
   - Set up a user with appropriate permissions

5. Update `.env` file with your database credentials and API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ARANGO_URL=http://localhost:8529
   ARANGO_DB_NAME=dash
   ARANGO_USERNAME=root
   ARANGO_PASSWORD=your_password
   ```

6. Run the application:
   ```
   python run.py
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```

4. Access the application at http://localhost:3000

## 🧩 Project Structure

```
dash/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agents
│   │   ├── consumer_agents/ # External data processors
│   │   ├── models.py        # Database models
│   │   ├── routes/          # API endpoints
│   │   └── __init__.py      # App initialization
│   ├── migrations/          # Database migrations
│   ├── tests/               # Python test suite
│   ├── run.py               # Entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts
│   │   ├── pages/           # Page components
│   │   ├── services/        # API and WebSocket services
│   │   └── App.js           # Main app component
│   ├── package.json         # Node.js dependencies
└── README.md                # This file
```

## 📝 Development Roadmap

1. ✅ Basic chat functionality with LangGraph integration
2. ✅ Knowledge graph integration with ArangoDB
3. ✅ Consumer agents for external data sources
4. ⬜ Admin simulation interface with Blockly
5. ⬜ Comprehensive test coverage
6. ⬜ Production deployment pipeline
7. ⬜ Frontend implementation with React and Material UI

## 🔭 What's Next for Dash

I plan to continue development during weekends and free time, focusing on implementing the UI, improving various tools, and exploring different approaches to writing agents. My goal is to steadily enhance Dash's capabilities while maintaining its core vision of providing truly personal AI agents that understand and act according to each user's unique needs and preferences.

## 🔧 Development Guidelines

- Keep code files under 300 lines to maintain readability
- Write tests for all major functionality
- Follow environment-specific configurations for dev, test, and prod
- Avoid data mocking in production code
- Prefer simple solutions and avoid code duplication

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details. 