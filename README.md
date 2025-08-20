# Wand AI — Multi-Agent Orchestrator (Backend Challenge)

A prototype orchestration layer with dynamic agent creation, pluggable tools, and DAG execution supporting concurrency, retries, and timeouts.

## Tech Stack

- **Python 3.11**
- **FastAPI**
- **asyncio**
- **httpx**
- **tenacity**
- **Pydantic v2**

---

## Design Decisions

### 1. Async-first FastAPI Backend
- Chosen for its small footprint and first-class async support to run node tasks concurrently without extra infrastructure.
- Results are exposed via simple REST endpoints for easy consumption by a frontend or tools like `curl`.

### 2. Explicit, Typed Spec for the Execution Graph
- **WorkflowSpec** (nodes + edges) validated by Pydantic.
- A lightweight DAG validator (Kahn’s algorithm) builds topological levels for parallel fan-out/fan-in.

### 3. Pluggable Agents & Tools via Registries
- **AgentRegistry** and **ToolRegistry** enable dynamic discovery and extension.
- A generic `ToolAgent` runs any registered tool (e.g., `http.get`, `json.pick`), allowing most functionality to be added as tools without new agent code.

### 4. Resilience Built-In
- Per-node timeouts using `asyncio.wait_for`.
- Retries with exponential backoff using `tenacity`.
- Node status model tracks attempts, timestamps, logs, and errors for debugging and demo purposes.

### 5. In-Memory Run Store (Prototype)
- Keeps the system simple for a 24-hour build while leaving clear seams to persist runs in SQLite/Postgres later.

### 6. Separation of Concerns
- **`models.py`**: Schema definitions.
- **`orchestrator/`**: Graph and engine logic.
- **`tools/`**: Tool implementations.
- **`main.py`**: API entry point.
- This structure makes the system easier to test and extend incrementally.

---

## Trade-Offs Due to the 24-Hour Constraint

- **In-Process Orchestration Only**: No external queue/worker (e.g., Celery/Redis). The engine is structured to add a broker later if needed.
- **Polling Over Live Streaming**: Status is retrieved via `GET /workflows/{id}`. Server-Sent Events or WebSockets would be better for live logs but were deferred for simplicity.
- **Minimal Persistence**: Runs are stored in memory. Durable storage (e.g., SQLite/SQLModel), migrations, and replays are noted as future work.
- **Auth & RBAC Omitted**: Public endpoints for the demo. Bearer auth and rate limits can be added via FastAPI dependencies if needed.

---

## Included Tools

- **`http.get`**: Fetches data via HTTP.
- **`json.pick`**: Extracts fields from JSON (similar to `jq`).
- **Optional**: `chart.bar` (requires `matplotlib`) for quick visual artifacts.

---

## How to Run / Test the System

### Prerequisites

- **Python 3.11+**
- **macOS/Linux/WSL** recommended (Windows is also supported).

### 1. Setup & Install

```bash
git clone https://github.com/ZenitsuSlayer/wand-ai-assement.git
cd wand-ai-assement


pipenv install -r requirements.txt
pipenv shell
```

### 2. Start the API
```
uvicorn app.main:app --reload
```

Available Endpoints:
1. Health Check: GET http://127.0.0.1:8000/health
2. List Tools: GET http://127.0.0.1:8000/tools
3. List Agents: GET http://127.0.0.1:8000/agents

### 3. Submit a Sample Workflow
A sample workflow (examples/sample_workflow.json) fetches JSON and extracts field

```
curl -s -X POST http://127.0.0.1:8000/workflows \
  -H 'content-type: application/json' \
  --data @examples/sample_workflow.json
```

## Example Response
```curl -s -X POST http://127.0.0.1:8000/workflows \
  -H 'content-type: application/json' \
  --data @examples/sample_workflow.json
  ```
### 4. Poll for Status/Results
```
curl -s "http://127.0.0.1:8000/workflows/<RUN_ID>" | jq .
```

## Expected Output (When Finished):

```
{
  "status": "SUCCEEDED",
  "nodes": {
    "fetch": {
      "status": "SUCCEEDED",
      "output": { "status_code": 200, "json": { "...": "..." } },
      "attempts": 1,
      "logs": ["attempt=1 success"]
    },
    "extract": {
      "status": "SUCCEEDED",
      "output": { "picked": { "title": "...", "id": 1 } },
      "attempts": 1,
      "logs": ["attempt=1 success"]
    }
  }
}
```
### Future Improvements
1. Durable Storage: Add SQLite/Postgres for persistence.
2. Live Streaming: Implement Server-Sent Events or WebSockets for real-time updates.
3. Auth & RBAC: Add authentication and rate limiting.
4. Extended Toolset: Include more tools like LLM calls, file I/O, etc.
