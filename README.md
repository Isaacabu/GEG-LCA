# GEGenius – GEG & LCA Energieanalyse

> Ein deutschsprachiges Webtool zur **GEG**- (Gebäudeenergiegesetz) und **LCA**-Analyse
> (Lebenszyklusanalyse / Ökobilanz) von Gebäuden – auf Basis der Norm **DIN V 18599**.

Das Tool berechnet aus den Eingaben zu einem Gebäude (Geometrie, Bauteile, Anlagentechnik,
Photovoltaik) den Heizwärmebedarf, die End- und Primärenergie, den PV-Ertrag, die Energiebilanz
sowie die CO₂-Bilanz – und ordnet das Ergebnis in Effizienzklassen ein.

---

## Funktionen

- **Gebäudehülle** – Wärmeverluste über Wände, Dach, Boden, Fenster und Türen; U-Werte aus
  Schicht­aufbauten (λ-Werte nach DIN 4108-4), inkl. 3D-Schichtansicht der Bauteile.
- **Heizwärmebedarf** – echtes **DIN V 18599-2**-Monatsbilanzverfahren (Wärmesenken − nutzbare
  Gewinne, Ausnutzungsgrad, Referenzklima Potsdam, Nutzungsprofile nach Teil 10).
- **Anlagentechnik** – Prozesskette Heizung (Teil 5), Warmwasser (Teil 8) und Wohnungslüftung
  (Teil 6) mit Wärmerückgewinnung; End- und Primärenergie, f_P/CO₂ nach GEG 2024.
- **Beleuchtung & Photovoltaik** – Tabellenverfahren Beleuchtung (Teil 4, Nichtwohngebäude) und
  PV-Ertrag nach **DIN V 18599-9** (monatlich je Ausrichtung, Dachgeometrie).
- **Energie- & CO₂-Bilanz** – Endenergie + Haushaltsstrom − PV-Eigenverbrauch, CO₂ gesamt,
  Einordnung in Effizienzklassen und Benchmark-Bänder.
- **Ökobaudat-Integration** – echte LCA-Kennwerte (GWP A1–A3, Dichte) aus dem offiziellen
  ÖKOBAUDAT-Export (~2.600 Datensätze) für die graue Energie der Wandaufbauten.

## Screenshots

| Gebäudehülle (3D-Schichtansicht) | Energiebilanz |
| --- | --- |
| ![Schichtansicht](Screenshots%20f%C3%BCr%20Frontend/3D-Schichtansicht.png) | ![Energiebilanz](Screenshots%20f%C3%BCr%20Frontend/Enegiebilanz%20Werte.png) |

> Weitere Screenshots liegen unter `Screenshots für Frontend/` und `Screenshots für Backend/`.

---

## Architektur

Das Repository enthält **zwei eigenständige Implementierungen** desselben Rechners:

1. **Django-Monolith** *(primäre App)* – Python/Django, server-gerendertes Single-Page-UI plus
   JSON- und DRF-API. Das ist die Anwendung, die das `Dockerfile` startet.
   → Ordner: `manage.py`, `geglca/`, `dashboard/`
2. **TypeScript-Monorepo** *(neuere Neufassung)* – React + Vite Frontend und Express Backend mit
   gemeinsamer, unit-getesteter Berechnungsbibliothek.
   → Ordner: `apps/` (`backend`, `frontend`), `packages/shared`

Der eigentliche Rechenkern des Django-Teils liegt in `dashboard/services/din18599*.py`; die
normative Herleitung ist in `docs/DIN18599_Umsetzung.md` dokumentiert.

---

## Schnellstart

### Django-App (primär)

Voraussetzung: **Python 3.12+**

```bash
pip install -r requirements.txt     # Django, DRF, django-filter
python setup.py                     # Migrationen + Admin (admin/admin) + Beispieldaten + Ökobaudat-Import
python manage.py runserver          # http://localhost:8000  (Admin unter /admin/)
```

Ohne den `setup.py`-Komfortschritt genügen auch:

```bash
python manage.py migrate
python manage.py runserver
```

Ökobaudat-Materialien (neu) importieren:

```bash
python manage.py import_ekobaudat --list      # verfügbare CSVs in dashboard/data/ auflisten
python manage.py import_ekobaudat <datei.csv> # importieren
```

Per Docker:

```bash
docker build -t geglca .
docker run -p 8000:8000 geglca
```

### TypeScript-Monorepo (alternativ)

Voraussetzung: **Node.js** (npm workspaces)

```bash
npm install
npm run dev      # Backend (Express, :4001) + Frontend (Vite, :5173) parallel
npm test         # Unit-Tests (vitest) in packages/shared
npm run build    # Frontend bauen
```

---

## Projektstruktur (Auszug)

```
.
├── manage.py, geglca/, dashboard/   # Django-App (primär)
│   └── dashboard/services/          # DIN-V-18599-Rechenkern
├── apps/ , packages/shared/         # TypeScript-Monorepo (React/Vite + Express)
├── docs/                            # DIN-Umsetzung & Dokumentation
├── scripts/                         # Diagnose-/Recherche-Skripte (kein Laufzeitcode)
├── Dockerfile, requirements.txt
└── Screenshots für Frontend|Backend/
```

## Tests

```bash
python manage.py test dashboard      # Django-Tests
npm test                             # TypeScript: vitest (packages/shared)
```

---

## Hinweise

- **Studien-/Kursprojekt**, nicht für den Produktivbetrieb gehärtet: `geglca/settings.py` nutzt
  `DEBUG=True`, SQLite und einen mitgelieferten `SECRET_KEY`; `setup.py` legt einen
  `admin`/`admin`-Superuser an.
- **Domänensprache ist Deutsch** – Modellfelder, API-Routen und UI-Texte verwenden Umlaute
  (`Gebäude`, `Bauteil`, `api/tür-typ`). Bitte beibehalten.
- **Urheberrechtlich geschützte DIN-Normdaten** (PDFs, extrahierte Texte) gehören **nicht** ins
  Repository und sind in `.gitignore` ausgeschlossen.

## Team

- Ken Truong
- Berke Bozdoğan
- Ahmet Yetişir
- Yunus Cevik
