# Autonomous Coder Agent 🤖

**Local-First Agentic System for Automated Software Repair & Contextual Code Base Search**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Qwen2.5--Coder-black.svg)
![LangChain](https://img.shields.io/badge/LangChain-Orchestration-1C3C3C.svg)
![LanceDB](https://img.shields.io/badge/LanceDB-Vector_Database-000000.svg)
![Pytest](https://img.shields.io/badge/Pytest-Sandbox_Testing-0A9EDC.svg?logo=pytest&logoColor=white)

> An autonomous, privacy-preserving AI Software Engineer built to diagnose, repair, and verify codebases locally without cloud API dependencies or recurring execution costs.

---

##  Overview

The **Autonomous Coder Agent** is a local agentic software repair engine designed to tackle non-deterministic code modification tasks. Built on a **ReAct (Reason → Act → Observe)** loop, the system interfaces with local file systems, executes codebase search via vector embeddings, applies targeted code patches, and validates fixes in a closed-loop sandbox harness using `pytest`.

Running entirely on local open-weights infrastructure via **Ollama (`qwen2.5-coder:7b`)**, the project addresses common local model constraints (such as multi-call hallucinations or broken JSON schemas) through custom fallback parsers and single-action turn enforcement.

---

## Key Features

- **Local ReAct Control Loop:** Iterative reasoning-action cycle where the model plans actions, executes tools, observes feedback, and refines fixes.
- **Codebase Vector Search (RAG):** Local semantic indexing using **LanceDB** and HuggingFace embeddings (`all-MiniLM-L6-v2`) to query files based on architectural intent.
- **MCP-Style Tool Integration:** Modular execution tools (`read_file`, `write_file`, `run_tests`, `search_codebase`) bridging LLM output directly to OS operations.
- **Closed-Loop Test Sandboxing:** Runs unit test suites via Python `subprocess`, feeding terminal `pytest` logs back to the agent history until a green suite is achieved.
- **Local Model Failure Mitigation:** Built-in JSON balanced-brace text parser (`extract_first_json_call`) to reliably capture tool invocations from small open-weights models.

---

##  Architecture & Control Flow

```
┌────────────────────────────────────────────────────────┐
│                   Autonomous Loop                      │
│                                                        │
│  ┌───────────┐    1. Prompt/History    ┌────────────┐  │
│  │           │ ──────────────────────> │ Local LLM  │  │
│  │   Agent   │                         │  (Ollama/  │  │
│  │ Engine    │ <────────────────────── │  Qwen 2.5) │  │
│  │ (Python)  │    2. Thought + Action  └────────────┘  │
│  └─────┬─────┘                                         │
│        │                                               │
│        │ 3. Execute Tool                               │
│        ▼                                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │                   MCP Tools                      │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │  │
│  │  │search_codebase│ │ read/write   │ │ run_tests │ │  │
│  │  │  (LanceDB)   │ │    files     │ │ (pytest)  │ │  │
│  │  └──────────────┘ └──────────────┘ └───────────┘ │  │
│  └─────────────────────────┬────────────────────────┘  │
│                            │                           │
│                            │ 4. Observation / Feedback │
│                            └───────────────────────────┘
└────────────────────────────────────────────────────────┘
```

1. **Indexing Phase:** Code files are embedded into dense 384-dimensional vector spaces and stored in LanceDB.
2. **Analysis Phase:** The model receives the target task/bug report and queries workspace context.
3. **Patching Phase:** The agent executes target edits against the workspace using file manipulation tools.
4. **Verification Phase:** The agent invokes `pytest` to inspect output. If tests fail, the error trace is passed back as a `ToolMessage` observation for self-correction.

---

##  Tech Stack

- **Orchestration:** LangChain, LangChain Community
- **Local Model Provider:** Ollama (`qwen2.5-coder:7b`)
- **Vector Database:** LanceDB (Embedded Rust Vector Store)
- **Embeddings Model:** HuggingFace `all-MiniLM-L6-v2`
- **Execution & Sandboxing:** Python `subprocess`, `pytest`

---

##  Setup & Execution

### 1. Prerequisites
Ensure you have **Ollama** installed and running on your system:
```bash
ollama pull qwen2.5-coder:7b
```

### 2. Environment Setup
Clone the repository and install required Python packages:
```bash
git clone https://github.com/yourusername/autonomous-coder-agent.git
cd autonomous-coder-agent

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run the Agent Loop
```bash
python agent.py
```

---

##  Project Structure

```text
├── agent.py               # Main agent execution loop, tool definitions, and fallback parser
├── workspace/             # Execution sandbox directory
│   ├── server.py          # Target application file
│   ├── database.py        # Database dependency file
│   └── test_server.py     # Pytest test suite harness
├── lancedb_data/          # Local persistent LanceDB vector tables
└── README.md              # Documentation
```

---

##  License

Distributed under the **MIT License**. See `LICENSE` for details.
