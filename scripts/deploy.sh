#!/usr/bin/env bash
# Auf dem Server ausführen (cars.devmc.eu)
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/var/www/vhosts/devmc.eu/cars.devmc.eu}"
cd "$DEPLOY_DIR"

if [[ ! -f manage.py ]]; then
    echo "Fehler: manage.py nicht in $DEPLOY_DIR – zuerst scripts/server-first-install.sh ausführen."
    exit 1
fi

if [[ ! -d venv ]]; then
    python3 -m venv venv
fi

# shellcheck source=/dev/null
source venv/bin/activate

git pull origin main
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py seed_dealer_templates
python manage.py collectstatic --noinput

echo ""
echo "Update fertig in $DEPLOY_DIR"
echo "Gunicorn/Systemd-Dienst ggf. neu starten, z. B.:"
echo "  sudo systemctl restart gunicorn-cars-devmc  # falls eingerichtet"
