#!/usr/bin/env python3
"""Envoie une alerte e-mail en cas d'échec de sauvegarde (appelé depuis le cron)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.email_service import notifier_echec_sauvegarde


def main() -> int:
    message = " ".join(sys.argv[1:]).strip() or "La sauvegarde automatique a échoué."
    try:
        notifier_echec_sauvegarde(message)
    except Exception as exc:
        print(f"Impossible d'envoyer l'alerte : {exc}", file=sys.stderr)
        return 1
    print("Alerte sauvegarde envoyée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
