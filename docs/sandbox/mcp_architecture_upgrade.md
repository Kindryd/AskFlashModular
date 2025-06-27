# 🧠 MCP Architecture Upgrade Plan for AskFlash Modular

This document outlines the planned evolution of `ai-orchestrator.container` into a fully capable Master Control Program (`mcp.container`). It is designed to be understood and utilized by an AI assistant in Cursor IDE for autonomous implementation.

---

## 🎯 Objective

To implement an intelligent, event-driven orchestration layer that uses Redis, RabbitMQ, and Postgres to coordinate a multi-agent AI system for reasoning, moderation, embedding, and augmentation.

---

## 📦 New Container: mcp.container

### Purpose
- Acts as the central brain for AI reasoning coordination
- Dispatches tasks to agents
- Tracks state, progress, and context per task
- Emits progress updates to frontend via Redis

### Responsibilities
- Manage a Redis JSON record per task (context, stage, result)
- Execute and track a task DAG
- Route messages to RabbitMQ queues
- Listen to Redis events for task completions
- Emit user-readable progress events
- Handle retries or failures

---

## 📡 Communication Overview

### Redis
- `task:{task_id}:context` – KV store for AI working memory
- `task:{task_id}:progress` – Stream of progress updates
- `task:{task_id}` – Main task state (JSON)
- `user:{user_id}:task:{task_id}:events` – Frontend UI events

### RabbitMQ Queues
- `intent.task`
- `embedding.task`
- `executor.task`
- `moderator.task`
- `final_response.task`

### Events to Emit (Pub/Sub or Streams)
- `ai:task:start`
- `ai:plan:ready`
- `ai:embedding:complete`
- `ai:execution:complete`
- `ai:moderation:pass`
- `ai:response:ready`

---

## 🧠 Task DAG Example (Stored in Redis or Postgres)
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
  "current_stage": "intent_analysis",
  "status": "in_progress",
  "context": "...",
  "vector_hits": [],
  "response": null
}
```

---

## 🧩 Agent Containers

### preprocessor.container (Strategist)
- Input: Raw user query
- Output: Sub-questions, query expansion
- AI Model: GPT-3.5

### executor.container (Researcher)
- Input: Final question + vector hits
- Output: Full AI response
- AI Model: GPT-4o

### moderator.container (Editor)
- Input: Final AI output
- Output: Confidence rating, rewrite if needed
- AI Model: GPT-3.5 or 4o

### web-search.container (Optional)
- Input: Query string
- Output: Factual context + URLs
- API: DuckDuckGo / SerpAPI + LLM analysis

---

## 🧠 ReAct Format for GPT Prompts (Optional)
- Thought:
- Action:
- Observation:
- Thought:
- Final Answer:

---

## ✅ Summary

You are creating a modular, multi-agent, DAG-driven reasoning engine with:
- RabbitMQ for task dispatch
- Redis for context + progress
- Postgres for task history
- ReAct-style traceability

This document provides all the scaffolding the Cursor IDE AI needs to evolve the current orchestrator into a full MCP system.

