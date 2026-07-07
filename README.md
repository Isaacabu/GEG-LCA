# GEGenius – GEG- & LCA-Energieanalyse

> Ein deutschsprachiges Webtool zur **GEG**- (Gebäudeenergiegesetz) und **LCA**-Analyse
> (Lebenszyklus-/Ökobilanz) von Gebäuden – normbasiert nach **DIN V 18599** und **GEG 2024**.

![Dashboard](Screenshots%20f%C3%BCr%20Frontend/Dashboard%20Bild.png)

---

## Projektbeschreibung

**GEGenius** berechnet aus den Eingaben zu einem Gebäude (Geometrie, Bauteile, Anlagentechnik,
Photovoltaik) den **Heizwärmebedarf**, die **End- und Primärenergie**, den **PV-Ertrag**, die
**Energie- und CO₂-Bilanz** sowie eine vereinfachte **Ökobilanz (GWP)** – und ordnet das Ergebnis
in **Effizienzklassen** ein.

Der Rechenkern ist **kein Schätz-/Faustformel-Tool**, sondern setzt die Normverfahren real um:

- **Heizwärmebedarf:** DIN V 18599-2 Monatsbilanzverfahren (Wärmesenken − nutzbare Gewinne,
  Ausnutzungsgrad η, Referenzklima Potsdam, Nutzungsprofile nach Teil 10).
- **Anlagentechnik:** Prozesskette Heizung (Teil 5), Warmwasser (Teil 8), Wohnungslüftung (Teil 6)
  mit Wärmerückgewinnung; End-/Primärenergie und CO₂ nach GEG 2024 (Anlage 8/9).
- **Beleuchtung & PV:** Tabellenverfahren Beleuchtung (Teil 4, Nichtwohngebäude) und PV-Ertrag
  nach DIN V 18599-9 (monatlich je Ausrichtung, Dachgeometrie).
- **Bauphysik:** DIN 4108 – Mindestwärmeschutz, sommerlicher Wärmeschutz, Tauwasser (Glaser),
  Wärmebrücken/Luftdichtheit.
- **Ökobilanz:** Herstellung A1–A3 aus echten **ÖKOBAUDAT-2024**-Kennwerten (~2.600 Datensätze),
  Betrieb B6 aus der Energiebilanz.

### Technischer Aufbau

Eine eigenständige **Django-Anwendung** (Python) mit server-gerendertem Single-Page-UI plus
JSON- und DRF-API. Das ist die Anwendung, die auch das `Dockerfile` startet.

```
manage.py              # Django-Entry-Point
geglca/                # Projekt (settings, urls, wsgi/asgi)
dashboard/             # App: Models, Views, API, Templates, Rechenkern
  services/            # DIN V 18599 + DIN 4108 (Rechenkern)
  templates/dashboard/ # index.html (Rechner), dashboard_home.html (Startseite)
  data/                # ÖKOBAUDAT-CSV (Import-Quelle)
docs/                  # Normumsetzung & Dokumentation
scripts/               # Norm-Verifikation, PDF-Extraktion, Playwright-Smoke-Test
```

---

## Installationsanleitung

### Voraussetzungen

- **Python 3.12+**
- optional **Node.js** (nur für den Browser-Smoke-Test)
- optional **Docker**

### 1) Lokal einrichten (empfohlen)

```bash
# 1. Repository klonen
git clone https://github.com/Isaacabu/GEG-LCA.git
cd GEG-LCA

# 2. Virtuelle Umgebung anlegen
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Abhängigkeiten installieren (Django 6, DRF, django-filter, openpyxl)
pip install -r requirements.txt

# 4. Datenbank + Admin (admin/admin) + Beispieldaten + ÖKOBAUDAT-Import in einem Schritt
python setup.py

# 5. Server starten
python manage.py runserver
```

Aufrufen: **http://localhost:8000/** (Dashboard) · **/projekt/** (Rechner) · **/admin/** (Admin).

Ohne den Komfortschritt `setup.py` genügen auch:

```bash
python manage.py migrate
python manage.py runserver
```

### 2) ÖKOBAUDAT-Materialien (neu) importieren

```bash
python manage.py import_ekobaudat --list          # verfügbare CSVs in dashboard/data/ auflisten
python manage.py import_ekobaudat "<datei.csv>"   # importieren (überschreibt die Tabelle)
```

> Ohne diesen Import bleiben die grauen Emissionen (LCA/Ökobilanz) leer. `setup.py` führt ihn
> automatisch aus.

### 3) Per Docker

```bash
docker build -t geglca .
docker run -p 8000:8000 geglca
```

---

## Umgebungsvariablen / Secrets

### Laufzeit (Anwendung)

Als **Studien-/Kursprojekt** ist die App bewusst ohne Konfigurationsaufwand lauffähig – es sind
aktuell **keine** Umgebungsvariablen zwingend erforderlich:

| Einstellung | Aktueller Wert | Ort |
| --- | --- | --- |
| `SECRET_KEY` | fest hinterlegt (`django-insecure-…`) | `geglca/settings.py` |
| `DEBUG` | `True` | `geglca/settings.py` |
| `ALLOWED_HOSTS` | `[]` | `geglca/settings.py` |
| Datenbank | SQLite (`db.sqlite3`) | `geglca/settings.py` |
| Admin-Login | `admin` / `admin` | von `setup.py` erzeugt |

> ⚠️ **Nicht produktionsgehärtet.** Für einen echten Betrieb sollten `SECRET_KEY`, `DEBUG=False`
> und `ALLOWED_HOSTS` über Umgebungsvariablen gesetzt und **niemals** committet werden
> (`.env` ist in `.gitignore` bereits ausgeschlossen).

### CI/CD – GitHub Actions (Docker-Image veröffentlichen)

Der Workflow `.github/workflows/docker-publish.yml` baut und pusht ein Docker-Image zu Docker Hub.
Dafür müssen im GitHub-Repo unter **Settings → Secrets and variables → Actions** folgende
**Secrets** hinterlegt sein:

| Secret | Beschreibung |
| --- | --- |
| `DOCKERHUB_USERNAME` | Docker-Hub-Benutzername |
| `DOCKERHUB_TOKEN` | Docker-Hub Access-Token (kein Passwort) |
| `DOCKERHUB_REPO_NAME` | Ziel-Repository-Name für das Image |

---

## Beispielworkflow

Ein typischer Durchlauf von der leeren Startseite bis zum fertigen Bericht:

1. **Dashboard öffnen** (`/`) → **„＋ Neues Projekt"** → der Rechner öffnet ein Standardgebäude.
2. **🏢 Gebäudedaten:** Gebäudetyp, Geometrie (L×B×H, Geschosse), Standort/Klima und Personenzahl
   festlegen. Nutzungsprofil und interne Gewinne werden nach DIN V 18599-10 vorbelegt.
3. **🏠 Gebäudehülle:** Wand-/Dach-/Boden-Schichtaufbauten wählen (λ nach DIN 4108-4, U-Werte
   werden live berechnet), Fenster/Türen setzen. Der Heizwärmebedarf (DIN V 18599-2) rechnet
   automatisch mit.
4. **⚙️ Anlagentechnik:** Heizsystem, Wärmeübergabe, Leitungslage und Lüftung wählen →
   End-/Primärenergie, CO₂ und Effizienzklasse erscheinen.
5. **☀️ Photovoltaik:** „Ja, PV vorhanden" → Module im 3D-Modell platzieren; Ertrag,
   Eigenverbrauch und CO₂-Einsparung (DIN V 18599-9) werden berechnet.
6. **🟢 Energiebilanz:** Gesamtergebnis (Effizienzklasse, Kennzahlen je m², Wärmebilanz,
   CO₂-Bilanz, Stromverrechnung, Energiekosten) auf einen Blick.
7. **📋 DIN 4108:** Mindest-/sommerlicher Wärmeschutz, Tauwasser- und Luftdichtheitsnachweis.
8. **🌍 Ökobilanz (LCA):** Graue Emissionen A1–A3 je Bauteil aus ÖKOBAUDAT; zusätzlich **interne
   Bauteile** (Innenwände, Geschossdecken …) mit eigenem Schichtaufbau erfassen.
9. **📄 Bericht (PDF)** erzeugen (vollständiger, ausführlicher Ergebnisbericht) und den Stand über
   **„💾 Im Dashboard sichern"** speichern – das Projekt erscheint danach auf der Startseite.

---

## Tests

```bash
python manage.py test dashboard      # Django-Tests
python scripts/verify_din18599.py    # Norm-Verifikation DIN V 18599
python scripts/verify_din4108.py     # Norm-Verifikation DIN 4108

# Browser-End-to-End-Test (Dev-Server muss laufen):
npm install                          # installiert Playwright
npm run smoke                        # klickt alle Tabs durch, prüft auf Konsolen-/Netzwerkfehler
```

---

## Hinweise

- **Domänensprache ist Deutsch** – Modellfelder, API-Routen und UI-Texte verwenden Umlaute
  (`Gebäude`, `Bauteil`, `api/tür-typ`). Bitte beibehalten.
- **Urheberrechtlich geschützte DIN-Normdaten** (PDFs, extrahierte Texte) gehören **nicht** ins
  Repository und sind in `.gitignore` ausgeschlossen.
- Ergebnisse sind normbasierte **Näherungen ohne Gewähr** und ersetzen keinen Nachweis nach GEG §88.

---

## Teammitglieder

- **Ken Truong**
- **Berke Bozdoğan**
- **Ahmet Yetişir**
- **Yunus Cevik**
