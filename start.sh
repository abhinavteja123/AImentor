#!/bin/bash

# AI Life Mentor - Quick Start Script for Linux/Mac

echo ""
echo "========================================"
echo "  AI Life Mentor - Docker Quick Start"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if .env file has been configured
if grep -q "your_deepseek_api_key_here" .env 2>/dev/null; then
    echo "WARNING: You need to configure your DeepSeek API key!"
    echo ""
    echo "Please edit the .env file and replace:"
    echo "  DEEPSEEK_API_KEY=your_deepseek_api_key_here"
    echo "with your actual API key from https://platform.deepseek.com/"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Step 1: Building Docker images..."
echo ""
docker-compose build

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed!"
    exit 1
fi

echo ""
echo "Step 2: Starting all services..."
echo ""
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start services!"
    exit 1
fi

echo ""
echo "Step 3: Waiting for services to be healthy..."
sleep 10

echo ""
echo "========================================"
echo "  All services are running!"
echo "========================================"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  PostgreSQL: localhost:5432"
echo "  MongoDB:    localhost:27017"
echo "  Redis:      localhost:6379"
echo ""
echo "To view logs:     docker-compose logs -f"
echo "To stop:          docker-compose down"
echo "To seed database: docker-compose exec backend python -m scripts.seed_database"
echo ""
