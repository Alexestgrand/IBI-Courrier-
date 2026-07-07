#!/usr/bin/env python3
"""Écoute locale (127.0.0.1) pour déclencher deploy.sh via HTTPS (Caddy)."""

from __future__ import annotations

import hmac
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("DEPLOY_WEBHOOK_HOST", "127.0.0.1").strip()
PORT = int(os.environ.get("DEPLOY_WEBHOOK_PORT", "9089").strip())
SECRET = os.environ.get("DEPLOY_WEBHOOK_SECRET", "").strip()
REPO_DIR = Path(os.environ.get("DEPLOY_REPO_DIR", str(Path.home() / "IBI-Courrier-")).strip())
DEPLOY_SCRIPT = REPO_DIR / "ibi-courriers-web" / "scripts" / "deploy.sh"

_deploy_lock = threading.Lock()


class DeployWebhookHandler(BaseHTTPRequestHandler):
    server_version = "IBIDeployWebhook/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[deploy-webhook] {self.address_string()} - {fmt % args}\n")

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/hooks/deploy/health":
            self._send_json(200, {"status": "ready"})
            return
        self._send_json(404, {"error": "not_found"})

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        token = auth[7:].strip()
        if not SECRET or not token:
            return False
        return hmac.compare_digest(token, SECRET)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/hooks/deploy":
            self._send_json(404, {"error": "not_found"})
            return
        if not self._auth_ok():
            self._send_json(401, {"error": "unauthorized"})
            return
        if not _deploy_lock.acquire(blocking=False):
            self._send_json(409, {"error": "deploy_already_running"})
            return

        try:
            if not DEPLOY_SCRIPT.is_file():
                self._send_json(500, {"error": "deploy_script_missing"})
                return

            payload = self._read_json()
            env = os.environ.copy()
            if branch := payload.get("branch"):
                env["DEPLOY_BRANCH"] = str(branch)
            if compose := payload.get("compose_file"):
                env["DEPLOY_COMPOSE_FILE"] = str(compose)
            if health := payload.get("health_url"):
                env["DEPLOY_HEALTH_URL"] = str(health)

            result = subprocess.run(
                [str(DEPLOY_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=1200,
                cwd=DEPLOY_SCRIPT.parent,
                env=env,
            )
            if result.returncode != 0:
                self._send_json(
                    500,
                    {
                        "error": "deploy_failed",
                        "stdout": (result.stdout or "")[-4000:],
                        "stderr": (result.stderr or "")[-4000:],
                    },
                )
                return
            self._send_json(200, {"status": "ok", "message": "Déploiement terminé"})
        except subprocess.TimeoutExpired:
            self._send_json(504, {"error": "deploy_timeout"})
        finally:
            _deploy_lock.release()


def main() -> None:
    if not SECRET:
        print("DEPLOY_WEBHOOK_SECRET est requis.", file=sys.stderr)
        sys.exit(1)
    ThreadingHTTPServer.allow_reuse_address = True
    try:
        server = ThreadingHTTPServer((HOST, PORT), DeployWebhookHandler)
    except OSError as exc:
        print(f"Impossible d'écouter sur {HOST}:{PORT} — {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Webhook deploy actif sur http://{HOST}:{PORT}/hooks/deploy", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
