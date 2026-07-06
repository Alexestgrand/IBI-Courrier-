#!/bin/bash
# Attend que l'API réponde (backend + nginx peuvent mettre quelques secondes)
wait_for_health() {
  local url="${1:-http://127.0.0.1:8080/api/health}"
  local max_attempts="${2:-30}"
  local attempt=1

  while [ "$attempt" -le "$max_attempts" ]; do
    if curl -sf "$url" >/dev/null 2>&1; then
      curl -sf "$url"
      echo ""
      return 0
    fi
    echo "Attente API… (${attempt}/${max_attempts})"
    sleep 2
    attempt=$((attempt + 1))
  done

  echo "ERREUR: l'API ne répond pas après ${max_attempts} tentatives."
  docker compose -f docker-compose.prod.yml logs backend --tail 30 || true
  return 1
}
