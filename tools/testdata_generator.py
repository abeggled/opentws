#!/usr/bin/env python3
"""
OpenTWS Test Data Generator — Issue #110

Generates configurable test traffic for KNX, Modbus TCP, and MQTT adapters.
Each protocol runs as an independent async task; all three can run in parallel.

Usage:
    python tools/testdata_generator.py [config.yaml]

If no config file is given, tools/testdata_generator_example.yaml is used.

Value generation modes (per signal):
    fixed      — constant value (requires: value)
    sine       — sine wave between min/max (optional: period [s], default 60)
    random     — uniform random between min/max
    ramp       — linear ramp from min to max, then wraps (optional: period [s])
    sequence   — cycles through a list (requires: values: [...])
    toggle     — alternates True/False
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("testdata")


# ---------------------------------------------------------------------------
# Value generation
# ---------------------------------------------------------------------------

class ValueGenerator:
    """Stateful value generator; call .next() to get the next value."""

    def __init__(self, cfg: dict) -> None:
        self.mode: str = cfg.get("mode", "fixed")
        self.min_val: float = float(cfg.get("min", 0))
        self.max_val: float = float(cfg.get("max", 1))
        self.fixed_val: Any = cfg.get("value", self.min_val)
        self.period: float = float(cfg.get("period", 60.0))
        self.seq_values: list = cfg.get("values", [])
        self._seq_idx: int = 0
        self._toggle: bool = False
        self._t0: float = time.monotonic()

    def next(self) -> Any:
        elapsed = time.monotonic() - self._t0

        if self.mode == "fixed":
            return self.fixed_val

        if self.mode == "sine":
            ratio = (math.sin(2 * math.pi * elapsed / self.period) + 1) / 2
            return self.min_val + ratio * (self.max_val - self.min_val)

        if self.mode == "random":
            return random.uniform(self.min_val, self.max_val)

        if self.mode == "ramp":
            ratio = (elapsed % self.period) / self.period
            return self.min_val + ratio * (self.max_val - self.min_val)

        if self.mode == "sequence":
            if not self.seq_values:
                return self.min_val
            val = self.seq_values[self._seq_idx % len(self.seq_values)]
            self._seq_idx += 1
            return val

        if self.mode == "toggle":
            self._toggle = not self._toggle
            return self._toggle

        return self.fixed_val


# ---------------------------------------------------------------------------
# KNX generator (tunneling/routing client — sends GroupValueWrite)
# ---------------------------------------------------------------------------

async def knx_generator(cfg: dict) -> None:
    try:
        from xknx import XKNX
        from xknx.io import ConnectionConfig, ConnectionType
        from xknx.telegram import Telegram
        from xknx.telegram.address import GroupAddress
        from xknx.telegram.apci import GroupValueWrite
        from xknx.dpt import DPTArray, DPTBinary
    except ImportError:
        logger.error("xknx not installed — KNX generator disabled")
        return

    try:
        _root = Path(__file__).resolve().parent.parent
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from opentws.adapters.knx.dpt_registry import DPTRegistry
    except ImportError:
        logger.error("Cannot import DPTRegistry — run this script from the project root")
        return

    conn_type = (
        ConnectionType.ROUTING
        if cfg.get("connection_type") == "routing"
        else ConnectionType.TUNNELING
    )
    conn_cfg = ConnectionConfig(
        connection_type=conn_type,
        gateway_ip=cfg["host"],
        gateway_port=int(cfg.get("port", 3671)),
        local_ip=cfg.get("local_ip"),
    )
    xknx = XKNX(connection_config=conn_cfg)

    try:
        await xknx.start()
        logger.info("KNX connected → %s:%d (%s)", cfg["host"], cfg.get("port", 3671), cfg.get("connection_type", "tunneling"))
    except Exception:
        logger.exception("KNX connection failed")
        return

    async def send_loop(tel_cfg: dict) -> None:
        ga = tel_cfg["group_address"]
        dpt_id = tel_cfg.get("dpt_id", "DPT9.001")
        interval = float(tel_cfg.get("interval", 5.0))
        dpt = DPTRegistry.get(dpt_id)
        gen = ValueGenerator(tel_cfg)

        while True:
            value = gen.next()
            try:
                raw = dpt.encoder(value)
                payload_value = DPTBinary(raw[0]) if dpt.data_type == "BOOLEAN" else DPTArray(list(raw))
                telegram = Telegram(
                    destination_address=GroupAddress(ga),
                    payload=GroupValueWrite(payload_value),
                )
                await xknx.telegrams.put(telegram)
                logger.info("KNX  GA=%-10s DPT=%-12s value=%s", ga, dpt_id, value)
            except Exception:
                logger.exception("KNX send failed GA=%s", ga)
            await asyncio.sleep(interval)

    tasks = [
        asyncio.create_task(send_loop(tc), name=f"knx-{tc['group_address']}")
        for tc in cfg.get("telegrams", [])
    ]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await xknx.stop()
        raise


# ---------------------------------------------------------------------------
# Modbus TCP generator (acts as a server/slave — openTWS polls it)
# ---------------------------------------------------------------------------

async def modbus_generator(cfg: dict) -> None:
    try:
        from pymodbus.server import StartAsyncTcpServer
        from pymodbus.datastore import (
            ModbusSequentialDataBlock,
            ModbusSlaveContext,
            ModbusServerContext,
        )
    except ImportError:
        logger.error("pymodbus not installed — Modbus generator disabled")
        return

    try:
        _root = Path(__file__).resolve().parent.parent
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from opentws.adapters.modbus_base import encode_value
    except ImportError:
        logger.warning("Cannot import encode_value — using basic uint16 encoding")

        def encode_value(  # type: ignore[misc]
            value: Any,
            data_format: str = "uint16",
            byte_order: str = "big",
            word_order: str = "big",
            scale_factor: float = 1.0,
        ) -> list[int]:
            return [int(float(value) / scale_factor) & 0xFFFF]

    # Each slave gets 1000 registers/coils pre-allocated
    co = ModbusSequentialDataBlock(0, [0] * 1000)
    di = ModbusSequentialDataBlock(0, [0] * 1000)
    hr = ModbusSequentialDataBlock(0, [0] * 1000)
    ir = ModbusSequentialDataBlock(0, [0] * 1000)

    unit_id = int(cfg.get("unit_id", 1))
    slave_ctx = ModbusSlaveContext(di=di, co=co, hr=hr, ir=ir)
    server_ctx = ModbusServerContext(slaves={unit_id: slave_ctx}, single=False)

    host = cfg.get("host", "0.0.0.0")
    port = int(cfg.get("port", 502))

    # Pymodbus function codes: 1=coils, 2=discrete_inputs, 3=holding, 4=input
    _FC = {"coil": 1, "discrete_input": 2, "holding": 3, "input": 4}

    async def update_loop() -> None:
        async def update_one(reg_cfg: dict) -> None:
            interval = float(reg_cfg.get("interval", 1.0))
            reg_type = reg_cfg.get("register_type", "holding")
            address = int(reg_cfg.get("address", 0))
            data_format = reg_cfg.get("data_format", "uint16")
            scale_factor = float(reg_cfg.get("scale_factor", 1.0))
            gen = ValueGenerator(reg_cfg)
            fc = _FC.get(reg_type, 3)

            while True:
                value = gen.next()
                try:
                    if reg_type in ("coil", "discrete_input"):
                        slave_ctx.setValues(fc, address, [int(bool(value))])
                        logger.info("Modbus %-16s[%d] = %s", reg_type, address, bool(value))
                    else:
                        regs = encode_value(value, data_format, scale_factor=scale_factor)
                        slave_ctx.setValues(fc, address, regs)
                        logger.info("Modbus %-16s[%d] = %s  raw=%s", reg_type, address, value, regs)
                except Exception:
                    logger.exception("Modbus update failed register=%d", address)
                await asyncio.sleep(interval)

        tasks = [
            asyncio.create_task(update_one(rc), name=f"modbus-reg-{rc.get('address', 0)}")
            for rc in cfg.get("registers", [])
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    logger.info("Modbus TCP server starting on %s:%d (unit_id=%d)", host, port, unit_id)
    server_task = asyncio.create_task(
        StartAsyncTcpServer(context=server_ctx, address=(host, port)),
        name="modbus-server",
    )
    update_task = asyncio.create_task(update_loop(), name="modbus-updater")

    try:
        await asyncio.gather(server_task, update_task)
    except asyncio.CancelledError:
        server_task.cancel()
        update_task.cancel()
        await asyncio.gather(server_task, update_task, return_exceptions=True)
        raise


# ---------------------------------------------------------------------------
# MQTT generator (publisher — openTWS subscribes to these topics)
# ---------------------------------------------------------------------------

async def mqtt_generator(cfg: dict) -> None:
    try:
        import aiomqtt
    except ImportError:
        logger.error("aiomqtt not installed — MQTT generator disabled")
        return

    host = cfg.get("host", "localhost")
    port = int(cfg.get("port", 1883))
    username = cfg.get("username") or None
    password = cfg.get("password") or None

    topic_cfgs = cfg.get("topics", [])
    generators = [(tc, ValueGenerator(tc)) for tc in topic_cfgs]

    async def publish_loop(topic_cfg: dict, gen: ValueGenerator, client: Any) -> None:
        topic = topic_cfg["topic"]
        interval = float(topic_cfg.get("interval", 5.0))
        retain = bool(topic_cfg.get("retain", False))
        payload_template: str | None = topic_cfg.get("payload_template")

        while True:
            value = gen.next()
            try:
                if payload_template:
                    val_str = value if isinstance(value, str) else json.dumps(value)
                    payload = payload_template.replace("###DP###", val_str)
                else:
                    payload = value if isinstance(value, str) else json.dumps(value)
                await client.publish(topic, payload, retain=retain)
                logger.info("MQTT  %-30s = %s", topic, value)
            except Exception:
                logger.exception("MQTT publish failed topic=%s", topic)
            await asyncio.sleep(interval)

    while True:
        try:
            kwargs: dict[str, Any] = {"hostname": host, "port": port}
            if username:
                kwargs["username"] = username
            if password:
                kwargs["password"] = password

            async with aiomqtt.Client(**kwargs) as client:
                logger.info("MQTT generator connected → %s:%d", host, port)
                tasks = [
                    asyncio.create_task(
                        publish_loop(tc, gen, client),
                        name=f"mqtt-{tc['topic']}",
                    )
                    for tc, gen in generators
                ]
                try:
                    await asyncio.gather(*tasks)
                except asyncio.CancelledError:
                    for t in tasks:
                        t.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    raise
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("MQTT generator error — reconnecting in 5 s")
            await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _main(config_path: str) -> None:
    config_file = Path(config_path)
    if not config_file.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    with config_file.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    tasks: list[asyncio.Task] = []

    if "knx" in config:
        tasks.append(asyncio.create_task(knx_generator(config["knx"]), name="knx"))
    if "modbus" in config:
        tasks.append(asyncio.create_task(modbus_generator(config["modbus"]), name="modbus"))
    if "mqtt" in config:
        tasks.append(asyncio.create_task(mqtt_generator(config["mqtt"]), name="mqtt"))

    if not tasks:
        logger.warning("No protocols configured — nothing to do. Check your config file.")
        return

    active = [t.get_name() for t in tasks]
    logger.info("Starting generators: %s", ", ".join(active))
    logger.info("Press Ctrl+C to stop.")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Shutting down...")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Stopped.")


if __name__ == "__main__":
    _default_cfg = Path(__file__).parent / "testdata_generator_example.yaml"
    _cfg_path = sys.argv[1] if len(sys.argv) > 1 else str(_default_cfg)

    try:
        asyncio.run(_main(_cfg_path))
    except KeyboardInterrupt:
        pass
