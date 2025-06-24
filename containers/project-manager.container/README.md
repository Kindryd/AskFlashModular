# project-manager.container

## 📌 Purpose
Handles notifications, external ticketing systems, and project management integrations. Manages workflows, task creation, and external system synchronization.

## 🔗 DB Tables Used
### Write:
- (none - writes to external systems)

### Read-only:
- `rulesets` - Integration configurations
- `users` - User notification preferences
- `conversation_histories` - Context for task creation

## 🔁 Communication
### API:
- `POST /api/projects/notify` - Send notifications
- `POST /api/projects/tickets` - Create external tickets
- `GET /api/projects/integrations` - List project integrations
- `POST /api/projects/sync` - Sync with external systems

### Redis:
- **Emits**: `project:ticket_created`, `project:notification_sent`
- **Subscribes**: `conversation:action_required`, `ai:task_identified`

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
JIRA_URL=${JIRA_URL}
JIRA_TOKEN=${JIRA_TOKEN}
TEAMS_WEBHOOK_URL=${TEAMS_WEBHOOK_URL}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
NOTIFICATION_QUEUE_SIZE=1000
```

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/project-manager .
docker run --env-file .env askflash/project-manager
``` 