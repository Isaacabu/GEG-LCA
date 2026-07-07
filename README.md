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
- **DIN 4108 (Bauphysik)** – Mindestwärmeschutz (Teil 2, Tab. 3), sommerlicher Wärmeschutz
  (Sonneneintragskennwert, Teil 2 §8.4), Tauwasser-/Glaser-Nachweis (Teil 3 + Teil 4) und
  Wärmebrücken-/Luftdichtheits-Nachweis (Beiblatt 2 / Teil 7); Details in `docs/DIN4108_Umsetzung.md`.

## Screenshots

| Gebäudehülle (3D-Schichtansicht) | Energiebilanz |
| --- | --- |
| ![Schichtansicht](Screenshots%20f%C3%BCr%20Frontend/3D-Schichtansicht.png) | ![Energiebilanz](Screenshots%20f%C3%BCr%20Frontend/Enegiebilanz%20Werte.png) |

> Weitere Screenshots liegen unter `Screenshots für Frontend/` und `Screenshots für Backend/`.

---

## Architektur

Eine eigenständige **Django-Anwendung** (Python/Django): server-gerendertes Single-Page-UI plus
JSON- und DRF-API. Das ist die Anwendung, die das `Dockerfile` startet.
→ Ordner: `manage.py`, `geglca/`, `dashboard/`

Der Rechenkern liegt in `dashboard/services/` (`din18599*.py` für die Energiebilanz, `din4108.py`
für die Bauphysik-Nachweise); die normative Herleitung ist in `docs/DIN18599_Umsetzung.md` und
`docs/DIN4108_Umsetzung.md` dokumentiert.

> Hinweis: Eine frühere React/TypeScript-Neufassung (`apps/`, `packages/`) diente nur als
> Design-Referenz und wurde entfernt (nachweislich unabhängig von der Django-App).

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

### End-to-End-Test (optional)

Voraussetzung: **Node.js** (nur für den Browser-Test; läuft gegen den laufenden Dev-Server).

```bash
npm install                 # installiert Playwright
npm run smoke               # klickt alle Tabs durch, prüft auf Konsolen-/Netzwerkfehler
```

---

## Projektstruktur (Auszug)

```
.
├── manage.py, geglca/, dashboard/   # Django-App
│   └── dashboard/services/          # Rechenkern: DIN V 18599 + DIN 4108
├── docs/                            # DIN-Umsetzung & Dokumentation
├── scripts/                         # Norm-Verifikation, PDF-Extraktion, Playwright-Smoke-Test
├── Dockerfile, requirements.txt, package.json (nur Playwright)
└── Screenshots für Frontend|Backend/
```

## Tests

```bash
python manage.py test dashboard      # Django-Tests
python scripts/verify_din18599.py    # Norm-Verifikation DIN V 18599
python scripts/verify_din4108.py     # Norm-Verifikation DIN 4108
npm run smoke                        # Browser-End-to-End-Test (Dev-Server muss laufen)
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
