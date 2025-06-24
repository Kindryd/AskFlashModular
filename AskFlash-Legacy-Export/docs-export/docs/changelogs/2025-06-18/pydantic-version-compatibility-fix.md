# Pydantic Version Compatibility Fix - OpenAPI Schema Generation

**Date**: 2025-06-18  
**Type**: Critical Bug Fix  
**Priority**: Critical  
**Status**: ✅ Resolved

## Issue Description

The Swagger UI documentation at `localhost:8000/docs` was failing with a server error, and accessing `/openapi.json` was returning a 500 Internal Server Error. The backend logs showed:

```
TypeError: No method for generating JsonSchema for core_schema.type='invalid' (expected: GenerateJsonSchema.invalid_schema)
```

This error occurred when FastAPI tried to generate the OpenAPI schema for the Swagger documentation.

## Root Cause Analysis

The issue was caused by **Pydantic version 2.9.2**, which has a known bug with schema generation that affects FastAPI's OpenAPI generation. The error `core_schema.type='invalid'` is a characteristic symptom of this Pydantic version bug.

**Investigation Process:**
1. Initially suspected datetime timezone issues in models/schemas
2. Fixed timezone-related issues but problem persisted
3. Systematically disabled API routes and model imports
4. Even with minimal FastAPI app, the error persisted
5. Checked container package versions: discovered Pydantic 2.9.2
6. Identified this as a known compatibility issue

## Solution Applied

**Downgraded Pydantic to compatible version:**
- **Before**: `pydantic==2.9.2` and `pydantic_core==2.27.1`
- **After**: `pydantic==2.8.2` and `pydantic_core==2.20.1`

**Steps taken:**
1. Updated `backend/requirements-base.txt`
2. Rebuilt Docker container with `--no-cache`
3. Restored all original imports and functionality
4. Verified fix by testing OpenAPI endpoints

## Files Modified

### `backend/requirements-base.txt`
```diff
- pydantic==2.9.2
+ pydantic==2.8.2
- pydantic_core==2.27.1
+ pydantic_core==2.20.1
```

## Verification Steps

✅ **OpenAPI Schema Generation**: `http://localhost:8000/openapi.json` returns valid JSON schema  
✅ **Swagger UI Access**: `http://localhost:8000/docs` loads properly  
✅ **Health Check**: `http://localhost:8000/health` returns `{"status": "healthy"}`  
✅ **All Services Running**: All Docker containers healthy and operational  
✅ **Backend Startup**: No errors in backend container logs  

## Testing Results

```bash
# OpenAPI Schema Test
$ Invoke-RestMethod -Uri "http://localhost:8000/openapi.json" -Method Get
# Returns: Valid OpenAPI 3.1.0 schema

# Swagger UI Test  
$ Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method Get
# Returns: Full HTML page with Swagger UI

# Health Check Test
$ Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
# Returns: {"status": "healthy"}
```

## Container Status
All services now running healthy:
- ✅ `askflash-backend-1` - Up and healthy
- ✅ `askflash-db-1` - Up and healthy  
- ✅ `askflash-frontend-1` - Up and running
- ✅ `askflash-qdrant-1` - Up and running
- ✅ `askflash-adminer-1` - Up and running

## Impact

- **Swagger UI Documentation**: Now fully accessible for API testing and exploration
- **OpenAPI Schema**: Properly generated for all endpoints and models
- **Developer Experience**: API documentation and testing capabilities restored
- **Production Readiness**: Critical API documentation functionality working

## Future Prevention

- **Version Pinning**: Keep Pydantic pinned to tested compatible versions
- **Compatibility Testing**: Test major dependency updates in isolation
- **Container Rebuilds**: Use `--no-cache` for dependency changes
- **Systematic Debugging**: Follow methodical approach to isolate issues

## Related Issues Fixed

This fix also resolved the secondary datetime timezone compatibility issues that were discovered during the investigation process.

## Notes

- Pydantic 2.9.x series has known schema generation bugs
- FastAPI 0.110.0 + Pydantic 2.8.2 is a stable combination
- This fix ensures proper functionality for subsequent full rebuilds
- All functionality restored to working state after the downgrade 