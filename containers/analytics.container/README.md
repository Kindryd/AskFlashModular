# analytics.container

## 📌 Purpose
Collects logs, events, and analytics data from all services. Provides monitoring, reporting, and operational insights for the AskFlash platform.

## 🔗 DB Tables Used
### Write:
- (writes to S3/file storage, not DB)

### Read-only:
- `users` - User metadata for analytics
- `conversation_histories` - Usage pattern analysis

## 🔁 Communication
### API:
- `POST /api/analytics/events` - Receive analytics events
- `GET /api/analytics/metrics` - Get system metrics
- `GET /api/analytics/reports` - Generate usage reports
- `GET /api/analytics/health` - Service health metrics

### Redis:
- **Emits**: `analytics:report_generated`, `analytics:alert_triggered`
- **Subscribes**: `*` (listens to all events for analytics)

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
S3_BUCKET=${ANALYTICS_S3_BUCKET}
S3_ACCESS_KEY=${S3_ACCESS_KEY}
S3_SECRET_KEY=${S3_SECRET_KEY}
LOG_RETENTION_DAYS=90
METRICS_AGGREGATION_INTERVAL=300
ALERT_THRESHOLD_ERROR_RATE=0.05
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/analytics .
docker run --env-file .env askflash/analytics
``` 