#!/bin/bash

echo "🐳 Deploying GoatMeasure Pro with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create uploads directory
mkdir -p uploads

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Remove old images (optional)
read -p "🗑️  Remove old Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down --rmi all
fi

# Build and start containers
echo "🔨 Building and starting containers..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker compose ps

# Show logs
echo "📋 Recent logs:"
docker compose logs --tail=20

# Test the application
echo "🧪 Testing application..."
sleep 5

if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ GoatMeasure Pro is running successfully!"
    echo "🌐 Access your application at: http://goatmorpho.info"
    echo "📊 API health check: http://goatmorpho.info/api/health"
else
    echo "❌ Health check failed. Check logs:"
    docker compose logs app
fi

echo ""
echo "📚 Useful commands:"
echo "  View logs: docker compose logs -f app"
echo "  Restart:   docker compose restart"
echo "  Stop:      docker compose down"
echo "  Update:    git pull && docker compose up -d --build"