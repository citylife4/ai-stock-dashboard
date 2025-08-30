// MongoDB initialization script for AI Stock Dashboard
// This script runs when MongoDB container starts for the first time

// Switch to the application database
db = db.getSiblingDB('ai_stock_dashboard');

// Create indexes for better performance
// Users collection indexes
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

// User stocks collection indexes
db.user_stocks.createIndex({ "user_id": 1, "symbol": 1 }, { unique: true });
db.user_stocks.createIndex({ "user_id": 1 });
db.user_stocks.createIndex({ "symbol": 1 });

// Stock analysis collection indexes (for caching analysis results)
db.stock_analysis.createIndex({ "symbol": 1, "analysis_date": -1 });
db.stock_analysis.createIndex({ "analysis_date": -1 });

print('AI Stock Dashboard database initialized with indexes');