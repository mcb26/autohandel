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
- `/admin/` Django-Admin

## Rechtlicher Hinweis

Datenschutz- und Impressumstexte sind Platzhalter und mussen vor produktivem Einsatz rechtlich gepruft werden.
