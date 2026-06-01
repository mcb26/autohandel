#!/usr/bin/env bash
# Erstinstallation auf cars.devmc.eu (einmalig auf dem Server)
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/var/www/vhosts/devmc.eu/cars.devmc.eu}"
REPO_URL="${REPO_URL:-https://github.com/mcb26/autohandel.git}"
DOMAIN="${DOMAIN:-cars.devmc.eu}"

mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

if [[ -f manage.py ]]; then
    echo "Projekt existiert bereits in $DEPLOY_DIR – für Updates: bash scripts/deploy.sh"
    exit 0
fi

if [[ -n "$(ls -A "$DEPLOY_DIR" 2>/dev/null || true)" ]]; then
    echo "Verzeichnis ist nicht leer. Bitte leeren oder anderen DEPLOY_DIR setzen."
    exit 1
fi

git clone "$REPO_URL" .

python3 -m venv venv
# shellcheck source=/dev/null
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo ""
    echo "=== .env angelegt – bitte anpassen: ==="
    echo "  nano $DEPLOY_DIR/.env"
    echo ""
    echo "Mindestens:"
    echo "  DJANGO_DEBUG=False"
    echo "  DJANGO_ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN"
    echo "  DJANGO_SECRET_KEY=<zufällig>"
    echo "  SITE_BASE_URL=https://$DOMAIN"
    echo "  TELEGRAM_BOT_TOKEN=..."
    echo "  TELEGRAM_NOTIFY_CHAT_ID=..."
    echo ""
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo ""
echo "Basis-Installation abgeschlossen in $DEPLOY_DIR"
echo "Als Nächstes:"
echo "  python manage.py createsuperuser"
echo "  Gunicorn + Webserver (Nginx/Apache) für https://$DOMAIN einrichten"
