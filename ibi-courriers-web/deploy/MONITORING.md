# Monitoring — IBI Courriers

## Health check public

URL à surveiller : `https://courriersibi.com/api/health`

Réponse attendue (HTTP **200**) :
```json
{
  "status": "ok"
}
```

En cas de problème (HTTP **503**) :
```json
{
  "status": "degraded",
  "database": "error",
  "upload_disk": "low"
}
```

UptimeRobot : surveiller le code HTTP **200** ou le mot-clé `"ok"` dans le corps.

## Diagnostic détaillé (admin)

Connecté en tant qu'admin : `GET /api/admin/health`

Expose environnement, espace disque, détails base de données.

## UptimeRobot (gratuit)

1. Créer un compte sur [https://uptimerobot.com](https://uptimerobot.com)
2. Ajouter un monitor **HTTP(s)** :
   - URL : `https://courriersibi.com/api/health`
   - Intervalle : 5 minutes
   - Alerte e-mail en cas de down (code ≠ 200)
3. Optionnel : mot-clé `ok` dans le corps de la réponse

## Caddy (headers sécurité)

Sur le VPS :
```bash
sudo cp ~/IBI-Courrier-/ibi-courriers-web/deploy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Staging

- Branche Git : `staging`
- Port local VPS : `8081`
- Health : `http://127.0.0.1:8081/api/health`
- Workflow : `.github/workflows/deploy-staging.yml` (tests + build avant déploiement)
- DNS optionnel : `staging.courriersibi.com` → décommenter le bloc dans `deploy/Caddyfile`

## Sauvegardes

Les sauvegardes automatiques (cron) et manuelles (admin) partagent le volume Docker `backups` (`/data/backups`).

Installation cron : `./scripts/install-backup-cron.sh` (quotidien à 3h00, logs dans `logs/backup.log`).

En cas d'échec, une alerte e-mail est envoyée aux adresses `NOTIFY_EMAILS` (SMTP requis).

Variables utiles dans `.env` :
- `COMPOSE_PROJECT_NAME=ibi-courriers-prod` — évite de cibler le mauvais stack Docker
- `NOTIFY_EMAILS=admin@ibi.ci` — destinataires des alertes sauvegarde
