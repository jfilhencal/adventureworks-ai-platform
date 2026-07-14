# Phase 1: SQL Server Integration Setup Guide

## Prerequisites

- SQL Server installed locally or accessible remotely
- AdventureWorksDW2019 (or similar) sample database installed
- ODBC Driver 18 for SQL Server installed
- Python 3.11+

## Installation Steps

### 1. Install ODBC Driver

**Windows:**
Download and install the [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install msodbcsql18 mssql-tools18
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
apt-get install -y msodbcsql18
```

### 2. Configure Database Connection

Edit `backend/.env` with your SQL Server details:

```bash
# Example for local SQL Server Express
SQL_SERVER=localhost\SQLEXPRESS
SQL_DATABASE=AdventureWorksDW2019
SQL_USER=sa
SQL_PASSWORD=YourPassword123!

# Azure OpenAI (leave blank for now)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_API_KEY=
```

### 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the Application

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
2026-07-10 15:30:00 - app.main - INFO - Starting AdventureWorks AI Platform API in development mode
2026-07-10 15:30:01 - app.core.database - INFO - Database connection verified
```

## Test Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "backend",
  "database": "ok"
}
```

### Sales Summary
```bash
curl http://localhost:8000/sales/summary
```

Response:
```json
{
  "total_revenue": 29358677.2207,
  "total_orders": 60398,
  "average_order_value": 486.0456
}
```

### Monthly Sales
```bash
curl http://localhost:8000/sales/monthly
```

Response:
```json
[
  {"month": "2010-07", "revenue": 348261, "orders": 113},
  {"month": "2010-08", "revenue": 526619, "orders": 172},
  ...
]
```

## Features Implemented

✅ SQLAlchemy ORM integration  
✅ Connection pooling with QueuePool  
✅ pyodbc driver for SQL Server  
✅ Error handling and logging  
✅ Repository pattern  
✅ Service layer pattern  
✅ Dependency injection  
✅ Startup verification of database connectivity  
✅ Rotating file and console logging  

## Logs

Application logs are written to:
- Console output (INFO and above)
- `backend/logs/app.log` (rolling file, 10 MB max)

Third-party loggers (sqlalchemy, urllib3) are suppressed to INFO level for cleaner output.

## Troubleshooting

### "pyodbc.Error: ('IM002', '[IM002] [Microsoft][ODBC Driver Manager] Data source name not found and no default driver specified')"

**Solution:** Install the ODBC Driver 18 for SQL Server and ensure it's registered in the system.

### "Connection refused" or "Timeout"

**Solution:** Check that your SQL Server is running and accessible:
```bash
# Windows: Test connection with sqlcmd
sqlcmd -S localhost\SQLEXPRESS -U sa -P YourPassword123!

# Linux/macOS: Test connection with sqlcmd
sqlcmd -S localhost,1433 -U sa -P YourPassword123!
```

### "Login failed for user 'sa'"

**Solution:** Verify credentials in `.env` and that SQL Server Authentication is enabled.

## Next Steps (Phase 2)

- Add forecasting endpoints using Prophet
- Integrate Azure AI Foundry for chat and analytics
- Add more business metrics and dimensions
