# AI Stock Dashboard - Docker Setup

This guide explains how to run the AI Stock Dashboard using Docker with user management, subscription tiers, and multi-AI analysis capabilities.

## Prerequisites

- Docker
- Docker Compose
- API Keys (OpenAI or Groq)

## Architecture Overview

The application now consists of three main services:
- **Frontend**: React application served by nginx
- **Backend**: FastAPI application with user management and multi-AI analysis
- **MongoDB**: Database for user accounts, subscriptions, and persistent data

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd ai-stock-dashboard
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file and add your API keys and database credentials
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   - Frontend HTTP: http://localhost:80
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required: API Keys for AI analysis
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Additional stock data sources
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
POLYGON_API_KEY=your_polygon_api_key_here

# Backend Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database Configuration
MONGODB_URL=mongodb://admin:password123@mongodb:27017
DATABASE_NAME=ai_stock_dashboard
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=password123

# Authentication & Security (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=jwt-secret-key-change-in-production
SECRET_KEY=your-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## Docker Commands

### Build and start all services:
```bash
docker compose up --build
```

### Run in background:
```bash
docker compose up -d
```

### Stop all services:
```bash
docker compose down
```

### View logs:
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Rebuild specific service:
```bash
docker compose build backend
docker compose build frontend
```

## Services

### MongoDB Database
- **Internal Port:** 27017 (not exposed externally)
- **Data Persistence:** Uses named volume `mongodb_data`
- **Initialization:** Automatically creates indexes for optimal performance
- **Health Check:** MongoDB ping command
- **Features:**
  - User account storage
  - Subscription tier management
  - Stock tracking per user
  - Analysis result caching

### Backend (FastAPI)
- **Port:** 8000
- **Health Check:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Features:**
  - User registration and authentication
  - JWT-based session management
  - Multi-AI analysis system (4 different AI models)
  - Subscription tier enforcement
  - Stock data fetching from multiple sources
  - Scheduled updates every 30 minutes
  - RESTful API endpoints

### Frontend (React + Vite)
- **Port:** 80
- **Features:**
  - User authentication interface
  - Subscription tier dashboard
  - Multi-AI analysis display
  - Real-time stock data visualization
  - Responsive design
  - Nginx reverse proxy for API calls

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    MongoDB      │
│   (React/Nginx) │────│   (FastAPI)     │────│   (Database)    │
│   Port: 80      │    │   Port: 8000    │    │   Port: 27017   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                        Docker Network
                     (ai-stock-network)
```

### Data Flow
1. **User Authentication**: Frontend → Backend → MongoDB
2. **Stock Analysis**: Backend → External APIs → AI Services → MongoDB (cache)
3. **User Dashboard**: Frontend → Backend → MongoDB → Multi-AI Analysis

## Production Deployment

### Required Ports for Production:
- **Port 34197 (HTTP)** - Frontend application
- **Port 34198 (HTTPS)** - Secure frontend application
- **MongoDB Port 27017** - Internal only, not exposed externally

### Database Security:
- **MongoDB Authentication**: Uses root username/password
- **Network Isolation**: MongoDB only accessible within Docker network
- **Data Persistence**: MongoDB data stored in named Docker volume
- **Initialization**: Auto-creates database indexes for performance

### HTTPS Setup Options:

#### Option 1: Self-Signed Certificates (Development/Testing)
```bash
# Generate self-signed certificates
./generate-ssl.sh

# Deploy with HTTPS
docker compose -f docker compose.prod.yml up -d
```

#### Option 2: Let's Encrypt Certificates (Production)
```bash
# Edit setup-letsencrypt.sh with your domain and email
nano setup-letsencrypt.sh

# Run Let's Encrypt setup
./setup-letsencrypt.sh
```

### Security Recommendations:
1. **Change default passwords** in production (MongoDB, admin credentials)
2. **Generate strong JWT secrets** for production
3. **Do NOT expose backend port 8000** in production
4. **Do NOT expose MongoDB port 27017** externally
5. **Use the production docker compose file**
6. **Set up SSL/TLS termination** (recommended)
7. **Use environment variables** for all secrets
8. **Regular database backups** recommended

### Production Setup:

1. **Use production docker compose:**
   ```bash
   # Copy production environment template
   cp .env.prod .env
   # Edit .env with your production API keys
   
   # Deploy with production configuration
   docker compose -f docker compose.prod.yml up -d
   ```

2. **With SSL Termination (recommended):**
   ```yaml
   # In docker compose.prod.yml, use:
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
docker compose -f docker compose.yml up -d
```

## Troubleshooting

### Check service health:
```bash
docker compose ps

# Or use the provided health check script
./health-check.sh
```

### View service logs:
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs mongodb
```

### Access MongoDB (for debugging):
```bash
# Connect to MongoDB container
docker compose exec mongodb mongosh

# Or connect with authentication
docker compose exec mongodb mongosh -u admin -p password123 --authenticationDatabase admin
```

### Database Operations:
```bash
# Backup MongoDB data
docker compose exec mongodb mongodump --db ai_stock_dashboard --out /data/backup

# Restore MongoDB data
docker compose exec mongodb mongorestore --db ai_stock_dashboard /data/backup/ai_stock_dashboard
```

### Restart services:
```bash
docker compose restart
```

### Clean up:
```bash
# Remove containers and networks
docker compose down

# Remove containers, networks, and images
docker compose down --rmi all

# Remove everything including volumes
docker compose down --volumes --rmi all
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info

### User Management
- `GET /api/v1/users/me` - Get user profile
- `GET /api/v1/users/stocks` - Get user's tracked stocks
- `POST /api/v1/users/stocks` - Add stock to user's watchlist
- `DELETE /api/v1/users/stocks/{symbol}` - Remove stock from watchlist

### Stock Analysis
- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `GET /api/v1/status` - Service status
- `GET /api/v1/stocks` - Get all stocks with AI analysis
- `POST /api/v1/stocks/analyze` - Trigger manual analysis

### Admin
- `GET /api/v1/admin/config` - Get admin configuration
- `POST /api/v1/admin/config` - Update admin configuration

## Security Notes

- **API keys** are passed as environment variables
- **Database credentials** are configurable via environment variables
- **JWT tokens** used for user session management
- **Password hashing** with bcrypt for user accounts
- **Frontend** uses nginx with security headers
- **Backend** runs as non-root user
- **MongoDB** runs with authentication enabled
- **CORS** is configured for the frontend domain
- **Health checks** ensure service availability
- **Network isolation** between services using Docker networks

## Data Backup and Recovery

### MongoDB Backup
```bash
# Create backup directory
mkdir -p ./mongodb-backups

# Backup MongoDB data
docker compose exec mongodb mongodump --db ai_stock_dashboard --out /data/backup
docker cp ai-stock-dashboard-mongodb:/data/backup ./mongodb-backups/

# Or use a one-liner for current date
docker compose exec mongodb mongodump --db ai_stock_dashboard --out /data/backup/$(date +%Y%m%d_%H%M%S)
```

### MongoDB Restore
```bash
# Restore from backup
docker cp ./mongodb-backups/backup ai-stock-dashboard-mongodb:/data/restore
docker compose exec mongodb mongorestore --db ai_stock_dashboard /data/restore/ai_stock_dashboard --drop
```

### Data Volume Management
```bash
# Create backup of Docker volume
docker run --rm -v ai-stock-dashboard_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb_backup.tar.gz -C /data .

# Restore Docker volume from backup
docker run --rm -v ai-stock-dashboard_mongodb_data:/data -v $(pwd):/backup alpine tar xzf /backup/mongodb_backup.tar.gz -C /data
```

## Performance

- **Frontend:** Static files served by nginx with gzip compression and caching
- **Backend:** Async FastAPI with scheduled background tasks and JWT authentication
- **Database:** MongoDB with proper indexing for user queries and stock data
- **Caching:** Analysis results cached to reduce API calls
- **Networking:** Internal Docker network for service communication
- **Persistence:** MongoDB data persisted using Docker volumes
- **Scalability:** Designed for horizontal scaling with user-specific data isolation
