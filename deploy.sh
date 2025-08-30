#!/bin/bash

# AI Stock Dashboard Deployment Script
# This script helps with building and deploying new versions of the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_NAME="ai-stock-dashboard"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build           Build new images with version tag"
    echo "  deploy          Deploy the application (build and start)"
    echo "  update          Update running application with new code"
    echo "  restart         Restart all services"
    echo "  stop            Stop all services"
    echo "  logs            Show logs for all services"
    echo "  status          Show status of all services"
    echo "  cleanup         Clean up old images and containers"
    echo ""
    echo "Options:"
    echo "  -v, --version   Specify version tag (default: timestamp)"
    echo "  -s, --service   Specify service (backend, frontend, or all)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy -v v1.2.3"
    echo "  $0 update -s backend"
    echo "  $0 logs"
}

# Generate version tag
generate_version() {
    if [ -n "$VERSION" ]; then
        echo "$VERSION"
    else
        echo "v$(date +%Y%m%d-%H%M%S)"
    fi
}

# Build images
build_images() {
    local version="$1"
    local service="$2"
    
    print_status "Building images with version: $version"
    
    export VERSION="$version"
    
    if [ "$service" = "all" ] || [ "$service" = "backend" ]; then
        print_status "Building backend image..."
        docker-compose -f "$COMPOSE_FILE" build backend
        docker tag "${PROJECT_NAME}_backend:latest" "${PROJECT_NAME}_backend:$version"
    fi
    
    if [ "$service" = "all" ] || [ "$service" = "frontend" ]; then
        print_status "Building frontend image..."
        docker-compose -f "$COMPOSE_FILE" build frontend
        docker tag "${PROJECT_NAME}_frontend:latest" "${PROJECT_NAME}_frontend:$version"
    fi
    
    print_success "Images built successfully"
}

# Deploy application
deploy() {
    local version="$1"
    
    print_status "Deploying application with version: $version"
    
    # Stop existing services
    print_status "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    
    # Build new images
    build_images "$version" "all"
    
    # Start services
    export VERSION="$version"
    print_status "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    for i in {1..60}; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "unhealthy"; then
            echo -n "."
            sleep 2
        else
            break
        fi
    done
    echo ""
    
    print_success "Deployment completed"
    show_status
}

# Update existing deployment
update() {
    local service="$2"
    local version=$(generate_version)
    
    print_status "Updating $service with version: $version"
    
    # Build new images
    build_images "$version" "$service"
    
    # Stop and remove containers to avoid metadata conflicts
    export VERSION="$version"
    if [ "$service" = "all" ]; then
        print_status "Stopping and removing all containers..."
        docker-compose -f "$COMPOSE_FILE" stop
        docker-compose -f "$COMPOSE_FILE" rm -f
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        print_status "Stopping and removing $service container..."
        docker-compose -f "$COMPOSE_FILE" stop "$service"
        docker-compose -f "$COMPOSE_FILE" rm -f "$service"
        docker-compose -f "$COMPOSE_FILE" up -d "$service"
    fi
    
    print_success "Update completed"
    show_status
}

# Show status
show_status() {
    print_status "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    print_status "Service health:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$PROJECT_NAME" || true
}

# Show logs
show_logs() {
    local service="$1"
    if [ "$service" = "all" ] || [ -z "$service" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=50
    else
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=50 "$service"
    fi
}

# Cleanup old images
cleanup() {
    print_status "Cleaning up old images and containers..."
    
    # Remove old containers
    docker container prune -f
    
    # Remove old images (keep last 3 versions)
    print_status "Removing old images (keeping last 3 versions)..."
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | \
    grep "$PROJECT_NAME" | \
    tail -n +4 | \
    awk '{print $3}' | \
    xargs -r docker rmi -f
    
    # Remove unused volumes
    docker volume prune -f
    
    print_success "Cleanup completed"
}

# Parse command line arguments
VERSION=""
SERVICE="all"
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        build|deploy|update|restart|stop|logs|status|cleanup)
            COMMAND="$1"
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate service
if [ "$SERVICE" != "all" ] && [ "$SERVICE" != "backend" ] && [ "$SERVICE" != "frontend" ]; then
    print_error "Invalid service. Must be 'all', 'backend', or 'frontend'"
    exit 1
fi

# Execute command
case "$COMMAND" in
    build)
        version=$(generate_version)
        build_images "$version" "$SERVICE"
        ;;
    deploy)
        version=$(generate_version)
        deploy "$version"
        ;;
    update)
        update "$SERVICE"
        ;;
    restart)
        print_status "Restarting services..."
        docker-compose -f "$COMPOSE_FILE" restart
        print_success "Services restarted"
        show_status
        ;;
    stop)
        print_status "Stopping services..."
        docker-compose -f "$COMPOSE_FILE" down
        print_success "Services stopped"
        ;;
    logs)
        show_logs "$SERVICE"
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    "")
        print_error "No command specified"
        usage
        exit 1
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
