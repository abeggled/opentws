"""
LogicManager — manages all logic graphs and integrates with the EventBus.

- Subscribes to DataValueEvents
- Triggers graphs whose datapoint_read nodes watch the changed DataPoint
- Executes the graph and writes outputs back via the registry
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from opentws.logic.executor import GraphExecutor
from opentws.logic.models import FlowData

logger = logging.getLogger(__name__)

_manager: "LogicManager | None" = None


def get_logic_manager() -> "LogicManager":
    if _manager is None:
        raise RuntimeError("LogicManager not initialised")
    return _manager


def init_logic_manager(db: Any, event_bus: Any, registry: Any) -> "LogicManager":
    global _manager
    _manager = LogicManager(db, event_bus, registry)
    return _manager


class LogicManager:
    def __init__(self, db: Any, event_bus: Any, registry: Any):
        self._db = db
        self._event_bus = event_bus
        self._registry = registry
        # hysteresis state per graph per node
        self._hysteresis: dict[str, dict[str, bool]] = {}
        # graph cache: id → FlowData
        self._graphs: dict[str, tuple[str, bool, FlowData]] = {}  # id → (name, enabled, flow)

    async def start(self) -> None:
        """Subscribe to EventBus and load all graphs into cache."""
        await self._load_graphs()
        from opentws.core.event_bus import DataValueEvent
        self._event_bus.subscribe(DataValueEvent, self._on_value_event)
        logger.info("LogicManager started — %d graphs loaded", len(self._graphs))

    async def stop(self) -> None:
        from opentws.core.event_bus import DataValueEvent
        self._event_bus.unsubscribe(DataValueEvent, self._on_value_event)

    async def reload(self) -> None:
        """Reload graph cache from DB (after a graph was saved)."""
        await self._load_graphs()

    # ── Event Handler ─────────────────────────────────────────────────────

    async def _on_value_event(self, event: Any) -> None:
        dp_id = str(event.datapoint_id)
        for graph_id, (name, enabled, flow) in self._graphs.items():
            if not enabled:
                continue
            # Check if any datapoint_read node watches this dp
            trigger_nodes = [
                n for n in flow.nodes
                if n.type == "datapoint_read" and n.data.get("datapoint_id") == dp_id
            ]
            if not trigger_nodes:
                continue
            # Build input overrides
            overrides: dict[str, dict[str, Any]] = {}
            for tn in trigger_nodes:
                overrides[tn.id] = {"value": event.value, "changed": True}
            await self._execute_graph(graph_id, name, flow, overrides)

    # ── Execution ─────────────────────────────────────────────────────────

    async def execute_graph(self, graph_id: str) -> dict[str, Any]:
        """Manually trigger a graph (e.g. from API).

        Reads current registry values for all datapoint_read nodes so that
        a manual run shows real values — not None.
        """
        entry = self._graphs.get(graph_id)
        if not entry:
            raise KeyError(f"Graph {graph_id} not in cache")
        name, enabled, flow = entry

        # Seed overrides from current registry values
        overrides: dict[str, dict[str, Any]] = {}
        for node in flow.nodes:
            if node.type != "datapoint_read":
                continue
            dp_id_str = node.data.get("datapoint_id")
            if not dp_id_str:
                continue
            try:
                dp_id = uuid.UUID(dp_id_str)
                vs = self._registry.get_value(dp_id)
                if vs is not None:
                    overrides[node.id] = {"value": vs.value, "changed": False}
            except Exception:
                pass

        return await self._execute_graph(graph_id, name, flow, overrides)

    async def _execute_graph(
        self,
        graph_id: str,
        name: str,
        flow: FlowData,
        overrides: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        hyst = self._hysteresis.setdefault(graph_id, {})
        executor = GraphExecutor(flow, hyst)
        try:
            outputs = executor.execute(overrides)
        except Exception as exc:
            logger.error("Graph %s (%s) execution error: %s", graph_id, name, exc)
            return {}

        # Process datapoint_write outputs — publish DataValueEvent so that
        # the registry, ring-buffer, MQTT and WebSocket all get notified.
        from opentws.core.event_bus import DataValueEvent
        for node in flow.nodes:
            if node.type != "datapoint_write":
                continue
            node_out = outputs.get(node.id, {})
            write_val = node_out.get("_write_value")
            if write_val is None:
                continue
            dp_id_str = node.data.get("datapoint_id")
            if not dp_id_str:
                continue
            try:
                dp_id = uuid.UUID(dp_id_str)
                event = DataValueEvent(
                    datapoint_id=dp_id,
                    value=write_val,
                    quality="good",
                    source_adapter="logic",
                )
                await self._event_bus.publish(event)
                logger.debug("Graph %s: wrote dp %s = %s", graph_id, dp_id_str, write_val)
            except Exception as exc:
                logger.warning("Graph %s: failed to write dp %s: %s", graph_id, dp_id_str, exc)

        return outputs

    # ── Cache ─────────────────────────────────────────────────────────────

    async def _load_graphs(self) -> None:
        rows = await self._db.fetchall(
            "SELECT id, name, enabled, flow_data FROM logic_graphs"
        )
        self._graphs = {}
        for row in rows:
            try:
                raw = json.loads(row["flow_data"]) if row["flow_data"] else {}
                flow = FlowData.model_validate(raw)
                self._graphs[row["id"]] = (row["name"], bool(row["enabled"]), flow)
            except Exception as exc:
                logger.warning("Failed to parse graph %s: %s", row["id"], exc)

    def invalidate_cache(self, graph_id: str) -> None:
        self._graphs.pop(graph_id, None)
        self._hysteresis.pop(graph_id, None)
