# 📡 AskFlash Messaging Schema (Redis + RabbitMQ)

This document defines the structure of inter-service messaging across the MCP architecture, focusing on:
- Redis Keys (KV + Streams)
- Redis Pub/Sub Channels
- RabbitMQ Queues
- Event Payload Schemas

---

## 🔑 Redis Key-Value Conventions

| Key Format                        | Purpose                                 | TTL     |
|----------------------------------|------------------------------------------|---------|
| `task:{task_id}`                 | Stores full task DAG + status            | 10 mins |
| `task:{task_id}:context`         | AI context buffer (tokens, text)         | 10 mins |
| `task:{task_id}:vector_hits`     | Stores vector doc IDs from Qdrant        | 10 mins |
| `response:task:{task_id}`        | Final message with sources               | 10 mins |
| `user:{user_id}:session:{id}`    | UI-specific session state                | Optional|

---

## 📢 Redis Pub/Sub Channels

| Channel Name                     | Publisher                | Purpose                          |
|----------------------------------|---------------------------|----------------------------------|
| `ai:task:start`                 | frontend or gateway       | Signals MCP to begin a task      |
| `ai:progress:{task_id}`        | any container             | UI-safe updates for frontend     |
| `ai:plan:ready`                | preprocessor              | Emits sub-questions + task plan  |
| `ai:embedding:complete`        | embedding.container       | Vector search done               |
| `ai:execution:complete`        | executor.container        | Main LLM reasoning done          |
| `ai:moderation:pass`           | moderator.container       | Approval to finalize response    |
| `ai:response:ready`            | MCP                       | Ready to show to user            |

---

## 📬 Redis Streams

| Stream Key                      | Purpose                             |
|----------------------------------|--------------------------------------|
| `task:{task_id}:progress`       | AI thinking stages + decisions       |
| `task:{task_id}:log`            | System events (for analytics)        |

---

## 📦 RabbitMQ Queues

| Queue Name         | Consumed By           | Payload Description                      |
|--------------------|------------------------|------------------------------------------|
| `intent.task`      | preprocessor.container | `{ task_id, query, user_id }`            |
| `embedding.task`   | embedding.container    | `{ task_id, query }`                     |
| `executor.task`    | executor.container     | `{ task_id, query, context, docs }`      |
| `moderator.task`   | moderator.container    | `{ task_id, response }`                  |
| `websearch.task`   | web-search.container   | `{ task_id, query }`                     |

---

## 🧪 Payload Examples

### Example: ai:progress:{task_id} Event
```json
{
  "task_id": "abc123",
  "stage": "embedding_lookup",
  "message": "AI is retrieving relevant documents",
  "timestamp": "2025-06-27T10:02:01Z"
}
```

### Example: RabbitMQ executor.task Payload
```json
{
  "task_id": "abc123",
  "query": "Who are the SRE team members?",
  "context": "User is asking about org structure...",
  "docs": ["doc:123", "doc:456"]
}
```

---

This messaging schema enables seamless communication between agents, allows robust task coordination, and supports real-time UI feedback for an intelligent AI orchestration system.

