# AI Stock Dashboard - Scaling and Architecture Guide

## Overview
This document outlines the scalability improvements and architectural changes made to support user management, subscription tiers, and multi-AI analysis.

## Database Architecture

### MongoDB Schema Design

#### Users Collection
```javascript
{
  _id: ObjectId,
  username: String (unique),
  email: String (unique),
  password_hash: String,
  subscription_tier: String (enum: "free", "pro", "expert"),
  max_stocks: Number,
  created_at: Date,
  updated_at: Date,
  is_active: Boolean
}
```

#### User Stocks Collection
```javascript
{
  _id: ObjectId,
  user_id: String (ref: users._id),
  symbol: String,
  added_at: Date
}
```

#### Stock Cache Collection (Future Enhancement)
```javascript
{
  _id: ObjectId,
  symbol: String (unique),
  stock_data: Object,
  ai_analyses: {
    basic: Object,
    warren_buffet: Object,
    peter_lynch: Object,
    dcf_math: Object
  },
  last_updated: Date,
  expires_at: Date
}
```

### Indexes for Performance
- `users.email` (unique)
- `users.username` (unique)
- `user_stocks.user_id`
- `user_stocks.symbol`
- `user_stocks.user_id + symbol` (compound, unique)
- `stocks.symbol` (for cache)
- `stocks.last_updated` (for cache expiry)

## Subscription Tiers

### Free Tier (Default)
- **Max Stocks:** 5
- **AI Models:** Basic AI only
- **Features:** Basic stock tracking and analysis

### Pro Tier
- **Max Stocks:** 10
- **AI Models:** Basic + Warren Buffet + Peter Lynch
- **Features:** Multiple AI perspectives, enhanced analysis

### Expert Tier
- **Max Stocks:** 20
- **AI Models:** All (Basic + Warren Buffet + Peter Lynch + DCF Math)
- **Features:** Full AI suite, maximum stock tracking

## Multi-AI System

### AI Model Types
1. **Basic AI:** General-purpose stock analysis
2. **Warren Buffet Style:** Value investing approach
3. **Peter Lynch Style:** Growth at reasonable price (GARP)
4. **DCF Mathematical:** Quantitative analysis using mathematical models

### AI Analysis Flow
```
Stock Data → Multi-AI Service → {
  For each AI model allowed by subscription:
    - Generate specialized analysis
    - Return score + reasoning
} → Aggregate results → Return MultiAIAnalysis
```

## API Deduplication Strategy

### Current Implementation
- User-specific stock tracking eliminates duplicate API calls
- Only fetch data for stocks that users are actually tracking
- Cache results in memory for the scheduler cycle

### Future Enhancements
1. **Redis Cache Layer:**
   ```
   Key: stock:{symbol}
   Value: { stock_data, ai_analyses, timestamp }
   TTL: 30 minutes
   ```

2. **Database Caching:**
   - Store stock data and AI analyses in MongoDB
   - Update only when data is stale (>30 minutes)
   - Serve cached data for multiple users tracking same stock

3. **Background Jobs:**
   - Separate worker processes for data fetching
   - Queue-based system for AI analysis
   - Scheduled bulk updates for popular stocks

## Horizontal Scaling Strategies

### Load Balancing
```
Internet → Load Balancer → {
  Frontend Instance 1 (React + Nginx)
  Frontend Instance 2 (React + Nginx)
  Frontend Instance N
}

Load Balancer → {
  Backend Instance 1 (FastAPI)
  Backend Instance 2 (FastAPI)  
  Backend Instance N
}
```

### Database Scaling
1. **MongoDB Replica Set:**
   - Primary for writes
   - Secondaries for read distribution
   - Automatic failover

2. **Sharding (Future):**
   - Shard by user_id for user data
   - Shard by symbol for stock data
   - Separate clusters for analytics

### Microservices Architecture (Future)
```
API Gateway → {
  User Service (Authentication, Profiles)
  Stock Service (Data Fetching, Caching)
  AI Service (Analysis Processing)
  Subscription Service (Billing, Limits)
  Notification Service (Alerts, Updates)
}
```

## Caching Strategy

### Multi-Level Caching
1. **Application Cache (Current):**
   - In-memory storage for scheduler results
   - 30-minute TTL for stock data

2. **Redis Cache (Recommended):**
   ```
   Layer 1: User session data (JWT, preferences)
   Layer 2: Stock data cache (raw API responses)
   Layer 3: AI analysis cache (processed results)
   ```

3. **CDN (Frontend):**
   - Static assets (CSS, JS, images)
   - API response caching for public endpoints

## Performance Optimizations

### Database Optimizations
- **Connection Pooling:** Reuse database connections
- **Query Optimization:** Use proper indexes and aggregation pipelines
- **Read Replicas:** Distribute read load across multiple nodes

### API Optimizations
- **Request Batching:** Combine multiple API calls
- **Parallel Processing:** Async processing for independent operations
- **Rate Limiting:** Implement intelligent backoff strategies

### Frontend Optimizations
- **Virtual Scrolling:** Handle large stock lists efficiently
- **Component Memoization:** Prevent unnecessary re-renders
- **Progressive Loading:** Load data incrementally

## Monitoring and Observability

### Metrics to Track
- **User Metrics:** Registration rate, active users, subscription conversions
- **System Metrics:** Response times, error rates, throughput
- **Business Metrics:** API usage, popular stocks, AI model performance

### Recommended Tools
- **Application Monitoring:** Sentry, DataDog, New Relic
- **Database Monitoring:** MongoDB Atlas monitoring, pgAdmin
- **Infrastructure:** Prometheus + Grafana, AWS CloudWatch

## Security Considerations

### Authentication & Authorization
- JWT tokens with proper expiration
- Role-based access control (user vs admin)
- Rate limiting per user/IP

### Data Protection
- Password hashing with bcrypt
- HTTPS everywhere (TLS 1.2+)
- Input validation and sanitization
- SQL injection prevention (using ORMs)

## Deployment Architecture

### Current Development Setup
```
Docker Compose:
- Frontend (React + Nginx)
- Backend (FastAPI + Uvicorn)
- MongoDB (optional, falls back to in-memory)
```

### Production Recommendations
```
Kubernetes Cluster:
- Frontend: Multiple pods behind service
- Backend: Horizontal pod autoscaler
- MongoDB: StatefulSet with persistent volumes
- Redis: Managed service or cluster
- Load Balancer: Ingress controller (nginx/traefik)
```

### CI/CD Pipeline
1. **Build:** Docker images for frontend/backend
2. **Test:** Unit tests, integration tests, E2E tests
3. **Deploy:** Rolling updates with health checks
4. **Monitor:** Automated alerts and rollback capabilities

## Future Enhancements

### Phase 1 (Short Term)
- [ ] Complete user registration with email verification
- [ ] Implement user stock management (add/remove stocks)
- [ ] Add subscription upgrade/downgrade functionality
- [ ] Admin user management interface

### Phase 2 (Medium Term)
- [ ] Redis caching layer
- [ ] Background job processing
- [ ] Real-time notifications
- [ ] Advanced AI model configurations

### Phase 3 (Long Term)
- [ ] Microservices architecture
- [ ] Advanced analytics and insights
- [ ] Mobile application
- [ ] API marketplace for third-party integrations

## Configuration Management

### Environment Variables
```bash
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_stock_dashboard

# Authentication
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key
POLYGON_API_KEY=your-polygon-key

# Scaling
MAX_WORKERS=4
REDIS_URL=redis://localhost:6379
CACHE_TTL=1800
```

### Feature Flags (Recommended)
```python
FEATURES = {
    "user_registration": True,
    "multi_ai_analysis": True,
    "premium_features": False,
    "real_time_updates": False
}
```

This architecture supports the current requirements while providing a clear path for future scaling and feature development.