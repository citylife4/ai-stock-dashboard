# AI Stock Dashboard - Docker Setup

This guide explains how to run the AI Stock Dashboard using Docker.

## Prerequisites

- Docker
- Docker Compose
- API Keys (OpenAI or Groq)

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd ai-stock-dashboard
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file and add your API keys
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend HTTP: http://localhost:34197
   - Frontend HTTPS: https://localhost:34198 (if SSL certificates are available)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required: API Keys for AI analysis
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Backend Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

## Docker Commands

### Build and start all services:
```bash
docker-compose up --build
```

### Run in background:
```bash
docker-compose up -d
```

### Stop all services:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild specific service:
```bash
docker-compose build backend
docker-compose build frontend
```

## Services

### Backend (FastAPI)
- **Port:** 8000
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Features:**
  - Stock data fetching from Yahoo Finance
  - AI-powered stock analysis
  - Scheduled updates every 30 minutes
  - RESTful API endpoints

### Frontend (React + Vite)
- **Port:** 80
- **Features:**
  - React-based dashboard
  - Real-time stock data display
  - AI analysis scores and recommendations
  - Responsive design
  - Nginx reverse proxy for API calls

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   (React/Nginx) │────│   (FastAPI)     │
│   Port: 80      │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
              Docker Network
```

## Production Deployment

### Required Ports for Production:
- **Port 34197 (HTTP)** - Frontend application
- **Port 34198 (HTTPS)** - Secure frontend application

### HTTPS Setup Options:

#### Option 1: Self-Signed Certificates (Development/Testing)
```bash
# Generate self-signed certificates
./generate-ssl.sh

# Deploy with HTTPS
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 2: Let's Encrypt Certificates (Production)
```bash
# Edit setup-letsencrypt.sh with your domain and email
nano setup-letsencrypt.sh

# Run Let's Encrypt setup
./setup-letsencrypt.sh
```

### Security Recommendations:
1. **Do NOT expose backend port 8000** in production
2. **Use the production docker-compose file**
3. **Set up SSL/TLS termination** (recommended)
4. **Use environment variables** for API keys

### Production Setup:

1. **Use production docker-compose:**
   ```bash
   # Copy production environment template
   cp .env.prod .env
   # Edit .env with your production API keys
   
   # Deploy with production configuration
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **With SSL Termination (recommended):**
   ```yaml
   # In docker-compose.prod.yml, use:
   frontend:
     ports:
       - "443:80"  # If your load balancer/proxy handles SSL
   ```

3. **Behind a Reverse Proxy/Load Balancer:**
   ```yaml
   # No external ports needed if behind nginx/haproxy/etc
   frontend:
     expose:
       - "80"  # Only expose to internal network
   ```

### Firewall Configuration:
```bash
# Allow only necessary ports
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS (if applicable)
# Do NOT open port 8000
```

## Development

### Development with hot reload:
1. **Backend:**
   ```bash
   cd backend
   docker build -t ai-stock-backend .
   docker run -p 8000:8000 -v $(pwd):/app -e DEBUG=true ai-stock-backend
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Production deployment:
```bash
docker-compose -f docker-compose.yml up -d
```

## Troubleshooting

### Check service health:
```bash
docker-compose ps
```

### View service logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Restart services:
```bash
docker-compose restart
```

### Clean up:
```bash
# Remove containers and networks
docker-compose down

# Remove containers, networks, and images
docker-compose down --rmi all

# Remove everything including volumes
docker-compose down --volumes --rmi all
```

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `GET /api/v1/status` - Service status
- `GET /api/v1/stocks` - Get all stocks with AI analysis
- `POST /api/v1/stocks/analyze` - Trigger manual analysis

## Security Notes

- API keys are passed as environment variables
- Frontend uses nginx with security headers
- Backend runs as non-root user
- CORS is configured for the frontend domain
- Health checks ensure service availability

## Performance

- **Frontend:** Static files served by nginx with gzip compression and caching
- **Backend:** Async FastAPI with scheduled background tasks
- **Database:** In-memory storage for real-time data (Redis can be added for persistence)
- **Networking:** Internal Docker network for service communication
