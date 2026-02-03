#!/bin/bash

# Telegram Bot Deployment Script for VPS
# This script deploys the bot to your VPS using Docker

set -e

echo "=========================================="
echo "Telegram Bot VPS Deployment"
echo "=========================================="

# Check if .env.bot exists
if [ ! -f .env.bot ]; then
    echo "❌ Error: .env.bot file not found!"
    echo "Please copy .env.bot.example to .env.bot and configure it."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed!"
    echo "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check for docker-compose or docker compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ Error: docker-compose is not installed!"
    echo "Please install docker-compose first."
    exit 1
fi

echo "✅ Prerequisites check passed (using $DOCKER_COMPOSE_CMD)"
echo ""

# Build the Docker image
echo "📦 Building Docker image..."
$DOCKER_COMPOSE_CMD -f docker-compose.bot.yml build

# Stop existing container if running
echo "🛑 Stopping existing container (if any)..."
$DOCKER_COMPOSE_CMD -f docker-compose.bot.yml down

# Start the bot
echo "🚀 Starting Telegram bot..."
$DOCKER_COMPOSE_CMD -f docker-compose.bot.yml up -d

# Show logs
echo ""
echo "✅ Bot deployed successfully!"
echo ""
echo "To view logs, run:"
echo "  $DOCKER_COMPOSE_CMD -f docker-compose.bot.yml logs -f"
echo ""
echo "To stop the bot, run:"
echo "  $DOCKER_COMPOSE_CMD -f docker-compose.bot.yml down"
echo ""
