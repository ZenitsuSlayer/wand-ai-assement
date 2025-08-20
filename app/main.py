from __future__ import annotations
import time, uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.models import WorkflowSpec, RunState
from app.orchestrator.engine import Orchestrator

app = FastAPI(title="Wand AI — Multi-Agent Orchestrator", version="0.1.0")
orch = Orchestrator()

@app.get("/health")
async def health():
    return {"ok": True, "ts": time.time()}

@app.get("/tools")
async def list_tools():
    return {"tools": orch.list_tools()}

@app.get("/agents")
async def list_agents():
    return {"agents": orch.list_agents()}

@app.post("/workflows", response_model=RunState)
async def submit_workflow(spec: WorkflowSpec):
    run_id = uuid.uuid4().hex[:12]
    return await orch.submit(run_id, spec)

@app.get("/workflows/{run_id}", response_model=RunState)
async def get_run(run_id: str):
    rs = orch.get_run(run_id)
    if not rs:
        raise HTTPException(404, "Run not found")
    return JSONResponse(rs.model_dump())
