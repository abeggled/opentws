"""
Integration Tests — Value Event Pipeline

Why ringbuffer instead of direct MQTT subscribe
================================================
The app's MQTT publisher is a background ``asyncio.Task`` that was created
with ``asyncio.create_task()`` inside the *session* event loop (via
asgi-lifespan).  Integration tests run in *function-scoped* event loops
(pytest-asyncio default).  These are two separate loop objects — the
session loop is suspended while a test's function loop is running, so the
publisher task never gets a chance to drain its queue during a test.

The ringbuffer, on the other hand, is updated synchronously inside
``EventBus.publish()`` (via ``asyncio.gather``) in the same function loop
that processes the HTTP request.  After ``await client.post(...)/value``
returns, the ringbuffer already contains the new entry.

Covered scenarios
-----------------
- REST write → ringbuffer entry created
- Ringbuffer entry contains all required metadata fields
- ``source_adapter`` field is set to ``"api"`` for REST writes
- Sequential writes track old_value → new_value correctly
- Test Mosquitto broker is reachable (basic connectivity smoke-test)
"""
from __future__ import annotations

import pytest
import aiomqtt


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_DP_BASE = {
    "name":          "PropTest DP",
    "data_type":     "FLOAT",
    "unit":          "W",
    "tags":          ["propagation-test"],
    "persist_value": False,
}


async def _create_dp(client, auth_headers, name: str) -> dict:
    resp = await client.post(
        "/api/v1/datapoints/",
        json={**_DP_BASE, "name": name},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _write_value(client, auth_headers, dp_id: str, value: float) -> None:
    resp = await client.post(
        f"/api/v1/datapoints/{dp_id}/value",
        json={"value": value},
        headers=auth_headers,
    )
    assert resp.status_code == 204, f"value write failed: {resp.text}"


async def _ringbuffer_for_dp(client, auth_headers, dp_id: str, limit: int = 10) -> list[dict]:
    """Fetch ringbuffer entries matching this datapoint's UUID."""
    resp = await client.get(
        "/api/v1/ringbuffer/",
        params={"q": dp_id, "limit": limit},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Ringbuffer-based propagation tests
# ---------------------------------------------------------------------------

async def test_rest_write_creates_ringbuffer_entry(client, auth_headers):
    """
    Writing a value via REST fires a DataValueEvent which the RingBuffer
    handler records.  After the POST /value call returns, the entry must
    already be present (EventBus.publish uses asyncio.gather, same loop).
    """
    dp = await _create_dp(client, auth_headers, "RingBuf Create Test")
    await _write_value(client, auth_headers, dp["id"], 42.0)

    entries = await _ringbuffer_for_dp(client, auth_headers, dp["id"])
    assert len(entries) >= 1
    latest = entries[0]   # newest-first order
    assert latest["datapoint_id"] == dp["id"]
    assert latest["new_value"] == pytest.approx(42.0)


async def test_ringbuffer_entry_has_required_fields(client, auth_headers):
    """
    Each ringbuffer entry must carry: ts, datapoint_id, new_value, old_value,
    quality, source_adapter.  These fields drive the debug log UI.
    """
    dp = await _create_dp(client, auth_headers, "RingBuf Fields Test")
    await _write_value(client, auth_headers, dp["id"], 99.9)

    entries = await _ringbuffer_for_dp(client, auth_headers, dp["id"], limit=1)
    assert entries, "No ringbuffer entry found after write"
    entry = entries[0]

    for field in ("ts", "datapoint_id", "new_value", "old_value", "quality", "source_adapter"):
        assert field in entry, f"Missing field '{field}' in ringbuffer entry: {entry}"


async def test_rest_write_source_adapter_is_api(client, auth_headers):
    """
    Values written through the REST endpoint must carry source_adapter='api'.
    """
    dp = await _create_dp(client, auth_headers, "RingBuf SourceAdapter Test")
    await _write_value(client, auth_headers, dp["id"], 1.0)

    entries = await _ringbuffer_for_dp(client, auth_headers, dp["id"], limit=1)
    assert entries
    assert entries[0]["source_adapter"] == "api"


async def test_sequential_writes_track_old_value(client, auth_headers):
    """
    After two sequential writes the second ringbuffer entry's old_value must
    equal the first write's value (chain: None → 10.0 → 20.0).
    """
    dp = await _create_dp(client, auth_headers, "RingBuf OldValue Test")

    await _write_value(client, auth_headers, dp["id"], 10.0)
    await _write_value(client, auth_headers, dp["id"], 20.0)

    entries = await _ringbuffer_for_dp(client, auth_headers, dp["id"], limit=5)
    # Entries are newest-first; [0]=second write, [1]=first write
    assert len(entries) >= 2
    second_write = entries[0]
    assert second_write["new_value"] == pytest.approx(20.0)
    assert second_write["old_value"] == pytest.approx(10.0)


async def test_three_writes_all_appear_in_ringbuffer(client, auth_headers):
    """Multiple writes are each recorded as separate ringbuffer entries."""
    dp = await _create_dp(client, auth_headers, "RingBuf Multi Test")

    for val in [1.0, 2.0, 3.0]:
        await _write_value(client, auth_headers, dp["id"], val)

    entries = await _ringbuffer_for_dp(client, auth_headers, dp["id"], limit=10)
    assert len(entries) >= 3
    recorded_values = {e["new_value"] for e in entries}
    assert {1.0, 2.0, 3.0}.issubset(recorded_values)


# ---------------------------------------------------------------------------
# MQTT broker connectivity smoke-test
# ---------------------------------------------------------------------------

async def test_mqtt_broker_reachable(mosquitto_port):
    """
    Basic smoke-test: connect to the test Mosquitto broker, publish one
    message, and disconnect cleanly.  Does not test the app's MQTT path.
    """
    async with aiomqtt.Client(hostname="localhost", port=mosquitto_port) as mqtt:
        await mqtt.publish("obs/test/ping", payload=b"pong")
    # No exception → broker is reachable
