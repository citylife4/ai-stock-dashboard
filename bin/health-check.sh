#!/bin/bash

# AI Stock Dashboard Health Check Script
# This script checks if all Docker services are running correctly

echo "🔍 AI Stock Dashboard Health Check"
echo "=================================="

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not available"
    exit 1
fi

# Check if containers are running
echo "📋 Checking container status..."
CONTAINERS=(
    "ai-stock-dashboard-mongodb"
    "ai-stock-dashboard-backend" 
    "ai-stock-dashboard-frontend"
)

for container in "${CONTAINERS[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$container"; then
        echo "✅ $container: Running"
    else
        echo "❌ $container: Not running"
    fi
done

echo ""
echo "🏥 Checking service health..."

# Check MongoDB
echo -n "🗃️  MongoDB: "
if docker exec ai-stock-dashboard-mongodb mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Backend API
echo -n "🔧 Backend API: "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy or unreachable"
fi

# Check Frontend
echo -n "🌐 Frontend: "
if curl -s -f http://localhost:80 > /dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy or unreachable"
fi

echo ""
echo "📊 Service URLs:"
echo "   Frontend: http://localhost:80"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"

echo ""
echo "🔧 To view logs, run:"
echo "   docker compose logs -f [service_name]"
echo ""
echo "Health check complete! 🎯"