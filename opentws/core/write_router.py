"""
Write Router — Phase 4

Two write paths:

1. MQTT dp/{uuid}/set  →  handle(dp_id, raw_payload)
   External write command: deserialize payload, write to all DEST/BOTH bindings.

2. DataValueEvent  →  handle_value_event(event)
   Internal propagation: a SOURCE/BOTH binding received a value → write it to all
   DEST/BOTH bindings of the same DataPoint (excluding the originating binding to
   prevent loopback). This implements cross-protocol bridging, e.g.:
     KNX GA 27/6/6 (SOURCE) → DataPoint → KNX GA 6/7/15 (DEST)
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


class WriteRouter:
    def __init__(self, db: Any, registry: Any) -> None:
        from opentws.db.database import Database
        from opentws.core.registry import DataPointRegistry
        self._db: Database = db
        self._registry: DataPointRegistry = registry

    # ------------------------------------------------------------------
    # Path 1 — inbound MQTT dp/{uuid}/set
    # ------------------------------------------------------------------

    async def handle(self, dp_id: uuid.UUID, raw_payload: str) -> None:
        """Deserialize payload and write to all DEST/BOTH bindings."""
        from opentws.models.types import DataTypeRegistry
        from opentws.adapters import registry as adapter_registry
        from opentws.adapters.registry import _row_to_binding

        logger.info("WriteRouter.handle: dp_id=%s payload=%r", dp_id, raw_payload)
        dp = self._registry.get(dp_id)
        if dp is None:
            logger.warning("Write request for unknown DataPoint %s — ignored", dp_id)
            return

        dt = DataTypeRegistry.get(dp.data_type)
        try:
            value = dt.mqtt_deserializer(raw_payload)
        except Exception:
            try:
                value = json.loads(raw_payload)
            except Exception:
                value = raw_payload
        logger.info("WriteRouter: dp=%s value=%r (type=%s)", dp.name, value, dp.data_type)

        await self._write_to_dest_bindings(dp_id, value, skip_binding_id=None)

    # ------------------------------------------------------------------
    # Path 2 — internal DataValueEvent propagation
    # ------------------------------------------------------------------

    async def handle_value_event(self, event: Any) -> None:
        """
        Propagate a DataValueEvent to all DEST/BOTH bindings of the same DataPoint.

        Called by the EventBus whenever a SOURCE/BOTH binding delivers a new value.
        The originating binding (event.binding_id) is skipped to avoid loopback.
        """
        logger.info(
            "WriteRouter.handle_value_event: dp=%s value=%r source_binding=%s",
            event.datapoint_id, event.value, event.binding_id,
        )
        await self._write_to_dest_bindings(
            event.datapoint_id, event.value, skip_binding_id=event.binding_id
        )

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    async def _write_to_dest_bindings(
        self,
        dp_id: uuid.UUID,
        value: Any,
        skip_binding_id: uuid.UUID | None,
    ) -> None:
        from opentws.adapters import registry as adapter_registry
        from opentws.adapters.registry import _row_to_binding

        rows = await self._db.fetchall(
            """SELECT * FROM adapter_bindings
               WHERE datapoint_id=? AND direction IN ('DEST','BOTH') AND enabled=1""",
            (str(dp_id),),
        )
        if not rows:
            logger.debug("No writable bindings for DataPoint %s", dp_id)
            return

        logger.info("WriteRouter: %d writable binding(s) for dp %s", len(rows), dp_id)
        for row in rows:
            binding = _row_to_binding(row)
            if skip_binding_id and binding.id == skip_binding_id:
                logger.debug("WriteRouter: skipping originating binding %s", binding.id)
                continue
            instance = adapter_registry.get_instance(binding.adapter_type)
            if instance is None:
                logger.warning(
                    "Adapter %s not running — write for binding %s skipped",
                    binding.adapter_type, binding.id,
                )
                continue
            try:
                await instance.write(binding, value)
                logger.info(
                    "WriteRouter: wrote to adapter=%s binding=%s value=%r",
                    binding.adapter_type, binding.id, value,
                )
            except Exception:
                logger.exception(
                    "Write failed: adapter=%s, binding=%s", binding.adapter_type, binding.id
                )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_write_router: WriteRouter | None = None


def get_write_router() -> WriteRouter:
    if _write_router is None:
        raise RuntimeError("WriteRouter not initialized")
    return _write_router


def init_write_router(db: Any, registry: Any) -> WriteRouter:
    global _write_router
    _write_router = WriteRouter(db, registry)
    return _write_router
