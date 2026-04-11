"""
Kamera-Proxy — leitet Kamera-Streams vom Backend weiter.

GET /api/v1/camera/proxy   Proxyt einen HTTP-Stream zur Kamera
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from obs.api.auth import decode_token

router = APIRouter(tags=["camera"])


async def _camera_auth(
    request: Request,
    _token: str = Query("", alias="_token", description="JWT als Query-Parameter"),
) -> str:
    """
    Akzeptiert JWT entweder als 'Authorization: Bearer …'-Header
    oder als URL-Query-Parameter '?_token=…' (nötig für <img>/<video>-Tags).
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return decode_token(auth_header[7:])
    if _token:
        return decode_token(_token)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide Authorization: Bearer {token} or ?_token=",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/proxy")
async def proxy_camera(
    url: str = Query(..., description="Vollständige Kamera-URL (http://…)"),
    username: str = Query("", description="Basic-Auth Benutzername"),
    password: str = Query("", description="Basic-Auth Passwort"),
    apikey_param: str = Query("", description="API-Key Query-Parameter-Name"),
    apikey_value: str = Query("", description="API-Key Wert"),
    _user: str = Depends(_camera_auth),
) -> StreamingResponse:
    """
    Proxyt den Kamera-Stream vom Backend aus.
    Ermöglicht HTTPS-Browser → Server → HTTP-Kamera (Mixed-Content-Bypass).
    """
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nur HTTP/HTTPS-URLs erlaubt",
        )

    target = url
    if apikey_param and apikey_value:
        sep = "&" if "?" in target else "?"
        target = f"{target}{sep}{apikey_param}={apikey_value}"

    auth = (username, password) if username else None

    # ── HEAD-Request: Erreichbarkeit prüfen + Content-Type holen ────────────
    content_type = "application/octet-stream"
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as hc:
            head = await hc.head(target, auth=auth)

        if head.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Kamera: Authentifizierung fehlgeschlagen (401)",
            )
        # 405 = HEAD nicht unterstützt → optimistisch weiterfahren
        if head.status_code != 405 and head.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Kamera antwortet mit {head.status_code}",
            )
        ct = head.headers.get("content-type", "")
        if ct:
            # Header-Injection verhindern
            content_type = ct.split("\n")[0].split("\r")[0]

    except HTTPException:
        raise
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Kamera nicht erreichbar: {exc}",
        ) from exc

    # ── Streaming-Generator ─────────────────────────────────────────────────
    async def _stream() -> AsyncGenerator[bytes, None]:
        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as hc:
            try:
                async with hc.stream("GET", target, auth=auth) as resp:
                    async for chunk in resp.aiter_bytes(chunk_size=8192):
                        yield chunk
            except httpx.RequestError:
                return  # Verbindung unterbrochen — Stream still beenden

    return StreamingResponse(_stream(), media_type=content_type)
