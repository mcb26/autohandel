# Autohandel

Dieses Projekt ist eine Django-Webapp für einen Autohändler mit Lead-Formular. Kunden können Fahrzeuge anbieten, und Anfragen werden in SQLite gespeichert sowie im Django-Admin verwaltet.

## Features

- Landingpage mit Hero-Bereich im Schwarz/Weiss/Grun-Design
- Lead-Formular mit Pflichtfeld-Validierung (inkl. DSGVO-Checkbox)
- Speicherung in SQL-Datenbank (SQLite in Entwicklung)
- Speicherung von `source_ip` und `user_agent`
- Optionaler E-Mail-Versand an den Handler via `send_mail`
- Datenschutz- und Impressumsseite (Platzhalter)
- Cookie-Banner für technisch notwendige Cookies
- Django-Admin mit Listenansicht, Filtern und Suche

## Projektstruktur

- `config/` Django-Projekt
- `leads/` Django-App
- `templates/` Seiten und Formular
- `static/` CSS, JS, Bilder

## Installation (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Umgebungsvariablen

Kopiere `.env.example` und passe Werte an:

```bash
cp .env.example .env
```

Beispielwerte sind in `.env.example` enthalten. Ohne Mail-Konfiguration bleibt die App funktionsfahig; E-Mails werden dann stillschweigend nicht zugestellt oder landen bei Nutzung des Console-Backends in der Konsole.

## Fahrzeugkatalog (auto-data.net)

Marken, Modellreihen, Baureihen und Motorisierungen kommen von [auto-data.net](https://www.auto-data.net/de/allbrands).

```bash
source venv/bin/activate   # oder: source .venv/bin/activate

# Import (beliebte Marken, ca. 15–30 Min.):
python3 -m leads.autodata_sync --popular-only

# Weitere Marken z. B.:
python3 -m leads.autodata_sync --brands Dacia,Volvo,Mazda

# Katalog für Formular bauen:
python3 -m leads.catalog_builder
```

Danach Seite neu laden (Hard-Reload). Der Server erkennt Änderungen an `leads/data/vehicle_catalog.json` automatisch.

## URLs

- `/` Startseite mit Formular
- `/danke/` Danke-Seite
- `/datenschutz/` Datenschutz
- `/impressum/` Impressum
- `/dashboard/` Händler-Dashboard (Login nötig)
- `/admin/` Django-Admin

## Deployment auf dem Server

Repository: [github.com/mcb26/autohandel](https://github.com/mcb26/autohandel)

**Produktiv-Pfad (devmc.eu):** `/var/www/vhosts/devmc.eu/cars.devmc.eu/`  
**Domain:** `https://cars.devmc.eu`

### Erstinstallation (einmalig, per SSH auf dem Server)

```bash
cd /var/www/vhosts/devmc.eu/cars.devmc.eu
# Skript aus dem Repo (nach erstem Clone) oder manuell:
bash scripts/server-first-install.sh
```

Manuell statt Skript:

```bash
cd /var/www/vhosts/devmc.eu/cars.devmc.eu
git clone https://github.com/mcb26/autohandel.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### Konfiguration (`.env`) für cars.devmc.eu

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=cars.devmc.eu,www.cars.devmc.eu
DJANGO_SECRET_KEY=ein-langer-zufälliger-string
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_SECURE_SSL_REDIRECT=True
SITE_BASE_URL=https://cars.devmc.eu

TELEGRAM_BOT_TOKEN=...
TELEGRAM_NOTIFY_CHAT_ID=...
```

Die `.env` liegt nur auf dem Server – nie ins Git committen.

### Test & Dauerbetrieb

```bash
cd /var/www/vhosts/devmc.eu/cars.devmc.eu
source venv/bin/activate
python manage.py runserver 127.0.0.1:8000
```

Für Produktion: **Gunicorn** + **Nginx/Apache** (Reverse Proxy auf `127.0.0.1:8000`).  
Ordner `media/` muss beschreibbar sein (Fahrzeugbilder).

### Updates (nach jedem `git push`)

```bash
cd /var/www/vhosts/devmc.eu/cars.devmc.eu
bash scripts/deploy.sh
# Gunicorn/Systemd-Dienst neu starten
```

## Rechtlicher Hinweis

Datenschutz- und Impressumstexte sind Platzhalter und mussen vor produktivem Einsatz rechtlich gepruft werden.
