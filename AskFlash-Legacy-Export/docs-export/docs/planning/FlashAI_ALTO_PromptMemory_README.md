# Flash AI - ALTO Prompt Memory & Instruction Layer

## 📌 Overview

This README outlines how to implement a **prompt memory strategy** for the ALTO protocol in Flash's AI system, ensuring that GPT-3.5 and GPT-4o can reliably interpret and use ALTO instructions without repeating full definitions every time.

The goal is to enable GPT models to consistently understand ALTO without increasing token usage or requiring fine-tuning.

---

## 🎯 Goals

- Ensure GPT-3.5 (intent layer) reliably translates English ↔ ALTO
- Ensure GPT-4o (executor layer) can interpret ALTO efficiently
- Avoid prompt bloat with minimal reusable few-shot examples
- Enable symbolic instruction processing at low cost and high consistency

---

## 🧠 Strategy Overview

| Component | Purpose |
|----------|---------|
| Prompt Header | Gives GPT a compact explanation of ALTO |
| Few-Shot Examples | Teaches GPT the conversion pattern |
| Wrapper Function | Automatically prepends prompt and examples |
| Optional Function Calling | Forces JSON output structure |
| RAG Support | Dynamically retrieves prompt memory if needed |

---

## 🛠 Tasks to Implement

### 1. `prompt_template.py`

#### `get_alto_translation_prompt(user_input: str) -> str`
- Includes a short ALTO description + few-shot examples + user input.
- Used by GPT-3.5 to translate natural language to ALTO.

#### Template:

```
You are a system that converts English questions into a symbolic instruction language called ALTO.

ALTO uses short codes:
- CMD:FA = fetch_answer, GC = generate_code, EX = explain
- Q = short keyword-form topic (e.g., rst_MFA)
- CTX = source document codes (e.g., AG3 = auth_guide_v3)
- FMT = output format: STP = step-by-step, SUM = summary, PY = Python code
- U = user role (SU = support agent, EN = engineer)
- L = output language (EN = English, PY = Python)

Examples:

Input: How do I reset my MFA?
Output:
CMD:FA
Q:rst_MFA
CTX:AG3,MP
FMT:STP
U:SU
L:EN

Input: Generate a Python script to delete old tokens.
Output:
CMD:GC
Q:del_tokens_py
CTX:TK2
FMT:PY
U:EN
L:PY

Input: {user_input}
Output:
```

### 2. `intent_parser.py`

- `def parse_to_alto(question: str) -> str:`
  - Uses `get_alto_translation_prompt()`, sends to GPT-3.5 Turbo
- `def translate_from_alto(alto_response: str, original_question: str) -> str:`
  - Translates back to user-friendly text

### 3. `alto_prompt_builder.py` (GPT-4o executor)

#### `build_prompt(alto: str, context: List[str]) -> str`
Use this format:

```
You are Flash's internal AI assistant. Interpret the following ALTO instruction:

ALTO defines symbolic commands for task execution:
CMD = command, Q = query topic, CTX = doc references, FMT = format, U = user role, L = language

Instruction:
{ALTO}

Documentation Context:
{context}

Respond in the format specified by FMT.
```

---

## 📂 File Structure

```
/flash-ai-alto
  ├── intent_parser.py
  ├── prompt_template.py
  ├── alto_prompt_builder.py
  └── tests/
      └── test_prompt_templates.py
```

---

## ✅ Deliverables

- [ ] `prompt_template.py` with reusable ALTO translation prompt
- [ ] `intent_parser.py` with translation logic for GPT-3.5
- [ ] `alto_prompt_builder.py` for GPT-4o instructions
- [ ] Test suite for validating prompt conversions

---

## 🧠 Final Notes for Cursor IDE AI

- Reuse the same 2–3 few-shot examples for ALTO training.
- Design functions to be called from higher-level orchestrators (`alto_runner.py`).
- ALTO is the default protocol for all Flash AI system communications.