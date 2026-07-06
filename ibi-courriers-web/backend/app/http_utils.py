"""Utilitaires HTTP (proxy, adresse client)."""

from fastapi import Request


def obtenir_ip_client(request: Request) -> str:
    """IP du client derrière nginx/Caddy (X-Forwarded-For ou X-Real-IP)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"
