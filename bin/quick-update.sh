#!/bin/bash

# Quick update script for code changes
# This script updates the application with minimal downtime

set -e

echo "🚀 AI Stock Dashboard - Quick Update"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Run this script from the project root."
    exit 1
fi

# Get current git commit for versioning
VERSION="git-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

echo "📦 Building new images with version: $VERSION"

# Export version for docker-compose
export VERSION

# Build new images without cache to ensure latest code
echo "🔨 Building backend..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

echo "🔨 Building frontend..."
docker-compose -f docker-compose.prod.yml build --no-cache frontend

echo "🔄 Updating services..."
# Stop containers first to avoid metadata conflicts
docker-compose -f docker-compose.prod.yml stop backend frontend

# Remove containers to avoid metadata issues
docker-compose -f docker-compose.prod.yml rm -f backend frontend

# Restart services with new images
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Show logs for a few seconds
echo "📋 Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=10 backend frontend

echo "✅ Update completed!"
echo "🌐 Application should be available at:"
echo "   HTTP:  http://localhost:34197"
echo "   HTTPS: https://localhost:34198"
