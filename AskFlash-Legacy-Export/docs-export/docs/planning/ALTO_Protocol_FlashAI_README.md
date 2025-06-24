# ALTO (AI Low-Level Task Operations) Protocol for Flash AI

## 📌 Overview

This README defines the development plan for building **ALTO**, a compact symbolic language to efficiently communicate with AI models like GPT-4o through an API. It is meant to **replace verbose natural language instructions** with short, symbolic, machine-oriented operations, enabling better performance, easier interpretation, and lower token cost.

Your job is to create:
- An ALTO encoder/decoder module
- A prompt template for interpreting ALTO commands
- Optional embedding format for Qdrant knowledge storage

---

## 🎯 Goals

- Eliminate natural language ambiguity in internal AI communication
- Reduce token usage by replacing English with symbolic ops
- Maintain full compatibility with GPT-4o and OpenAI API (no fine-tuning required)
- Store and retrieve instructions/responses efficiently in Qdrant

---

## 🧠 ALTO Instruction Format

ALTO is a simple, symbolic language that encodes AI tasks.

### Example

```
v1
CMD:FA
Q:rst_MFA
CTX:AG3,MP
FMT:STP
U:SU
L:EN
```

### Meaning

| Symbol | Meaning |
|--------|---------|
| `CMD`  | Command: FA = fetch_answer, EX = explain, GC = generate_code, PL = plan, DI = diagnose |
| `Q`    | Query in keyword form (e.g. rst_MFA = reset MFA) |
| `CTX`  | Context document codes (e.g. AG3 = auth_guide_v3, MP = mfa_policy) |
| `FMT`  | Format: STP = step-by-step, SUM = summary, LIS = list, FLW = flow |
| `U`    | User role: SU = support_agent, EN = engineer, HR = HR staff |
| `L`    | Language: EN = English, PY = Python, JS = JavaScript |

---

## 🛠️ Development Tasks

### 1. `alto_codec.py` – ALTO Encoder/Decoder

- `encode(json_dict: dict) -> str`  
  Converts structured task JSON to ALTO string

- `decode(alto_str: str) -> dict`  
  Converts ALTO string back to structured JSON

- Validate against known opcode sets and raise errors for unknown values

---

### 2. `alto_prompt_builder.py` – GPT Prompt Constructor

- `def build_prompt(alto_str: str, context_chunks: List[str]) -> str`

Constructs a GPT-friendly prompt using the following template:

---

## 🧠 ALTO Interpreter Prompt Template

```
You are Flash's internal AI assistant. Interpret the following ALTO (AI Low-Level Task Operation) instruction and execute it.

ALTO defines symbolic commands for efficient task communication:
- CMD:FA = fetch answer
- CMD:EX = explain
- CMD:GC = generate code
- CMD:PL = plan
- CMD:DI = diagnose
- FMT:STP = step-by-step, SUM = summary, LIS = list, FLW = flow
- CTX codes refer to internal documentation modules
- Q = keyword query
- U = user role
- L = output language or format

ALTO Instruction:
{alto_str}

Documentation Context:
{retrieved_chunks}

Respond only in the format specified by FMT.
```

---

### 3. `alto_runner.py` – Execution Module

- Accepts user query in JSON or ALTO format
- If JSON: encode to ALTO
- Retrieve context from Qdrant using `CTX` codes
- Call OpenAI with constructed prompt
- Return AI response to frontend or API caller

---

### 4. Optional: ALTO for Embedding in Qdrant

When storing resolved tasks or documents in Qdrant:

- Store ALTO strings as keys/metadata (e.g., `CMD:FA|Q:rst_MFA|CTX:AG3,MP`)
- Embed both query and answer as vectors
- Use cosine similarity on `Q` and `CTX` fields to retrieve efficient matches

This allows **machine-level recall** of previous tasks with near-zero token overhead.

---

## 📂 Suggested File Structure

```
/flash-ai-alto
  ├── alto_codec.py
  ├── alto_prompt_builder.py
  ├── alto_runner.py
  ├── tests/
  │   ├── test_alto_codec.py
  │   └── test_prompt_builder.py
  └── README.md
```

---

## ✅ Deliverables Checklist

- [ ] Encoder/decoder for ALTO ↔ JSON
- [ ] Prompt builder using interpreter template
- [ ] Integration with OpenAI API
- [ ] Context loader from Qdrant using `CTX:` symbols
- [ ] Test suite with example inputs/outputs

---

## 🧠 Final Notes for Cursor IDE AI

- Follow this protocol as the new communication standard for Flash’s internal AI tools
- Make it efficient, modular, and easy to extend with new opcodes
- Begin with just `fetch_answer`, `explain`, and `generate_code`
- Validate with short test prompts to confirm GPT-4o correctly interprets ALTO