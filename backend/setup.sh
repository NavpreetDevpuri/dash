#!/bin/bash

# Setup script for the Consumer Agents backend
# This script installs dependencies and prepares the environment

# ANSI color codes for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Chat System Setup...${NC}"

# Check if Python 3 is installed
if command -v python3 &>/dev/null; then
    echo -e "${GREEN}Python 3 is installed.${NC}"
else
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if pip is installed
if command -v pip3 &>/dev/null; then
    echo -e "${GREEN}pip is installed.${NC}"
else
    echo -e "${RED}Error: pip is not installed. Please install pip and try again.${NC}"
    exit 1
fi

# Check if Docker is installed
if command -v docker &>/dev/null; then
    echo -e "${GREEN}Docker is installed.${NC}"
else
    echo -e "${YELLOW}Warning: Docker is not installed. It is recommended for running ArangoDB.${NC}"
    echo -e "${YELLOW}Please install Docker and Docker Compose for the complete environment.${NC}"
fi

# Check if Docker Compose is installed
if command -v docker-compose &>/dev/null; then
    echo -e "${GREEN}Docker Compose is installed.${NC}"
else
    echo -e "${YELLOW}Warning: Docker Compose is not installed. It is required for the development environment.${NC}"
    echo -e "${YELLOW}Please install Docker Compose.${NC}"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment. Is python installed?${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install dependencies
echo -e "${GREEN}Installing Python requirements...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p instance
echo -e "${GREEN}Directories created.${NC}"

# Set up .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${GREEN}Creating .env file...${NC}"
    echo "OPENAI_API_KEY=" > .env
    echo -e "${YELLOW}Please add your OpenAI API key to the .env file.${NC}"
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Start the database with Docker Compose
echo -e "${GREEN}Starting ArangoDB with Docker Compose...${NC}"
docker-compose up -d arangodb

# Wait for ArangoDB to be ready
echo -e "${GREEN}Waiting for ArangoDB to be ready...${NC}"
sleep 10

# Initialize the database
echo -e "${GREEN}Initializing database...${NC}"
python -c "from app import create_app; create_app()"

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${GREEN}To start the backend server, run: python run.py${NC}"
echo -e "${GREEN}To start the frontend server, navigate to the frontend directory and run: npm install && npm start${NC}"
echo -e "${YELLOW}Make sure you have added your OpenAI API key to the .env file.${NC}"
echo -e "${GREEN}To use the standalone test script without Celery:${NC}"
echo -e "python -m app.consumer_agents.test_consumer_standalone"
echo -e "${GREEN}To run the full application:${NC}"
echo -e "flask run"
echo -e "${GREEN}To run with Docker:${NC}"
echo -e "docker-compose up" 