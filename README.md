# Dash - AI-Powered Personal Agent System

An AI-powered platform where each user gets their own personalized agents, designed to blend natural language conversations with dynamic knowledge graph interactions. Each user's personal agent provides a modern, real-time conversational experience while integrating advanced multi-agent reasoning, graph database querying, and automated ingestion of external data sources.

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
  - ReactJS with Material UI
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