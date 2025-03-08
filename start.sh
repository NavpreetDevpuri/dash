#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting AI Chat System...${NC}"

# Check if docker-compose is available
if command -v docker-compose &>/dev/null; then
    echo -e "${GREEN}Starting services with Docker Compose...${NC}"
    cd backend
    docker-compose up -d
    
    echo -e "${GREEN}Services started successfully!${NC}"
    echo -e "${YELLOW}Access the application at:${NC}"
    echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
    echo -e "${GREEN}Backend API: http://localhost:5000${NC}"
    echo -e "${GREEN}ArangoDB UI: http://localhost:8529${NC}"
    
    echo -e "\n${YELLOW}Press Ctrl+C to stop all services...${NC}"
    # Keep the script running to easily stop services with Ctrl+C
    read -r -d '' _ </dev/tty
    
    echo -e "\n${GREEN}Stopping services...${NC}"
    docker-compose down
else
    echo -e "${YELLOW}Docker Compose not found. Starting services manually...${NC}"
    
    # Start the backend
    echo -e "${GREEN}Starting backend...${NC}"
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Virtual environment not found. Running setup.sh first...${NC}"
        ./setup.sh
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start backend in the background
    echo -e "${GREEN}Starting Flask backend...${NC}"
    python run.py &
    BACKEND_PID=$!
    
    # Start frontend
    echo -e "${GREEN}Starting frontend...${NC}"
    cd ../frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}node_modules not found. Running npm install...${NC}"
        npm install
    fi
    
    # Start frontend
    npm start &
    FRONTEND_PID=$!
    
    echo -e "${GREEN}Services started successfully!${NC}"
    echo -e "${YELLOW}Access the application at:${NC}"
    echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
    echo -e "${GREEN}Backend API: http://localhost:5000${NC}"
    
    echo -e "\n${YELLOW}Press Ctrl+C to stop all services...${NC}"
    
    # Trap Ctrl+C and kill the processes
    trap "echo -e '\n${GREEN}Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
    
    # Wait for Ctrl+C
    wait
fi 