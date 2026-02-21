#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Chemistry Bot — First-Time SSL Certificate Acquisition
#
# Run this ONCE on the server to get the initial Let's Encrypt certificate.
# After that, the certbot service in docker-compose handles auto-renewal.
#
# Prerequisites:
#   1. DNS A record for chembot.hex8d.space must already point to this server.
#   2. Ports 80 and 443 must be reachable from the internet.
#   3. .env file must contain SSL_EMAIL=your@email.com
#
# Usage:
#   chmod +x scripts/init-ssl.sh
#   ./scripts/init-ssl.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")/.."

# Load .env if present
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

DOMAIN="${DOMAIN:-chembot.hex8d.space}"
EMAIL="${SSL_EMAIL:?SSL_EMAIL must be set in .env}"

echo "==> [1/4] Creating certbot volume directories..."
docker compose run --rm --entrypoint "" certbot \
    sh -c "mkdir -p /etc/letsencrypt /var/www/certbot"

echo "==> [2/4] Creating temporary self-signed cert so nginx can start..."
docker compose run --rm --entrypoint "" certbot sh -c "
    mkdir -p /etc/letsencrypt/live/${DOMAIN} &&
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/letsencrypt/live/${DOMAIN}/privkey.pem \
        -out    /etc/letsencrypt/live/${DOMAIN}/fullchain.pem \
        -subj   '/CN=localhost'
"

echo "==> [3/4] Starting nginx with the self-signed cert..."
docker compose up -d nginx

echo "    Waiting for nginx to be ready..."
sleep 3

echo "==> [4/4] Obtaining real Let's Encrypt certificate for ${DOMAIN}..."
docker compose run --rm --entrypoint "" certbot \
    certbot certonly \
        --webroot \
        --webroot-path /var/www/certbot \
        --email "${EMAIL}" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "${DOMAIN}"

echo "==> Reloading nginx to pick up the real certificate..."
docker compose exec nginx nginx -s reload

echo ""
echo "Done! https://${DOMAIN} is now secured with a Let's Encrypt certificate."
echo "The certbot service will auto-renew the certificate every 12 hours when needed."
