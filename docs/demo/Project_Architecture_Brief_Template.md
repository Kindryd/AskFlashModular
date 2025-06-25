
# Project Architecture Brief - [Project Name]

## 1. Problem Statement

Briefly describe what your project aims to solve.  
Who are the users? What’s the business or technical goal?

**Example:**  
This project aims to provide an internal AI assistant capable of answering documentation-related queries.  
Primary users are internal developers and support staff.

---

## 2. Current High-Level Architecture

Describe the major components and how they interact.  
Use bullet points for clarity. You can optionally sketch a diagram.

**Example:**  
- Frontend: React-based UI  
- Backend: FastAPI  
- Vector Store: Qdrant  
- LLM API: OpenAI GPT-4o  
- Flow: User submits question → Backend → Vector DB → LLM (fallback) → Response

---

## 3. Key Technical Constraints & Decisions

List any technical decisions made so far, including limitations, stack choices, or requirements.

**Example:**  
- Using Docker for deployment  
- Postgres as primary DB  
- Must work offline if OpenAI API is unavailable

---

## 4. Key Pain Points or Uncertainties

Highlight where you want guidance. Be specific.

**Example:**  
- Unsure how to handle token limits when context is large  
- Whether multi-tenancy is feasible in current design  
- Need help selecting best practice for secret management

---

## 5. End Vision / Future Direction

Describe the desired end state for your project.

**Example:**  
- AI assistant with self-updating index of all internal docs  
- Configurable per-team context settings  
- Slack integration for Q&A from chat

---

## 6. [Optional] Architecture Diagram

You can insert a diagram here showing the flow of data or services.  
Even a simple sketch will help.

**[Insert diagram here]**
