# Docker Deployment Guide

This guide explains how to deploy and update the AI Stock Dashboard using the improved Docker setup.

## Available Configurations

### 1. Development Setup (`docker-compose.dev.yml`)
- **Hot reload** enabled for both frontend and backend
- **Source code mounted** as volumes for instant updates
- **Exposed ports** for direct access (backend: 8000, frontend: 3000)
- **Debug mode** enabled

### 2. Production Setup (`docker-compose.prod.yml`)
- **Optimized builds** with multi-stage Dockerfiles
- **SSL/HTTPS** support
- **Health checks** for all services
- **Internal networking** (no exposed backend ports)
- **Versioned images** for rollback capability

## Quick Start

### Development Mode
```bash
# Start development environment with hot reload
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop
docker-compose -f docker-compose.dev.yml down
```

### Production Mode
```bash
# Deploy application
./deploy.sh deploy

# Or deploy with specific version
./deploy.sh deploy -v v1.2.3

# Quick update after code changes
./quick-update.sh
```

## Deployment Script Usage

The `deploy.sh` script provides comprehensive deployment management:

### Commands

- **`build`** - Build new images with version tags
- **`deploy`** - Full deployment (build + start)
- **`update`** - Update running application with new code
- **`restart`** - Restart services
- **`stop`** - Stop all services
- **`logs`** - Show service logs
- **`status`** - Show service status
- **`cleanup`** - Clean up old images and containers

### Options

- **`-v, --version`** - Specify version tag (default: timestamp)
- **`-s, --service`** - Target specific service (backend, frontend, or all)

### Examples

```bash
# Full deployment with version
./deploy.sh deploy -v v1.2.3

# Update only backend
./deploy.sh update -s backend

# Show logs for frontend only
./deploy.sh logs -s frontend

# Clean up old images
./deploy.sh cleanup

# Check service status
./deploy.sh status
```

## Quick Update Process

For rapid code updates during development:

```bash
./quick-update.sh
```

This script:
1. Builds new images with current git commit hash
2. Updates services with minimal downtime
3. Shows health status and recent logs
4. Uses `--no-cache` to ensure latest code is included

## Updating Code

### Method 1: Quick Update (Recommended for small changes)
```bash
# Make your code changes
git add .
git commit -m "Your changes"

# Update deployment
./quick-update.sh
```

### Method 2: Versioned Deployment (Recommended for releases)
```bash
# Make your code changes
git add .
git commit -m "Your changes"
git tag v1.2.3

# Deploy new version
./deploy.sh deploy -v v1.2.3
```

### Method 3: Service-specific Update
```bash
# Update only backend after backend changes
./deploy.sh update -s backend

# Update only frontend after frontend changes
./deploy.sh update -s frontend
```

## Troubleshooting

### Container Issues

```bash
# Check service status
./deploy.sh status

# View logs
./deploy.sh logs

# Restart services
./deploy.sh restart

# Clean rebuild
./deploy.sh cleanup
./deploy.sh deploy
```

### Common Issues

1. **Container metadata errors**: Run `./deploy.sh cleanup` then redeploy
2. **Port conflicts**: Check if ports 34197/34198 are available
3. **Health check failures**: Check logs for specific error messages
4. **SSL issues**: Ensure SSL certificates are in the `ssl/` directory

### Health Checks

All services include health checks:
- **MongoDB**: Tests database ping
- **Backend**: Tests `/health` endpoint
- **Frontend**: Tests nginx availability

### Logs and Monitoring

```bash
# All service logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Container resource usage
docker stats
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-secure-password
DATABASE_NAME=ai_stock_dashboard

# API Keys
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key
POLYGON_API_KEY=your-polygon-key

# Security
JWT_SECRET_KEY=your-jwt-secret
SECRET_KEY=your-app-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
```

### SSL Certificates

Place SSL certificates in the `ssl/` directory:
- `ssl/fullchain.pem`
- `ssl/privkey.pem`

## Best Practices

1. **Use versioned deployments** for production releases
2. **Test changes** in development mode first
3. **Regular cleanup** to prevent disk space issues
4. **Monitor logs** after deployments
5. **Backup database** before major updates
6. **Use semantic versioning** for releases (v1.2.3)

## Rollback

To rollback to a previous version:

```bash
# List available versions
docker images | grep ai-stock-dashboard

# Deploy specific version
./deploy.sh deploy -v v1.1.0
```

## Performance

### Image Size Optimization
- Multi-stage builds reduce final image size
- Development dependencies excluded from production
- Cached layers for faster rebuilds

### Update Speed
- Quick updates only rebuild changed services
- Docker layer caching speeds up builds
- Volume mounts for development hot reload

This deployment system provides both flexibility for development and reliability for production deployments.
