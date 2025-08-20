#!/bin/bash

echo "Starting Job Board Voice Application..."
echo "======================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env and add your Elevenlabs credentials"
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Build and start services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "Service Status:"
echo "---------------"
docker-compose ps

echo ""
echo "Testing connections..."
echo "---------------------"

# Test Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Connected"
else
    echo "✗ Failed"
fi

# Test Backend
echo -n "Backend API: "
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

# Test MCP Server
echo -n "MCP Server: "
if curl -s http://localhost:3000/sse 2>/dev/null | head -1 | grep -q "event:"; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

# Test Frontend
echo -n "Frontend: "
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

echo ""
echo "======================================="
echo "Application URLs:"
echo "- Job Board: http://localhost:3001"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- MCP Server: http://localhost:3000/sse"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop all: docker-compose down"
echo "======================================="