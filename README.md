# Dash - AI-Powered Chat System

An AI-powered chat platform designed to blend natural language conversations with dynamic knowledge graph interactions. It provides a modern, real-time conversational experience while integrating advanced multi-agent reasoning, graph database querying, and automated ingestion of external data sources.

## 🚀 Features

- **Conversational AI with Memory & Action Capabilities**
  - Multi-turn conversations using interchangeable LLMs
  - Support for both question answering and action-taking
  
- **Knowledge Graph Integration**
  - Natural language queries translate to secure AQL queries
  - Per-user private database alongside a shared, read-only common DB
  
- **Real-Time Interaction**
  - WebSocket-based real-time updates and "thinking" indicators
  
- **Consumer Agents for External Data**
  - Monitor external message sources (emails, Slack, WhatsApp, etc.)
  
- **Admin Simulation Interface (Blockly)**
  - Simulate external events using a graphical interface

## 🛠️ Technical Stack

- **Frontend**: ReactJS with Material UI
- **Backend**: Flask with LangGraph
- **Database**: ArangoDB
- **Communication**: WebSockets with Flask-SocketIO
- **AI Framework**: LangChain and LangGraph

## 📋 Requirements

- Python 3.9+
- Node.js 16+
- ArangoDB 3.9+
- Docker and Docker Compose (optional)

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
│   ├── run.py               # Entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── contexts/        # React contexts
│   │   ├── pages/           # Page components
│   │   └── App.js           # Main app component
│   ├── package.json         # Node.js dependencies
└── README.md                # This file
```

## 📝 Development Roadmap

1. ✅ Basic chat functionality with LangGraph integration
2. ⬜ Knowledge graph integration with ArangoDB
3. ⬜ Consumer agents for external data sources
4. ⬜ Admin simulation interface with Blockly

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details. 