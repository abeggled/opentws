"""
Integration Tests — QR-Code-Widget (Visu-Seiten-API)

Das QR-Code-Widget ist ein reines Frontend-Widget ohne eigenen Backend-Endpunkt.
Diese Tests prüfen, dass die Visu-Seiten-API die Widget-Konfiguration korrekt
speichert und zurückliefert (Round-Trip-Sicherheit).

Abgedeckt:
  1.  Typ URL: url_url wird verlustfrei gespeichert
  2.  Typ WiFi: alle Felder (ssid, password, encryption, hidden) round-trip-sicher
  3.  Typ vCard: alle Felder (firstname, lastname, company, mobile, email) round-trip-sicher
  4.  Gemeinsame Felder (qrType, label, errorCorrection, darkColor, lightColor) round-trip
  5.  Alle drei Typen auf derselben Seite als separate Widgets
  6.  Leere Felder werden als leere Strings / false gespeichert
"""
from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.integration

# ── Hilfsroutinen ─────────────────────────────────────────────────────────────

async def _create_page(client, auth_headers, name: str) -> str:
    resp = await client.post(
        "/api/v1/visu/nodes",
        json={"name": name, "type": "PAGE", "order": 999, "access": "public"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Seite erstellen fehlgeschlagen: {resp.text}"
    return resp.json()["id"]


async def _save_page(client, auth_headers, page_id: str, widgets: list) -> None:
    resp = await client.put(
        f"/api/v1/visu/pages/{page_id}",
        json={
            "grid_cols": 12,
            "grid_row_height": 80,
            "grid_cell_width": 80,
            "background": None,
            "widgets": widgets,
        },
        headers=auth_headers,
    )
    assert resp.status_code in (200, 204), f"Seite speichern fehlgeschlagen: {resp.text}"


async def _load_page(client, auth_headers, page_id: str) -> dict:
    resp = await client.get(f"/api/v1/visu/pages/{page_id}", headers=auth_headers)
    assert resp.status_code == 200, f"Seite laden fehlgeschlagen: {resp.text}"
    return resp.json()


async def _delete_node(client, auth_headers, node_id: str) -> None:
    await client.delete(f"/api/v1/visu/nodes/{node_id}", headers=auth_headers)


def _qrcode_widget(widget_id: str, config: dict, x: int = 0) -> dict:
    return {
        "id": widget_id,
        "name": "E2E QR-Code",
        "type": "QrCode",
        "datapoint_id": None,
        "status_datapoint_id": None,
        "x": x, "y": 0, "w": 3, "h": 3,
        "config": config,
    }


def _base_config(**overrides) -> dict:
    base = {
        "qrType":          "url",
        "label":           "",
        "errorCorrection": "M",
        "darkColor":       "#000000",
        "lightColor":      "#ffffff",
        "url_url":         "",
        "wifi_ssid":       "",
        "wifi_password":   "",
        "wifi_encryption": "WPA",
        "wifi_hidden":     False,
        "vcard_firstname": "",
        "vcard_lastname":  "",
        "vcard_company":   "",
        "vcard_mobile":    "",
        "vcard_email":     "",
    }
    base.update(overrides)
    return base


# ── Test 1: URL-Typ round-trip ────────────────────────────────────────────────

async def test_qrcode_url_type_round_trip(client, auth_headers):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-URL-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config(
        qrType="url",
        url_url="https://meine-hausautomation.local/visu",
        label="Startseite",
    )

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)

        saved = page["widgets"][0]["config"]
        assert saved["qrType"]  == "url"
        assert saved["url_url"] == "https://meine-hausautomation.local/visu"
        assert saved["label"]   == "Startseite"
    finally:
        await _delete_node(client, auth_headers, page_id)


# ── Test 2: WiFi-Typ round-trip ───────────────────────────────────────────────

async def test_qrcode_wifi_type_round_trip(client, auth_headers):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-WiFi-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config(
        qrType="wifi",
        wifi_ssid="GaesteNetz",
        wifi_password="Geheim1234",
        wifi_encryption="WPA",
        wifi_hidden=True,
        label="Gäste-WLAN",
    )

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)

        saved = page["widgets"][0]["config"]
        assert saved["qrType"]          == "wifi"
        assert saved["wifi_ssid"]       == "GaesteNetz"
        assert saved["wifi_password"]   == "Geheim1234"
        assert saved["wifi_encryption"] == "WPA"
        assert saved["wifi_hidden"]     is True
        assert saved["label"]           == "Gäste-WLAN"
    finally:
        await _delete_node(client, auth_headers, page_id)


async def test_qrcode_wifi_wep_encryption(client, auth_headers):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-WEP-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config(qrType="wifi", wifi_ssid="AltesNetz", wifi_encryption="WEP")

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)
        assert page["widgets"][0]["config"]["wifi_encryption"] == "WEP"
    finally:
        await _delete_node(client, auth_headers, page_id)


async def test_qrcode_wifi_no_encryption(client, auth_headers):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-Open-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config(qrType="wifi", wifi_ssid="OffenesCafe", wifi_encryption="none")

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)
        assert page["widgets"][0]["config"]["wifi_encryption"] == "none"
        assert page["widgets"][0]["config"]["wifi_ssid"]       == "OffenesCafe"
    finally:
        await _delete_node(client, auth_headers, page_id)


# ── Test 3: vCard-Typ round-trip ──────────────────────────────────────────────

async def test_qrcode_vcard_type_round_trip(client, auth_headers):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-vCard-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config(
        qrType="vcard",
        vcard_firstname="Max",
        vcard_lastname="Mustermann",
        vcard_company="Musterfirma AG",
        vcard_mobile="+41 79 123 45 67",
        vcard_email="max@musterfirma.ch",
        label="Kontakt",
    )

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)

        saved = page["widgets"][0]["config"]
        assert saved["qrType"]           == "vcard"
        assert saved["vcard_firstname"]  == "Max"
        assert saved["vcard_lastname"]   == "Mustermann"
        assert saved["vcard_company"]    == "Musterfirma AG"
        assert saved["vcard_mobile"]     == "+41 79 123 45 67"
        assert saved["vcard_email"]      == "max@musterfirma.ch"
        assert saved["label"]            == "Kontakt"
    finally:
        await _delete_node(client, auth_headers, page_id)


# ── Test 4: Darstellungs-Felder round-trip ────────────────────────────────────

@pytest.mark.parametrize("field,value", [
    ("errorCorrection", "H"),
    ("errorCorrection", "L"),
    ("darkColor",       "#1a3c6e"),
    ("lightColor",      "#f0ead6"),
    ("label",           "Mein QR"),
])
async def test_qrcode_display_fields_round_trip(client, auth_headers, field, value):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-Disp-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config(url_url="https://example.com", **{field: value})

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)
        assert page["widgets"][0]["config"][field] == value
    finally:
        await _delete_node(client, auth_headers, page_id)


# ── Test 5: Alle drei Typen auf einer Seite ───────────────────────────────────

async def test_qrcode_all_three_types_on_same_page(client, auth_headers):
    page_id  = await _create_page(client, auth_headers, f"E2E-QrCode-Multi-{uuid.uuid4().hex[:8]}")
    id_url   = str(uuid.uuid4())
    id_wifi  = str(uuid.uuid4())
    id_vcard = str(uuid.uuid4())

    try:
        await _save_page(client, auth_headers, page_id, [
            _qrcode_widget(id_url,   _base_config(qrType="url",   url_url="https://a.example.com"), x=0),
            _qrcode_widget(id_wifi,  _base_config(qrType="wifi",  wifi_ssid="TestNetz"),             x=4),
            _qrcode_widget(id_vcard, _base_config(qrType="vcard", vcard_firstname="Anna"),           x=8),
        ])
        page = await _load_page(client, auth_headers, page_id)

        by_id = {w["id"]: w["config"] for w in page["widgets"]}
        assert by_id[id_url]["qrType"]           == "url"
        assert by_id[id_url]["url_url"]          == "https://a.example.com"
        assert by_id[id_wifi]["qrType"]          == "wifi"
        assert by_id[id_wifi]["wifi_ssid"]       == "TestNetz"
        assert by_id[id_vcard]["qrType"]         == "vcard"
        assert by_id[id_vcard]["vcard_firstname"] == "Anna"
    finally:
        await _delete_node(client, auth_headers, page_id)


# ── Test 6: Leere Felder / Defaults ───────────────────────────────────────────

async def test_qrcode_empty_fields_saved(client, auth_headers):
    page_id   = await _create_page(client, auth_headers, f"E2E-QrCode-Empty-{uuid.uuid4().hex[:8]}")
    widget_id = str(uuid.uuid4())
    cfg = _base_config()  # alles leer / Default

    try:
        await _save_page(client, auth_headers, page_id, [_qrcode_widget(widget_id, cfg)])
        page = await _load_page(client, auth_headers, page_id)

        saved = page["widgets"][0]["config"]
        assert saved["qrType"]          == "url"
        assert saved["url_url"]         == ""
        assert saved["wifi_ssid"]       == ""
        assert saved["vcard_firstname"] == ""
        assert saved["wifi_hidden"]     is False
    finally:
        await _delete_node(client, auth_headers, page_id)
