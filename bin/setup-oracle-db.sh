#!/bin/bash

# Oracle Autonomous Database Setup Script for AI Stock Dashboard
# This script creates and configures Oracle Autonomous Database for the application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ORACLE_CONFIG_FILE="$PROJECT_ROOT/oracle-config.json"
WALLET_DIR="$PROJECT_ROOT/oracle-wallet"
REQUIREMENTS_FILE="$PROJECT_ROOT/oracle-requirements.txt"

echo -e "${BLUE}🏗️  Oracle Autonomous Database Setup for AI Stock Dashboard${NC}"
echo "=============================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if Oracle config file exists
if [[ ! -f "$ORACLE_CONFIG_FILE" ]]; then
    print_error "Oracle configuration file not found: $ORACLE_CONFIG_FILE"
    echo "Please create the Oracle configuration file first using:"
    echo "  ./bin/setup-oracle-config.sh"
    exit 1
fi

# Read Oracle configuration
ORACLE_CONFIG=$(cat "$ORACLE_CONFIG_FILE")
DB_NAME=$(echo "$ORACLE_CONFIG" | jq -r '.db_name')
DB_USERNAME=$(echo "$ORACLE_CONFIG" | jq -r '.username')
DB_PASSWORD=$(echo "$ORACLE_CONFIG" | jq -r '.password')
WALLET_PASSWORD=$(echo "$ORACLE_CONFIG" | jq -r '.wallet_password')
CONNECTION_STRING=$(echo "$ORACLE_CONFIG" | jq -r '.connection_string')

print_info "Using Oracle database: $DB_NAME"
print_info "Username: $DB_USERNAME"

# Step 1: Install Oracle client dependencies
echo
echo -e "${BLUE}📦 Step 1: Installing Oracle Client Dependencies${NC}"
echo "=================================================="

# Create requirements file for Oracle
cat > "$REQUIREMENTS_FILE" << EOF
# Oracle Database Dependencies
oracledb>=1.4.0
cx_Oracle>=8.3.0
sqlalchemy>=2.0.0
alembic>=1.12.0

# Additional MongoDB compatibility (for migration)
pymongo>=4.5.0
motor>=3.3.0
EOF

print_status "Created Oracle requirements file"

# Install Oracle dependencies
if command -v pip &> /dev/null; then
    print_info "Installing Oracle Python dependencies..."
    pip install -r "$REQUIREMENTS_FILE"
    print_status "Oracle dependencies installed"
else
    print_warning "pip not found. Please install the requirements manually:"
    cat "$REQUIREMENTS_FILE"
fi

# Step 2: Setup Oracle Wallet
echo
echo -e "${BLUE}🔐 Step 2: Setting up Oracle Wallet${NC}"
echo "=================================="

mkdir -p "$WALLET_DIR"

if [[ -f "$WALLET_DIR/tnsnames.ora" ]]; then
    print_warning "Oracle wallet already exists. Backing up..."
    cp -r "$WALLET_DIR" "$WALLET_DIR.backup.$(date +%Y%m%d_%H%M%S)"
fi

print_info "Oracle wallet directory: $WALLET_DIR"
print_status "Wallet directory created"

# Step 3: Create Oracle Database Schema
echo
echo -e "${BLUE}🗃️  Step 3: Creating Database Schema${NC}"
echo "===================================="

# Create the database schema SQL
cat > "$PROJECT_ROOT/oracle-schema.sql" << 'EOF'
-- AI Stock Dashboard Oracle Schema
-- Compatible with Oracle Autonomous Database

-- Create sequences for auto-incrementing IDs
CREATE SEQUENCE user_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE admin_config_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE user_stocks_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE audit_logs_seq START WITH 1 INCREMENT BY 1;

-- Users table
CREATE TABLE users (
    id NUMBER DEFAULT user_seq.NEXTVAL PRIMARY KEY,
    username VARCHAR2(50) UNIQUE NOT NULL,
    email VARCHAR2(255) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    subscription_tier VARCHAR2(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'expert')),
    max_stocks NUMBER DEFAULT 5,
    is_active NUMBER(1) DEFAULT 1,
    is_admin NUMBER(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stock_count NUMBER DEFAULT 0
);

-- Admin configuration table (replaces JSON file)
CREATE TABLE admin_config (
    id NUMBER DEFAULT admin_config_seq.NEXTVAL PRIMARY KEY,
    stock_symbols CLOB, -- JSON array of stock symbols
    ai_analysis_prompt CLOB,
    data_source VARCHAR2(50) DEFAULT 'yahoo',
    alpha_vantage_api_key VARCHAR2(255),
    polygon_api_key VARCHAR2(255),
    ai_provider VARCHAR2(50) DEFAULT 'openai',
    ai_model VARCHAR2(100) DEFAULT 'gpt-3.5-turbo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User stocks tracking table
CREATE TABLE user_stocks (
    id NUMBER DEFAULT user_stocks_seq.NEXTVAL PRIMARY KEY,
    user_id NUMBER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR2(10) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

-- Audit logs table
CREATE TABLE audit_logs (
    id NUMBER DEFAULT audit_logs_seq.NEXTVAL PRIMARY KEY,
    action VARCHAR2(100) NOT NULL,
    details CLOB,
    admin_user VARCHAR2(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock data cache table (for performance)
CREATE TABLE stock_data_cache (
    symbol VARCHAR2(10) PRIMARY KEY,
    data CLOB, -- JSON data
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_user_stocks_user_id ON user_stocks(user_id);
CREATE INDEX idx_user_stocks_symbol ON user_stocks(symbol);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_stock_cache_expires ON stock_data_cache(expires_at);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE TRIGGER users_updated_at_trigger
    BEFORE UPDATE ON users
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER admin_config_updated_at_trigger
    BEFORE UPDATE ON admin_config
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- Insert default admin configuration
INSERT INTO admin_config (
    stock_symbols,
    ai_analysis_prompt,
    data_source,
    alpha_vantage_api_key,
    polygon_api_key,
    ai_provider,
    ai_model
) VALUES (
    '["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]',
    'Analyze the following stock data and provide:
1. A score from 0-100 (100 being the best investment opportunity)
2. A brief reason for the score (2-3 sentences)

Consider factors like:
- Recent price performance
- Trading volume
- Market cap
- General market sentiment for the sector

Stock Data:
Symbol: {symbol}
Current Price: ${current_price}
Previous Close: ${previous_close}
Daily Change: {change_percent}%
Volume: {volume}
Market Cap: ${market_cap}

Respond in JSON format:
{"score": <number>, "reason": "<explanation>"}',
    'yahoo',
    '',
    '',
    'openai',
    'gpt-3.5-turbo'
);

COMMIT;
EOF

print_status "Database schema SQL created"

# Step 4: Create Python database adapter
echo
echo -e "${BLUE}🐍 Step 4: Creating Oracle Database Adapter${NC}"
echo "============================================="

cat > "$PROJECT_ROOT/backend/app/database_oracle.py" << 'EOF'
import os
import json
import oracledb
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OracleDatabase:
    def __init__(self):
        self.engine = None
        self.session_local = None
        self._connection_string = None
        
    def initialize(self, config_file: str = "oracle-config.json"):
        """Initialize Oracle database connection."""
        try:
            # Load Oracle configuration
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Setup Oracle client
            wallet_dir = config.get('wallet_dir', './oracle-wallet')
            if os.path.exists(wallet_dir):
                oracledb.init_oracle_client(config_dir=wallet_dir)
            
            # Create connection string
            username = config['username']
            password = config['password']
            connection_string = config['connection_string']
            
            # SQLAlchemy connection string for Oracle
            self._connection_string = f"oracle+oracledb://{username}:{password}@{connection_string}"
            
            # Create engine
            self.engine = create_engine(
                self._connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create session factory
            self.session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 FROM DUAL"))
                result.fetchone()
            
            logger.info("Oracle database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Oracle database: {e}")
            return False
    
    def get_session(self):
        """Get database session."""
        if self.session_local is None:
            raise RuntimeError("Database not initialized")
        return self.session_local()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a query and return results."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                if result.returns_rows:
                    return result.fetchall()
                else:
                    conn.commit()
                    return result.rowcount
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if database is available."""
        try:
            if self.engine is None:
                return False
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL"))
            return True
        except:
            return False

# Global Oracle database instance
oracle_db = OracleDatabase()
EOF

print_status "Oracle database adapter created"

# Step 5: Create migration script
echo
echo -e "${BLUE}🔄 Step 5: Creating MongoDB to Oracle Migration Script${NC}"
echo "===================================================="

cat > "$PROJECT_ROOT/migrate_to_oracle.py" << 'EOF'
#!/usr/bin/env python3
"""
Migration script to move data from MongoDB to Oracle Autonomous Database
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# MongoDB imports
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

# Oracle imports
from backend.app.database_oracle import oracle_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoToOracleMigrator:
    def __init__(self, mongo_url: str, mongo_db_name: str):
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.mongo_db = self.mongo_client[mongo_db_name]
        
    async def migrate_users(self):
        """Migrate users from MongoDB to Oracle."""
        logger.info("Migrating users...")
        
        try:
            # Get users from MongoDB
            users_cursor = self.mongo_db.users.find({})
            users = await users_cursor.to_list(length=None)
            
            if not users:
                logger.info("No users found in MongoDB")
                return
            
            # Insert users into Oracle
            for user in users:
                oracle_db.execute_query("""
                    INSERT INTO users (
                        username, email, password_hash, subscription_tier,
                        max_stocks, is_active, is_admin, created_at, stock_count
                    ) VALUES (
                        :username, :email, :password_hash, :subscription_tier,
                        :max_stocks, :is_active, :is_admin, :created_at, :stock_count
                    )
                """, {
                    'username': user.get('username'),
                    'email': user.get('email'),
                    'password_hash': user.get('password_hash'),
                    'subscription_tier': user.get('subscription_tier', 'free'),
                    'max_stocks': user.get('max_stocks', 5),
                    'is_active': 1 if user.get('is_active', True) else 0,
                    'is_admin': 1 if user.get('is_admin', False) else 0,
                    'created_at': user.get('created_at', datetime.utcnow()),
                    'stock_count': user.get('stock_count', 0)
                })
            
            logger.info(f"Migrated {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            raise
    
    async def migrate_user_stocks(self):
        """Migrate user stocks from MongoDB to Oracle."""
        logger.info("Migrating user stocks...")
        
        try:
            # Get user stocks from MongoDB
            stocks_cursor = self.mongo_db.user_stocks.find({})
            stocks = await stocks_cursor.to_list(length=None)
            
            if not stocks:
                logger.info("No user stocks found in MongoDB")
                return
            
            # Get user ID mapping (MongoDB ObjectId to Oracle ID)
            user_mapping = {}
            oracle_users = oracle_db.execute_query("SELECT id, email FROM users")
            
            for oracle_user in oracle_users:
                user_mapping[oracle_user[1]] = oracle_user[0]  # email -> oracle_id
            
            # Insert user stocks into Oracle
            for stock in stocks:
                user_email = stock.get('user_email')  # Assuming we have email in MongoDB
                if user_email in user_mapping:
                    oracle_db.execute_query("""
                        INSERT INTO user_stocks (user_id, symbol, added_at)
                        VALUES (:user_id, :symbol, :added_at)
                    """, {
                        'user_id': user_mapping[user_email],
                        'symbol': stock.get('symbol'),
                        'added_at': stock.get('added_at', datetime.utcnow())
                    })
            
            logger.info(f"Migrated {len(stocks)} user stocks")
            
        except Exception as e:
            logger.error(f"Error migrating user stocks: {e}")
            raise
    
    async def migrate_admin_config(self):
        """Migrate admin configuration."""
        logger.info("Migrating admin configuration...")
        
        try:
            # Check if there's existing config in Oracle
            existing_config = oracle_db.execute_query("SELECT COUNT(*) FROM admin_config")
            if existing_config[0][0] > 0:
                logger.info("Admin config already exists in Oracle, skipping...")
                return
            
            # Try to read from JSON file (current system)
            try:
                with open('backend/admin_config.json', 'r') as f:
                    config_data = json.load(f)
                
                oracle_db.execute_query("""
                    UPDATE admin_config SET
                        stock_symbols = :stock_symbols,
                        ai_analysis_prompt = :ai_analysis_prompt,
                        data_source = :data_source,
                        alpha_vantage_api_key = :alpha_vantage_api_key,
                        polygon_api_key = :polygon_api_key,
                        ai_provider = :ai_provider,
                        ai_model = :ai_model,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, {
                    'stock_symbols': json.dumps(config_data.get('stock_symbols', [])),
                    'ai_analysis_prompt': config_data.get('ai_analysis_prompt', ''),
                    'data_source': config_data.get('data_source', 'yahoo'),
                    'alpha_vantage_api_key': config_data.get('alpha_vantage_api_key', ''),
                    'polygon_api_key': config_data.get('polygon_api_key', ''),
                    'ai_provider': config_data.get('ai_provider', 'openai'),
                    'ai_model': config_data.get('ai_model', 'gpt-3.5-turbo')
                })
                
                logger.info("Migrated admin configuration from JSON file")
                
            except FileNotFoundError:
                logger.info("No existing admin config file found, using defaults")
            
        except Exception as e:
            logger.error(f"Error migrating admin config: {e}")
            raise
    
    async def run_migration(self):
        """Run complete migration."""
        logger.info("Starting MongoDB to Oracle migration...")
        
        try:
            await self.migrate_users()
            await self.migrate_user_stocks()
            await self.migrate_admin_config()
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.mongo_client.close()

async def main():
    """Main migration function."""
    # Configuration
    mongo_url = "mongodb://localhost:27017"  # Update as needed
    mongo_db_name = "ai_stock_dashboard"
    
    # Initialize Oracle database
    if not oracle_db.initialize():
        logger.error("Failed to initialize Oracle database")
        return
    
    # Run migration
    migrator = MongoToOracleMigrator(mongo_url, mongo_db_name)
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())
EOF

print_status "Migration script created"

# Step 6: Create test script
echo
echo -e "${BLUE}🧪 Step 6: Creating Database Test Script${NC}"
echo "========================================"

cat > "$PROJECT_ROOT/test_oracle_db.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script for Oracle Autonomous Database connection and functionality
"""

import json
from backend.app.database_oracle import oracle_db

def test_oracle_connection():
    """Test Oracle database connection."""
    print("🔗 Testing Oracle database connection...")
    
    if not oracle_db.initialize():
        print("❌ Failed to initialize Oracle database")
        return False
    
    if not oracle_db.is_available():
        print("❌ Oracle database is not available")
        return False
    
    print("✅ Oracle database connection successful")
    return True

def test_basic_queries():
    """Test basic database operations."""
    print("📊 Testing basic database queries...")
    
    try:
        # Test simple query
        result = oracle_db.execute_query("SELECT 1 FROM DUAL")
        print(f"✅ Basic query successful: {result}")
        
        # Test admin config
        config_result = oracle_db.execute_query("SELECT * FROM admin_config WHERE ROWNUM = 1")
        if config_result:
            print("✅ Admin config table accessible")
        else:
            print("⚠️  No admin config found")
        
        # Test users table
        user_count = oracle_db.execute_query("SELECT COUNT(*) FROM users")
        print(f"✅ Users table accessible - {user_count[0][0]} users found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return False

def test_data_operations():
    """Test data insertion and retrieval."""
    print("💾 Testing data operations...")
    
    try:
        # Test inserting and retrieving a test user
        oracle_db.execute_query("""
            INSERT INTO users (username, email, password_hash, subscription_tier)
            VALUES (:username, :email, :password_hash, :subscription_tier)
        """, {
            'username': 'test_user_oracle',
            'email': 'test@oracle.com',
            'password_hash': 'test_hash',
            'subscription_tier': 'free'
        })
        
        # Retrieve the test user
        test_user = oracle_db.execute_query("""
            SELECT username, email FROM users WHERE email = :email
        """, {'email': 'test@oracle.com'})
        
        if test_user:
            print(f"✅ Data operations successful: {test_user[0]}")
            
            # Clean up test user
            oracle_db.execute_query("DELETE FROM users WHERE email = :email", 
                                   {'email': 'test@oracle.com'})
            print("✅ Test data cleaned up")
        else:
            print("❌ Failed to retrieve test data")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data operations failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🏗️  Oracle Autonomous Database Test Suite")
    print("==========================================")
    
    tests = [
        test_oracle_connection,
        test_basic_queries,
        test_data_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Oracle database is ready for use.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()
EOF

print_status "Test script created"

# Step 7: Create configuration helper
echo
echo -e "${BLUE}⚙️  Step 7: Creating Configuration Helper${NC}"
echo "==========================================="

cat > "$PROJECT_ROOT/bin/setup-oracle-config.sh" << 'EOF'
#!/bin/bash

# Oracle Configuration Setup Script

echo "🔧 Oracle Autonomous Database Configuration Setup"
echo "================================================="

CONFIG_FILE="oracle-config.json"

echo "Please provide your Oracle Autonomous Database details:"
echo

read -p "Database Name (e.g., myautodbname): " DB_NAME
read -p "Username (e.g., ADMIN): " DB_USERNAME
read -s -p "Password: " DB_PASSWORD
echo
read -s -p "Wallet Password: " WALLET_PASSWORD
echo
read -p "Connection String (e.g., myautodbname_high): " CONNECTION_STRING
read -p "Wallet Directory (default: ./oracle-wallet): " WALLET_DIR

WALLET_DIR=${WALLET_DIR:-./oracle-wallet}

# Create configuration file
cat > "$CONFIG_FILE" << EOF
{
  "db_name": "$DB_NAME",
  "username": "$DB_USERNAME",
  "password": "$DB_PASSWORD",
  "wallet_password": "$WALLET_PASSWORD",
  "connection_string": "$CONNECTION_STRING",
  "wallet_dir": "$WALLET_DIR"
}
EOF

echo "✅ Configuration saved to $CONFIG_FILE"
echo "⚠️  Please ensure your Oracle wallet files are in: $WALLET_DIR"
echo "   Required files: tnsnames.ora, sqlnet.ora, cwallet.sso"
EOF

chmod +x "$PROJECT_ROOT/bin/setup-oracle-config.sh"
print_status "Configuration helper created"

# Final summary
echo
echo -e "${GREEN}🎉 Oracle Autonomous Database Setup Complete!${NC}"
echo "=============================================="
echo
print_info "Next steps:"
echo "1. Run: ./bin/setup-oracle-config.sh (to configure Oracle connection)"
echo "2. Download and extract Oracle wallet to oracle-wallet/ directory"
echo "3. Run: python3 oracle-schema.sql (to create database schema)"
echo "4. Run: python3 test_oracle_db.py (to test the connection)"
echo "5. Run: python3 migrate_to_oracle.py (to migrate from MongoDB)"
echo
print_info "Files created:"
echo "  📄 $ORACLE_CONFIG_FILE (template)"
echo "  📁 $WALLET_DIR (directory)"
echo "  📄 oracle-schema.sql (database schema)"
echo "  📄 backend/app/database_oracle.py (Oracle adapter)"
echo "  📄 migrate_to_oracle.py (migration script)"
echo "  📄 test_oracle_db.py (test script)"
echo "  📄 bin/setup-oracle-config.sh (config helper)"
echo
print_warning "Remember to:"
echo "  • Keep your Oracle credentials secure"
echo "  • Download your Oracle wallet files"
echo "  • Update environment variables for production"
echo
echo -e "${BLUE}Happy coding! 🚀${NC}"
