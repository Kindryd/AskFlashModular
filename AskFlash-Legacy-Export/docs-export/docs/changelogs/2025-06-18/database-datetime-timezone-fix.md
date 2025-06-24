# Database DateTime Timezone Fix

**Date**: 2025-06-18  
**Type**: Bug Fix  
**Priority**: Critical  
**Status**: ✅ Resolved

## Issue Description

After a clean Docker rebuild (no cache), the backend application was failing to start with a database datetime timezone error:

```
sqlalchemy.exc.DBAPIError: <class 'asyncpg.exceptions.DataError'>: invalid input for query argument $12: datetime.datetime(2025, 6, 18, 14, 52, 1... (can't subtract offset-naive and offset-aware datetimes)
```

The error occurred during application startup when trying to create the default ruleset, specifically with the `created_at` and `updated_at` timestamp fields.

## Root Cause Analysis

1. **Database Schema Mismatch**: PostgreSQL columns were defined as `TIMESTAMP WITHOUT TIME ZONE` but the application was trying to insert timezone-aware datetime objects
2. **Lambda Functions in Defaults**: The `TimestampMixin` was using lambda functions in `default` parameters, which causes issues with Pydantic v2
3. **Conflicting Column Definitions**: Both `Base` class and `TimestampMixin` were defining timestamp columns

## Solution Implemented

### 1. Fixed Database Model (`backend/app/models/base.py`)

**Before:**
```python
class Base(DeclarativeBase):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
```

**After:**
```python
def utc_now():
    """Get current UTC datetime as naive datetime (for TIMESTAMP WITHOUT TIME ZONE columns)"""
    return datetime.utcnow()

class Base(DeclarativeBase):
    id = Column(Integer, primary_key=True, index=True)

class TimestampMixin:
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
```

### 2. Database Schema Reset

- Cleaned database schema: `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
- Ran fresh migrations: `alembic upgrade head`

### 3. Key Fixes Applied

1. **Proper Function References**: Replaced lambda functions with proper function references (`utc_now`)
2. **Naive DateTime**: Changed from `datetime.now(timezone.utc)` to `datetime.utcnow()` to match PostgreSQL's `TIMESTAMP WITHOUT TIME ZONE`
3. **Removed Duplicate Columns**: Removed timestamp columns from `Base` class to avoid conflicts
4. **Pydantic v2 Compliance**: Followed codebase rules for Pydantic v2 compatibility

## Migration Process

1. **Clean Database**: Used correct PostgreSQL credentials (`postgres` user, not `askflash`)
2. **Schema Reset**: Completely dropped and recreated the public schema
3. **Fresh Migrations**: Applied all Alembic migrations from scratch
4. **Service Restart**: Restarted backend container to apply fixes

## Verification

✅ Backend application starts successfully  
✅ Health endpoint responds: `{"status": "healthy"}`  
✅ All Docker services running properly:
- askflash-backend-1: Running (healthy)
- askflash-db-1: Up (healthy)
- askflash-frontend-1: Up
- askflash-qdrant-1: Up
- askflash-adminer-1: Up

## Technical Details

- **Database**: PostgreSQL 13 with `TIMESTAMP WITHOUT TIME ZONE` columns
- **ORM**: SQLAlchemy with AsyncPG driver
- **Migration Tool**: Alembic
- **Compliance**: Pydantic v2, Codebase conventions

## Prevention Measures

1. **Datetime Best Practices**: Always use naive datetime objects for PostgreSQL `TIMESTAMP WITHOUT TIME ZONE`
2. **Function References**: Avoid lambda functions in SQLAlchemy column defaults
3. **Consistent Schema**: Ensure model definitions match database column types
4. **Testing**: Test application startup after clean builds

## Files Modified

- `backend/app/models/base.py` - Fixed datetime handling and column definitions

## Commands Used

```bash
# Clean database
docker-compose exec db psql -U postgres -d askflash -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Restart services
docker-compose restart backend

# Verify health
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```

This fix ensures the application will work correctly in subsequent full rebuilds and maintains compatibility with the Pydantic v2 upgrade. 