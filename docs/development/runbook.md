# Runbook

## Common Operations

### Deploying to Production

```bash
# 1. Pull latest changes
git pull origin main

# 2. Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 3. Run migrations
docker-compose exec backend python -c "
from db.migrations import run_migrations
import asyncio
asyncio.run(run_migrations())
"

# 4. Verify deployment
curl http://localhost:8000/api/v1/health
```

### Database Backups

```bash
# Create backup
docker exec mongodb mongodump --out=/backup/ai-underwriting-$(date +%Y%m%d)

# Restore backup
docker exec mongodb mongorestore /backup/ai-underwriting-20240101
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

### Scaling Services

```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3

# View running containers
docker-compose ps
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## Incident Response

### High CPU Usage

1. Check running processes:
   ```bash
   docker-compose exec backend top
   ```

2. Identify bottlenecks:
   - Check `/health` endpoint for system metrics
   - Review application logs for errors

3. Actions:
   - Scale down if needed
   - Check for stuck processes
   - Restart service if unresponsive

### Database Issues

1. Check MongoDB status:
   ```bash
   docker-compose exec mongo mongo --eval "db.adminCommand({ping: 1})"
   ```

2. Common issues:
   - Connection pool exhausted → Restart backend
   - Disk full → Clean up old documents
   - Slow queries → Check indexes

### Service Down

1. Check service status:
   ```bash
   docker-compose ps
   docker-compose logs backend
   ```

2. Recovery steps:
   - Check `/health/live` endpoint
   - Review error logs
   - Restart service: `docker-compose restart backend`

## Monitoring

### Key Metrics

| Metric | Healthy Range | Action Required |
|--------|---------------|-----------------|
| CPU | < 80% | Scale if consistently high |
| Memory | < 80% | Restart if high |
| Disk | < 80% | Clean up old documents |
| Response Time | < 500ms | Optimize queries |
| Error Rate | < 1% | Investigate errors |

### Health Check Commands

```bash
# Overall health
curl http://localhost:8000/api/v1/health

# Liveness (is running)
curl http://localhost:8000/api/v1/health/live

# Readiness (can serve traffic)
curl http://localhost:8000/api/v1/health/ready

# Metrics
curl http://localhost:8000/api/v1/health/metrics
```

## Rollback Procedure

If deployment fails:

```bash
# Revert to previous version
git checkout <previous-commit>

# Rebuild and restart
docker-compose up -d --build backend

# Verify health
curl http://localhost:8000/api/v1/health
```

## Performance Tuning

### Backend

- Increase `MAX_WORKERS` in settings
- Optimize MongoDB queries
- Add connection pooling

### Database

- Monitor with MongoDB Profiler
- Ensure indexes exist
- Consider replica set for high availability

### Frontend

- Enable gzip compression
- Use CDN for static assets
- Implement lazy loading
