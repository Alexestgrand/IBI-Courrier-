# Monitoring — IBI Courriers

## Health check

URL à surveiller : `https://courriersibi.com/api/health`

Réponse attendue :
```json
{
  "status": "ok",
  "environment": "production",
  "database": "ok",
  "upload_disk": "ok",
  "upload_disk_free_gb": 12.5
}
```

Si `status` vaut `degraded`, vérifier la base PostgreSQL et l'espace disque des uploads.

## UptimeRobot (gratuit)

1. Créer un compte sur [https://uptimerobot.com](https://uptimerobot.com)
2. Ajouter un monitor **HTTP(s)** :
   - URL : `https://courriersibi.com/api/health`
   - Intervalle : 5 minutes
   - Alerte e-mail en cas de down
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
- Workflow : `.github/workflows/deploy-staging.yml`
- DNS optionnel : `staging.courriersibi.com` → même IP, décommenter le bloc dans `deploy/Caddyfile`
