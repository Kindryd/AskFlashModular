# 📘 MCP Task DAG Specification

This document defines the structure, stages, and transition logic for task execution within the MCP (`mcp.container`) system. It enables the Cursor IDE AI to generate and reason through dynamic task plans for distributed container coordination.

---

## 🧠 DAG Definition Schema
Each AI task is represented as a DAG (Directed Acyclic Graph). Stored as a JSON object in Redis or Postgres.

```json
{
  "task_id": "abc123",
  "user_id": "user-001",
  "query": "Who are the SRE team members?",
  "plan": [
    "intent_analysis",
    "embedding_lookup",
    "executor_reasoning",
    "moderation",
    "response_packaging"
  ],
  "current_stage": "embedding_lookup",
  "completed_stages": ["intent_analysis"],
  "status": "in_progress",
  "context": "...",
  "vector_hits": ["doc:1", "doc:2"],
  "response": null,
  "error": null,
  "started_at": "...",
  "updated_at": "..."
}
```

---

## 🔁 Valid Task Stages (DAG Nodes)

1. **intent_analysis**  → Uses GPT-3.5 to break down and clarify the user’s query.
2. **embedding_lookup** → Queries Qdrant via embedding.container.
3. **executor_reasoning** → Uses GPT-4o to reason over query and documents.
4. **moderation** → Uses GPT-3.5 or 4 to validate tone, logic, structure.
5. **web_search** *(optional)* → Augments with live search if needed.
6. **response_packaging** → Assembles final message + metadata for frontend.

---

## 🧭 DAG Traversal Logic
- MCP always starts with `intent_analysis`
- If a stage is marked `completed`, MCP proceeds to the next
- If any stage fails, retry once; else, mark task as `failed`
- If `moderation` fails confidence threshold, MCP re-invokes `executor_reasoning`
- `web_search` is conditionally inserted if executor requests it

---

## 🧩 DAG Storage Locations
- **Redis**: Primary for active task DAGs (`task:{id}`)
- **Postgres**: Archival / audit log

---

## ⏱ Status Field Values
| Status          | Meaning                                 |
|------------------|-------------------------------------------|
| `in_progress`    | Task running                            |
| `waiting`        | Task waiting for container to pick up   |
| `failed`         | Terminal failure, no more retries       |
| `complete`       | All steps completed                     |
| `aborted`        | Task manually cancelled                 |

---

This document enables the MCP to coordinate agents across RabbitMQ and Redis while making logical decisions about flow and fault recovery.

