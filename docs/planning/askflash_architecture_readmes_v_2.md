# 🧱 AskFlash Unified Architecture & README Scaffolds (DB-Shared Model)

This version reflects the revised decision to use a **single shared Postgres database** with logical table ownership per container, instead of one database per service.

---

## 📦 Containers Overview

| Container                   | Role                                   | DB Tables Owned                              | Notes                                |
| --------------------------- | -------------------------------------- | -------------------------------------------- | ------------------------------------ |
| `conversation.container`    | Chat sessions, messaging history       | `conversation_histories`, `frequent_queries` | Calls `embedding`, `ai-orchestrator` |
| `embedding.container`       | Vector generation, context enhancement | `wikis`, `wiki_page_indexes`                 | Writes to Qdrant                     |
| `project-manager.container` | Notifications, external ticketing      | (reads `rulesets`, `users`)                  | No table ownership                   |
| `ai-orchestrator.container` | AI access control, routing             | `rulesets`, `integrations`                   | Interfaces with OpenAI & `local-llm` |
| `adaptive-engine.container` | User learning & behavior tracking      | `user_habbits` (writes), `users` (reads)     | Pushes insight to analytics/Qdrant   |
| `local-llm.container`       | Hosts local LLMs (e.g. Mistral)        | N/A                                          | API-mimic of OpenAI                  |
| `analytics.container`       | Collects logs & events                 | (writes to S3/file, not DB)                  | Passive consumer                     |
| `gateway.container`         | Reverse proxy                          | N/A                                          | Forwards all traffic                 |
| `adminer.container`         | DB management GUI                      | Full DB access                               | For manual inspection                |
| `qdrant.container`          | Embedding storage                      | N/A                                          | Managed externally                   |

---

## 🔁 Communication Highlights

### Sync (HTTP API)

- `conversation.container` ↔ `embedding.container`
- `conversation.container` ↔ `ai-orchestrator.container`
- `ai-orchestrator.container` ↔ `local-llm.container`

### Async (Redis Events)

- All containers emit analytics events
- `adaptive-engine.container` listens to user behavior
- `embedding.container` publishes `embedding:generated`

---

## 🧠 Shared Database Model

- **Single Postgres DB** (e.g. `askflashdb`)
- Each container **accesses only its own tables for write**
- Cross-service data is **accessed via API or with read-only access/view**

---

## 📘 README Scaffolding Template (per container)

````markdown
# <container-name>.container

## 📌 Purpose
Describe this container's responsibility.

## 🔗 DB Tables Used
- Write: <list>
- Read-only: <list>

## 🔁 Communication
### API:
- `/api/...` ← internal or public access
### Redis:
- Emits: `<topic>`
- Subscribes: `<topic>`

## ⚙️ Configuration
```env
POSTGRES_URL=postgresql://user:pass@postgres/askflashdb
REDIS_URL=redis://redis:6379
````

## 🧪 Testing

```bash
pytest tests/
```

## 🐳 Docker

```bash
docker build -t askflash/<container-name> .
docker run --env-file .env askflash/<container-name>
```

```

Let me know if you want the `README.md` content re-generated for each container individually using this updated pattern.

```
