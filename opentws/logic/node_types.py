"""Registry of all built-in node type definitions."""
from __future__ import annotations

from opentws.logic.models import NodeTypeDef, NodeTypePort

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _port(id_: str, label: str, type_: str = "value") -> NodeTypePort:
    return NodeTypePort(id=id_, label=label, type=type_)


# ---------------------------------------------------------------------------
# Built-in node type definitions
# ---------------------------------------------------------------------------

BUILTIN_NODE_TYPES: list[NodeTypeDef] = [

    # ── Constant ─────────────────────────────────────────────────────────
    NodeTypeDef(
        type="const_value",
        label="Festwert",
        category="logic",
        description="Gibt einen festen Wert aus — Zahl, Bool oder Text. Nützlich als Schwellwert oder Referenz.",
        inputs=[],
        outputs=[_port("value", "Wert")],
        config_schema={
            "value":     {"type": "string", "default": "0",      "label": "Wert"},
            "data_type": {"type": "string", "enum": ["number", "bool", "string"],
                          "default": "number", "label": "Datentyp"},
        },
        color="#475569",
    ),

    # ── Logic ────────────────────────────────────────────────────────────
    NodeTypeDef(
        type="and",
        label="AND",
        category="logic",
        description="Ausgang ist true wenn ALLE Eingänge true sind",
        inputs=[_port("a", "A"), _port("b", "B")],
        outputs=[_port("out", "Out")],
        color="#1d4ed8",
    ),
    NodeTypeDef(
        type="or",
        label="OR",
        category="logic",
        description="Ausgang ist true wenn MINDESTENS EIN Eingang true ist",
        inputs=[_port("a", "A"), _port("b", "B")],
        outputs=[_port("out", "Out")],
        color="#1d4ed8",
    ),
    NodeTypeDef(
        type="not",
        label="NOT",
        category="logic",
        description="Invertiert den Eingang",
        inputs=[_port("in", "In")],
        outputs=[_port("out", "Out")],
        color="#1d4ed8",
    ),
    NodeTypeDef(
        type="xor",
        label="XOR",
        category="logic",
        description="Ausgang ist true wenn GENAU EIN Eingang true ist",
        inputs=[_port("a", "A"), _port("b", "B")],
        outputs=[_port("out", "Out")],
        color="#1d4ed8",
    ),

    # ── Comparison ────────────────────────────────────────────────────────
    NodeTypeDef(
        type="compare",
        label="Vergleich",
        category="logic",
        description="Vergleicht zwei Werte (>, <, =, >=, <=, !=)",
        inputs=[_port("a", "A"), _port("b", "B")],
        outputs=[_port("out", "Ergebnis")],
        config_schema={
            "operator": {"type": "string", "enum": [">", "<", "=", ">=", "<=", "!="], "default": ">"}
        },
        color="#1d4ed8",
    ),
    NodeTypeDef(
        type="hysteresis",
        label="Hysterese",
        category="logic",
        description="Schaltet bei Überschreitung ON, erst bei Unterschreitung OFF",
        inputs=[_port("value", "Wert")],
        outputs=[_port("out", "Out")],
        config_schema={
            "threshold_on":  {"type": "number", "default": 25.0},
            "threshold_off": {"type": "number", "default": 20.0},
        },
        color="#1d4ed8",
    ),

    # ── DataPoint ─────────────────────────────────────────────────────────
    NodeTypeDef(
        type="datapoint_read",
        label="DataPoint lesen",
        category="datapoint",
        description="Gibt den aktuellen Wert eines DataPoints aus. Triggert bei Wertänderung.",
        inputs=[],
        outputs=[_port("value", "Wert"), _port("changed", "Geändert", "trigger")],
        config_schema={
            "datapoint_id":      {"type": "string", "format": "datapoint"},
            "datapoint_name":    {"type": "string"},
            # ── Transformation ────────────────────────────────────────────
            "value_formula":     {"type": "string",  "default": ""},
            # ── Filter ────────────────────────────────────────────────────
            "trigger_on_change": {"type": "boolean", "default": False},
            "min_delta":         {"type": "number",  "default": ""},
            "min_delta_pct":     {"type": "number",  "default": ""},
            "throttle_value":    {"type": "number",  "default": ""},
            "throttle_unit":     {"type": "string",  "default": "s"},
        },
        color="#0f766e",
    ),
    NodeTypeDef(
        type="datapoint_write",
        label="DataPoint schreiben",
        category="datapoint",
        description="Schreibt einen Wert in einen DataPoint",
        inputs=[_port("value", "Wert"), _port("trigger", "Trigger", "trigger")],
        outputs=[],
        config_schema={
            "datapoint_id":   {"type": "string",  "format": "datapoint"},
            "datapoint_name": {"type": "string"},
            # ── Transformation ────────────────────────────────────────────
            "value_formula":  {"type": "string",  "default": ""},
            # ── Filter ────────────────────────────────────────────────────
            "only_on_change": {"type": "boolean", "default": False},
            "min_delta":      {"type": "number",  "default": ""},
            "throttle_value": {"type": "number",  "default": ""},
            "throttle_unit":  {"type": "string",  "default": "s"},
        },
        color="#0f766e",
    ),

    # ── Math ──────────────────────────────────────────────────────────────
    NodeTypeDef(
        type="math_formula",
        label="Formel",
        category="math",
        description="Berechnet einen Ausdruck. Variablen: a, b",
        inputs=[_port("a", "A"), _port("b", "B")],
        outputs=[_port("result", "Ergebnis")],
        config_schema={"formula": {"type": "string", "default": "a + b"}},
        color="#7c3aed",
    ),
    NodeTypeDef(
        type="math_map",
        label="Skalieren",
        category="math",
        description="Skaliert einen Wert von einem Bereich in einen anderen",
        inputs=[_port("value", "Wert")],
        outputs=[_port("result", "Ergebnis")],
        config_schema={
            "in_min":  {"type": "number", "default": 0},
            "in_max":  {"type": "number", "default": 100},
            "out_min": {"type": "number", "default": 0},
            "out_max": {"type": "number", "default": 1},
        },
        color="#7c3aed",
    ),

    # ── Timer ─────────────────────────────────────────────────────────────
    NodeTypeDef(
        type="timer_delay",
        label="Verzögerung",
        category="timer",
        description="Verzögert ein Signal um N Sekunden",
        inputs=[_port("trigger", "Trigger", "trigger")],
        outputs=[_port("trigger", "Trigger", "trigger")],
        config_schema={"delay_s": {"type": "number", "default": 1.0}},
        color="#b45309",
    ),
    NodeTypeDef(
        type="timer_pulse",
        label="Impuls",
        category="timer",
        description="Gibt einen Impuls für N Sekunden aus",
        inputs=[_port("trigger", "Trigger", "trigger")],
        outputs=[_port("out", "Out")],
        config_schema={"duration_s": {"type": "number", "default": 1.0}},
        color="#b45309",
    ),
    NodeTypeDef(
        type="timer_cron",
        label="CronTrigger",
        category="timer",
        description="Löst automatisch nach einem Cron-Zeitplan aus (Minute Stunde Tag Monat Wochentag).",
        inputs=[],
        outputs=[_port("trigger", "Trigger", "trigger")],
        config_schema={"cron": {"type": "string", "default": "0 7 * * *"}},
        color="#b45309",
    ),

    # ── Script ────────────────────────────────────────────────────────────
    NodeTypeDef(
        type="python_script",
        label="Python Script",
        category="script",
        description="Führt ein Python-Skript aus. Verfügbar: inputs dict → return value",
        inputs=[_port("a", "A"), _port("b", "B"), _port("c", "C")],
        outputs=[_port("result", "Ergebnis")],
        config_schema={"script": {"type": "string", "default": "# inputs['a'], inputs['b']\nresult = inputs.get('a', 0)"}},
        color="#be185d",
    ),

    # ── MCP ───────────────────────────────────────────────────────────────
    NodeTypeDef(
        type="mcp_tool",
        label="MCP Tool",
        category="mcp",
        description="Ruft ein MCP-Tool auf",
        inputs=[_port("trigger", "Trigger", "trigger"), _port("input", "Input")],
        outputs=[_port("result", "Ergebnis"), _port("done", "Fertig", "trigger")],
        config_schema={
            "server_url": {"type": "string", "default": ""},
            "tool_name":  {"type": "string", "default": ""},
        },
        color="#0e7490",
    ),
]

# Dict lookup by type
NODE_TYPE_REGISTRY: dict[str, NodeTypeDef] = {nt.type: nt for nt in BUILTIN_NODE_TYPES}


def get_node_type(type_: str) -> NodeTypeDef | None:
    return NODE_TYPE_REGISTRY.get(type_)


def list_node_types() -> list[NodeTypeDef]:
    return BUILTIN_NODE_TYPES
