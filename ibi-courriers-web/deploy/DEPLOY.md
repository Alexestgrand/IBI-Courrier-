# Déploiement production — IBI Courriers

GitHub Actions déploie via **HTTPS (webhook)** plutôt que SSH port 22, car OVH bloque souvent les IP des runners GitHub.

## Installation unique sur le VPS

Connectez-vous en SSH :

```bash
ssh deploy@187.124.49.6
cd ~/IBI-Courrier-/ibi-courriers-web
git pull
chmod +x scripts/install-deploy-webhook.sh scripts/deploy-webhook.py
./scripts/install-deploy-webhook.sh
```

Puis mettez à jour Caddy :

```bash
sudo cp ~/IBI-Courrier-/ibi-courriers-web/deploy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Le script affiche le **secret** à copier dans GitHub.

## Secrets GitHub (Settings → Secrets → Actions)

| Secret | Valeur |
|--------|--------|
| `DEPLOY_WEBHOOK_URL` | `https://courriersibi.com/hooks/deploy` |
| `DEPLOY_WEBHOOK_SECRET` | secret affiché par `install-deploy-webhook.sh` |

Les anciens secrets SSH (`VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`) restent utilisables en secours si le webhook n'est pas configuré.

## Test manuel

```bash
source ~/.config/ibi-deploy-webhook.env
curl -sS -X POST http://127.0.0.1:9089/hooks/deploy \
  -H "Authorization: Bearer $DEPLOY_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"branch":"main"}'
```

## Déploiement manuel (sans GitHub)

```bash
cd ~/IBI-Courrier-/ibi-courriers-web
./scripts/deploy.sh
```

## Dépannage

| Symptôme | Action |
|----------|--------|
| GitHub : `401 unauthorized` | Vérifier `DEPLOY_WEBHOOK_SECRET` (GitHub = fichier `~/.config/ibi-deploy-webhook.env`) |
| GitHub : timeout / 502 | `sudo systemctl status ibi-deploy-webhook` et logs `journalctl -u ibi-deploy-webhook -f` |
| Webhook OK mais site inchangé | Vérifier `git log -1` dans `~/IBI-Courrier-` |
| SSH timeout depuis GitHub | Normal — utiliser le webhook |

Service systemd : `ibi-deploy-webhook` (écoute `127.0.0.1:9089`).
