# Troubleshooting Guide

## Backend Issues

### MongoDB Connection Failed

**Symptom:**
```
pymongo.errors.ServerSelectionTimeoutError: mongodb://localhost:27017: server
```

**Solutions:**
1. Verify MongoDB is running:
   ```bash
   docker ps | grep mongo
   # or
   ps aux | grep mongod
   ```

2. Check MongoDB port:
   ```bash
   curl http://localhost:27017
   ```

3. Restart MongoDB:
   ```bash
   docker-compose restart mongo
   ```

### OCR Processing Fails

**Symptom:**
```
Error processing PDF: ...
```

**Solutions:**
1. Verify Tesseract installation:
   ```bash
   tesseract --version
   ```

2. Verify Poppler installation:
   ```bash
   pdftoppm -v
   ```

3. Check file permissions:
   ```bash
   ls -la backend/uploads/
   chmod 755 backend/uploads/
   ```

### JWT Token Invalid

**Symptom:**
```
401 Unauthorized: Could not validate credentials
```

**Solutions:**
1. Check token expiration
2. Verify `SECRET_KEY` matches
3. Clear browser storage and re-login

### File Upload Fails

**Symptom:**
```
500 Internal Server Error: Failed to save file
```

**Solutions:**
1. Check disk space:
   ```bash
   df -h
   ```

2. Verify upload directory exists:
   ```bash
   ls -la backend/uploads/
   mkdir -p backend/uploads
   ```

3. Check file size limit (50MB max)

## Frontend Issues

### CORS Error

**Symptom:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solutions:**
1. Check API URL in frontend `.env`:
   ```
   VITE_API_URL=http://localhost:8000/api/v1
   ```

2. Verify CORS settings in backend:
   ```python
   # backend/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       ...
   )
   ```

### Authentication Not Working

**Symptom:**
- Login doesn't redirect
- Token not stored

**Solutions:**
1. Check browser console for errors
2. Verify localStorage is enabled
3. Clear application storage:
   - Open DevTools → Application → Clear storage

### Build Fails

**Symptom:**
```
npm run build fails
```

**Solutions:**
1. Clear node_modules:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Check Node.js version:
   ```bash
   node --version  # Should be 18+
   ```

3. Check for TypeScript errors:
   ```bash
   npm run typecheck
   ```

## Docker Issues

### Container Won't Start

**Symptom:**
```
Container fails to start
```

**Solutions:**
1. Check logs:
   ```bash
   docker-compose logs backend
   ```

2. Check port conflicts:
   ```bash
   lsof -i :8000
   ```

3. Rebuild container:
   ```bash
   docker-compose build --no-cache backend
   ```

### Out of Memory

**Symptom:**
```
OCI runtime process failed
```

**Solutions:**
1. Increase Docker memory limit (Settings → Resources)
2. Scale down services:
   ```bash
   docker-compose up -d --scale backend=1
   ```

### Volume Not Mounting

**Symptom:**
Files not visible in container

**Solutions:**
1. Check volume mount:
   ```bash
   docker-compose config | grep volumes
   ```

2. Recreate volumes:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

## Performance Issues

### Slow API Responses

**Solutions:**
1. Check database indexes:
   ```javascript
   db.documents.getIndexes()
   ```

2. Monitor query performance:
   ```javascript
   db.setProfilingLevel(1)
   db.system.profile.find().limit(10)
   ```

3. Add MongoDB connection pooling

### High Memory Usage

**Solutions:**
1. Restart services:
   ```bash
   docker-compose restart backend
   ```

2. Clean up old documents:
   ```python
   from services.cleanup import FileCleanupService
   cleanup = FileCleanupService()
   cleanup.cleanup_expired_documents(db)
   ```

## Error Log Analysis

### Finding Errors

```bash
# Backend logs
docker-compose logs backend 2>&1 | grep -i error

# Last 100 lines with errors
docker-compose logs --tail=100 backend | grep -i error

# Follow logs in real-time
docker-compose logs -f backend | grep -i error
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionRefusedError` | MongoDB not running | Start MongoDB |
| `FileNotFoundError` | File path wrong | Check file paths |
| `ValidationError` | Invalid input | Check request data |
| `HTTPException: 404` | Resource not found | Verify ID exists |
| `HTTPException: 500` | Server error | Check logs |

## Getting Help

1. Check existing issues on GitHub
2. Review application logs
3. Check monitoring dashboards
4. Run health checks:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
