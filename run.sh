#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting RAG Chatbot Services...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p logs

# Build and start services
echo -e "${GREEN}Building and starting services...${NC}"
docker-compose -f docker/docker-compose.yml up --build -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Initialize database
echo -e "${GREEN}Initializing database...${NC}"
docker-compose -f docker/docker-compose.yml exec -T api alembic upgrade head

echo -e "${GREEN}RAG Chatbot is running!${NC}"
echo -e "Web interface: ${YELLOW}http://localhost:8000${NC}"
echo -e "API documentation: ${YELLOW}http://localhost:8000/docs${NC}"

# Show logs
echo -e "${GREEN}Showing logs (Ctrl+C to exit)...${NC}"
docker-compose -f docker/docker-compose.yml logs -f 
