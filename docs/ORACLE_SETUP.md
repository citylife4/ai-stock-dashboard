# Oracle Autonomous Database Setup Guide

This guide walks you through setting up Oracle Autonomous Database for the AI Stock Dashboard application.

## 🎯 Overview

The application has been enhanced to support Oracle Autonomous Database as an alternative to MongoDB. This provides:

- **Enterprise-grade reliability** with Oracle's managed database service
- **Automatic scaling** and performance optimization
- **Built-in security** with encryption at rest and in transit
- **SQL-based queries** for complex analytics
- **Easy migration** from existing MongoDB data

## 📋 Prerequisites

1. Oracle Cloud Infrastructure (OCI) account
2. Oracle Autonomous Database instance (ATP or ADW)
3. Downloaded Oracle Wallet files
4. Python 3.12+ with pip
5. Docker (optional, for containerized deployment)

## 🚀 Quick Start

### Step 1: Create Oracle Autonomous Database

1. Log into your Oracle Cloud Infrastructure (OCI) console
2. Navigate to **Autonomous Database** service
3. Click **Create Autonomous Database**
4. Configure your database:
   - **Database Name**: `ai-stock-dashboard`
   - **Display Name**: `AI Stock Dashboard DB`
   - **Workload Type**: Autonomous Transaction Processing (ATP)
   - **Deployment Type**: Shared Infrastructure
   - **Database Version**: 19c or later
   - **OCPU Count**: 1 (can be scaled later)
   - **Storage**: 1 TB (can be scaled later)
   - **Auto Scaling**: Enabled
5. Set admin password (save this securely!)
6. Click **Create Autonomous Database**

### Step 2: Download Oracle Wallet

1. Once your database is **Available**, click on it
2. Click **Database Connection**
3. Click **Download Wallet**
4. Enter a wallet password (save this securely!)
5. Extract the wallet files to `./oracle-wallet/` directory

### Step 3: Run Setup Script

```bash
# Make sure you're in the project root directory
cd /path/to/ai-stock-dashboard

# Run the Oracle setup script
./bin/setup-oracle-db.sh
```

This script will:
- Create Oracle-specific database schema
- Set up Python dependencies
- Create migration scripts
- Generate configuration templates

### Step 4: Configure Oracle Connection

```bash
# Create Oracle configuration
./bin/setup-oracle-config.sh
```

Enter your Oracle database details when prompted:
- Database Name
- Username (usually `ADMIN`)
- Password
- Wallet Password
- Connection String (e.g., `ai-stock-dashboard_high`)

### Step 5: Initialize Database Schema

```bash
# Connect to your Oracle database and run the schema
sqlplus admin/your_password@ai-stock-dashboard_high @oracle-schema.sql
```

Or use SQL Developer / Oracle SQL Developer Web.

### Step 6: Test Connection

```bash
# Test the Oracle database connection
python test_oracle_db.py
```

You should see:
```
✅ Oracle database connection successful
✅ Admin config table accessible
✅ Users table accessible - 0 users found
🎉 All tests passed! Oracle database is ready for use.
```

### Step 7: Migrate Data (Optional)

If you have existing MongoDB data:

```bash
# Migrate from MongoDB to Oracle
python migrate_to_oracle.py
```

## 🔧 Configuration

### Environment Variables

Copy `.env.oracle.template` to `.env.oracle` and update:

```bash
cp .env.oracle.template .env.oracle
# Edit .env.oracle with your Oracle credentials
```

Key variables:
- `DATABASE_TYPE=oracle`
- `ORACLE_DB_NAME=your_db_name`
- `ORACLE_USERNAME=ADMIN`
- `ORACLE_PASSWORD=your_password`
- `ORACLE_CONNECTION_STRING=your_db_name_high`

### Oracle Wallet

Ensure your Oracle wallet files are in `./oracle-wallet/`:
```
oracle-wallet/
├── tnsnames.ora
├── sqlnet.ora
├── cwallet.sso
├── ewallet.p12
└── keystore.jks
```

## 🐳 Docker Deployment

### Development with Oracle

```bash
# Build and run with Oracle support
docker-compose -f docker-compose.oracle.yml up --build
```

This runs:
- Backend with Oracle connection on port 8001
- MongoDB (for migration) on port 27018

### Production Deployment

Update `docker-compose.prod.yml` to use Oracle:

```yaml
services:
  backend:
    environment:
      - DATABASE_TYPE=oracle
      - ORACLE_CONFIG_FILE=/app/oracle-config.json
    volumes:
      - ./oracle-config.json:/app/oracle-config.json:ro
      - ./oracle-wallet:/app/oracle-wallet:ro
```

## 📊 Database Schema

The Oracle schema includes:

### Tables
- **users** - User accounts and subscription info
- **admin_config** - Application configuration (replaces JSON file)
- **user_stocks** - User stock tracking
- **audit_logs** - Admin action logs
- **stock_data_cache** - Performance caching

### Features
- Auto-incrementing primary keys with sequences
- Foreign key constraints for data integrity
- Indexes for optimal query performance
- Triggers for automatic timestamp updates
- JSON storage for flexible configuration

## 🔄 Migration

### From MongoDB

The migration script handles:
- User accounts and authentication
- User stock tracking preferences
- Admin configuration settings
- Audit logs and system data

```bash
python migrate_to_oracle.py
```

### From File-based Config

Admin configuration automatically migrates from `admin_config.json` to Oracle on first run.

## 🛠️ Troubleshooting

### Connection Issues

1. **Wallet files not found**
   ```
   Error: Oracle wallet files not found
   ```
   - Ensure wallet files are in `./oracle-wallet/`
   - Check file permissions (readable by application)

2. **Invalid credentials**
   ```
   Error: ORA-01017: invalid username/password
   ```
   - Verify username and password in `oracle-config.json`
   - Check if user account is locked in Oracle

3. **Connection string issues**
   ```
   Error: ORA-12154: TNS:could not resolve the connect identifier
   ```
   - Verify connection string matches `tnsnames.ora`
   - Common formats: `dbname_high`, `dbname_medium`, `dbname_low`

### Performance Tuning

1. **Connection pooling**
   ```python
   # Adjust pool settings in database_oracle.py
   pool_size=10,
   max_overflow=20,
   pool_timeout=30
   ```

2. **Query optimization**
   - Use connection string suffixes:
     - `_high` - Maximum resources, low latency
     - `_medium` - Balanced resources
     - `_low` - Minimal resources, higher latency

### Monitoring

Monitor your Oracle Autonomous Database:
1. Go to OCI Console → Autonomous Database
2. Click on your database
3. Use **Performance Hub** for real-time metrics
4. Check **Database Actions** for SQL monitoring

## 🔒 Security Best Practices

1. **Credentials Management**
   - Store Oracle passwords in secure vault (OCI Vault, HashiCorp Vault)
   - Use environment variables, not hardcoded values
   - Rotate passwords regularly

2. **Network Security**
   - Use private endpoints when possible
   - Configure access control lists (ACLs)
   - Enable audit logging

3. **Wallet Security**
   - Keep wallet files secure and backed up
   - Use strong wallet passwords
   - Regenerate wallets if compromised

## 📈 Scaling

Oracle Autonomous Database auto-scales, but you can also:

1. **Manual scaling**
   - Adjust OCPU count in OCI console
   - Increase storage as needed

2. **Connection management**
   - Monitor connection pool usage
   - Adjust pool settings for high load

3. **Performance optimization**
   - Use appropriate service names (_high, _medium, _low)
   - Implement query result caching
   - Optimize database indexes

## 🤝 Support

For issues specific to:
- **Oracle Database**: Check Oracle Cloud Infrastructure documentation
- **Application**: Create an issue in this repository
- **Migration**: Run test scripts to validate data integrity

## 📚 Additional Resources

- [Oracle Autonomous Database Documentation](https://docs.oracle.com/en/cloud/paas/autonomous-database/)
- [Oracle Python Driver (oracledb)](https://python-oracledb.readthedocs.io/)
- [SQLAlchemy Oracle Dialect](https://docs.sqlalchemy.org/en/20/dialects/oracle.html)
- [Oracle Cloud Infrastructure](https://docs.oracle.com/en-us/iaas/Content/home.htm)

---

**Happy coding with Oracle! 🚀**
