"""Health check étendu."""

import os
import shutil

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings


def verifier_sante(db: Session) -> dict:
    checks: dict[str, str | bool | int] = {
        "status": "ok",
        "environment": settings.environment,
    }

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"
        checks["status"] = "degraded"

    upload_dir = settings.upload_dir
    if os.path.isdir(upload_dir):
        usage = shutil.disk_usage(upload_dir)
        libre_go = round(usage.free / (1024**3), 2)
        checks["upload_disk_free_gb"] = libre_go
        if libre_go < 0.5:
            checks["upload_disk"] = "low"
            checks["status"] = "degraded"
        else:
            checks["upload_disk"] = "ok"
    else:
        checks["upload_disk"] = "missing"
        checks["status"] = "degraded"

    return checks
