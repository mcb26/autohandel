#!/usr/bin/env bash
# Entwicklungsserver mit Projekt-venv starten (docxtpl & alle Abhängigkeiten)
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d venv ]]; then
    python3 -m venv venv
fi

# shellcheck source=/dev/null
source venv/bin/activate
pip install -q -r requirements.txt
python manage.py runserver "$@"
