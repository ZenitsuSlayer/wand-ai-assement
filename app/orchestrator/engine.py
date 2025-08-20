from __future__ import annotations
import asyncio, time, traceback
from typing import Any, Dict
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential
from app.models import AgentSpec, NodeResult, RunState, RunStatus, WorkflowSpec
from app.orchestrator.agent import AgentRegistry, ToolAgent
from app.orchestrator.graph import build_graph, topo_levels
from app.tools import default_tool_registry

class Orchestrator:
    def __init__(self) -> None:
        self._runs: Dict[str, RunState] = {}
        self._tools = default_tool_registry()
        self._agents = AgentRegistry()
        self._agents.register(ToolAgent)

    def list_tools(self) -> Dict[str, Any]:
        return self._tools.list()

    def list_agents(self) -> Dict[str, Any]:
        return self._agents.list()

    def get_run(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    async def submit(self, run_id: str, spec: WorkflowSpec) -> RunState:
        now = time.time()
        state = RunState(
            run_id=run_id,
            status=RunStatus.PENDING,
            nodes={n.id: NodeResult(status=RunStatus.PENDING) for n in spec.nodes},
            created_at=now,
            updated_at=now,
        )
        self._runs[run_id] = state
        asyncio.create_task(self._execute(run_id, spec))
        return state

    async def _execute(self, run_id: str, spec: WorkflowSpec) -> None:
        state = self._runs[run_id]
        state.status = RunStatus.RUNNING
        state.updated_at = time.time()
        try:
            adj, indeg = build_graph(spec)
            levels = topo_levels(adj, indeg.copy())

            # For looking up node specs quickly
            spec_by_id = {n.id: n for n in spec.nodes}
            # Shared context for outputs (isolation per node comes from not mutating each other's objects)
            outputs: Dict[str, Dict[str, Any]] = {}

            for level in levels:
                # Run all nodes in this level concurrently
                await asyncio.gather(*[
                    self._run_node(run_id, spec_by_id[node_id], outputs)
                    for node_id in level
                ])

            # Final status
            if any(n.status == RunStatus.FAILED for n in state.nodes.values()):
                state.status = RunStatus.FAILED
            else:
                state.status = RunStatus.SUCCEEDED
        except Exception as e:
            state.status = RunStatus.FAILED
            for nr in state.nodes.values():
                if nr.status == RunStatus.PENDING:
                    nr.status = RunStatus.FAILED
                    nr.error = "Aborted due to orchestration error"
            # Track top-level orchestration error in a pseudo-node
            state.nodes.setdefault("_orchestrator", NodeResult(status=RunStatus.FAILED, error=str(e)))
        finally:
            state.updated_at = time.time()

    async def _run_node(self, run_id: str, node_spec, outputs: Dict[str, Dict[str, Any]]) -> None:
        state = self._runs[run_id]
        nr = state.nodes[node_spec.id]
        nr.started_at = time.time()
        nr.status = RunStatus.RUNNING
        state.updated_at = time.time()

        agent: Any = self._agents.create(node_spec.agent.type)
        timeout = node_spec.agent.timeout_sec or 30.0
        retries = max(1, node_spec.agent.retries)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries),
            wait=wait_exponential(multiplier=0.25, min=0.5, max=3),
            reraise=True,
        ):
            with attempt:
                try:
                    nr.attempts += 1
                    # Inputs available: outputs of all predecessors
                    result = await asyncio.wait_for(
                        agent.run(params=node_spec.params, inputs=outputs, tools=self._tools),
                        timeout=timeout
                    )
                    outputs[node_spec.id] = result
                    nr.output = result
                    nr.status = RunStatus.SUCCEEDED
                    nr.completed_at = time.time()
                    nr.logs.append(f"attempt={nr.attempts} success")
                except Exception as e:
                    # If retries remain, this raises to tenacity which will retry
                    tb = traceback.format_exc(limit=3)
                    nr.logs.append(f"attempt={nr.attempts} error={e}")
                    nr.error = str(e)
                    if nr.attempts >= retries:
                        nr.status = RunStatus.FAILED
                        nr.completed_at = time.time()
                        raise
                finally:
                    self._runs[run_id].updated_at = time.time()
