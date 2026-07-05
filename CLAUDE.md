# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

A German-language tool for **GEG** (Gebäudeenergiegesetz / building energy law) and **LCA** (life-cycle
analysis) calculations: building envelope heat loss, heating-system primary energy, PV yield, energy balance,
and CO₂, oriented on DIN V 18599. Domain language is German throughout — model fields, API routes, and UI
strings use umlauts (`Gebäude`, `api/tür-typ`, `Bauteil`, `rohdichte`). Preserve them.

The project root is `GEG-LCA-main/` (this directory), nested one level under the workspace folder. Run all
commands from here.

> Student/coursework project: `geglca/settings.py` ships `DEBUG=True` and a committed `SECRET_KEY`, SQLite is
> the database, and `setup.py` creates an `admin`/`admin` superuser. Not production-hardened.

## The application

This repo is a **single Django app**: `manage.py`, `geglca/` (project), `dashboard/` (the app). It serves a
large server-rendered single-page UI plus a JSON + DRF API. **This is what `Dockerfile` runs.**

> History: a parallel React/TypeScript monorepo (`apps/`, `packages/`) plus two dead prototypes (`frontend/`,
> `backend/app.py`) used to live here for design reference. They were **removed** (verified independent of the
> Django app via the full smoke test) and archived under `../_repo_cleanup_backup/` (one level above the repo,
> local only). `package.json` now only carries the Playwright dev-tooling, not an npm workspace.

## Django app

### Commands
```bash
pip install -r requirements.txt        # Django 6.0, DRF, django-filter; needs Python 3.12
python setup.py                        # migrate + create admin/admin + sample data + Ökobaudat CSV import
python manage.py migrate
python manage.py runserver             # http://localhost:8000  (admin at /admin/)
python manage.py import_ekobaudat --list           # list CSVs in dashboard/data/
python manage.py import_ekobaudat <file.csv>       # import Ökobaudat materials
python manage.py test dashboard                    # test runner (tests.py is currently empty)
docker build -t geglca . && docker run -p 8000:8000 geglca
```

### Architecture
- **DIN 4108 (Wärme-/Feuchteschutz) sits alongside the 18599 energy balance.** `dashboard/services/din4108.py`
  implements four bauphysik proofs: Mindestwärmeschutz (Teil 2 §5, Tab. 3 → `pruefe_mindestwaermeschutz`),
  sommerlicher Wärmeschutz / Sonneneintragskennwert (Teil 2 §8.4 → `berechne_sommerlicher_waermeschutz`),
  Tauwasser/Glaser-Periodenbilanz (Teil 3 Anhang A + λ/μ aus Teil 4 → `berechne_tauwasser_glaser`, uses a
  lower-convex-hull to locate condensation planes), and Wärmebrücken ΔU_WB (Bbl 2) + Luftdichtheit n50
  (Teil 7 → `waermebruecken_zuschlag`/`pruefe_luftdichtheit`). Thin views `/calculate-mindestwaermeschutz/`,
  `/calculate-sommerlicher-waermeschutz/`, `/calculate-tauwasser/`, `/calculate-luftdichtheit/`,
  `/din4108-materialien/`; frontend tab „📋 DIN 4108" in `index.html`. Norm derivation + tables in
  `docs/DIN4108_Umsetzung.md`; verification `scripts/verify_din4108.py`; PDFs in `DIN_4108/` (gitignore,
  copyrighted) extracted via `scripts/din4108_extract.py`. The Bbl-2 ΔU_WB selector writes into the Hülle-tab
  `delta_u_wb` field, feeding the 18599 heating balance.
- **Heating demand uses a real DIN V 18599-2 monthly-balance engine.** `dashboard/services/din18599.py`
  (`calculate_heat_demand`) implements the monthly method (Q_h,b = Q_sink − η·Q_source per month, utilization
  factor η(γ,τ), Potsdam reference climate, Teil-10 usage profiles, Teil-1 factors). `dashboard/views.calculate`
  (`/calculate/`) is a thin wrapper around it. The normative derivation, exact constants, and verification are
  documented in `docs/DIN18599_Umsetzung.md`; reproduce norm-table extraction with `scripts/din_page.py` (render
  a norm page to PNG) and `scripts/din_table.py` (coordinate-based table extraction). **The copyrighted norm
  sources are NOT in the repo** (gitignored): PDFs in `../DIN V 18599/` and extracted text in `../din_texts/`
  (one level above the repo root, only on Ahmet's machine — path
  `C:\Users\ahmet\Desktop\schule\4. Sem\DigiProz\GEG-LCA-NEUESTE\`). Never commit them.
- **System engineering (Stufe 2) is DIN-based too.** `dashboard/services/din18599_anlage.py`
  (`calculate_system_din`) implements the monthly process chain heating (Teil 5) + hot water (Teil 8)
  + residential ventilation (Teil 6) with norm standard values; `views.calculate_system`
  (`/calculate-system/`) wraps it. The frontend sends the last envelope payload along, so the Teil-2
  balance is re-run with the ventilation system's effective air change (heat recovery). Fuel end
  energy is Hi-referenced; f_P/CO₂ per GEG 2024.
- **Lighting & PV are DIN-based too.** `dashboard/services/din18599_licht.py` implements the
  DIN V 18599-4 table method (non-residential only; flows into `calculate_system_din` as
  electricity). `calculate_pv` implements DIN V 18599-9 (monthly E_sol per orientation, k_pk
  Tab. B.2, f_perf Tab. B.1). Night setback (Teil 2 Gl. 28–30) is built into `din18599.py`
  (`night_setback=false` to disable). `calculate_balance` aggregates end energy + household
  electricity − PV self-consumption (own consistent scheme, not a DIN procedure).
- **Shared constants and validators**: all "magic numbers" (solar factors, primary-energy/CO₂ factors, rating
  thresholds, defaults, plausibility bounds) live in `dashboard/constants.py`; input helpers
  (`safe_float`, `validate_*`, `get_rating`) in `dashboard/utils.py`. Both `views.py` and the unused service
  import from these — add new constants here, not inline.
- **Routing** (`dashboard/urls.py`): bespoke POST endpoints (`/calculate/` etc., all `@csrf_exempt`) coexist
  with a DRF `DefaultRouter` exposing `/api/<model>/` CRUD ViewSets for the Bautechnik domain.
- **Models** (`dashboard/models.py`): `Material` → `MaterialSchicht` → `Konstruktion` (U-value computed as a
  `@property` from layer R-values via the `KonstruktionSchicht` through-table with `order`); plus `FensterTyp`,
  `TürTyp`, `SonnenschutzTyp`, `Gebäude` → `Bauteil`, and `EkobaudatMaterial` (imported reference data).
- **Two material data sources — don't conflate them.** (1) *Thermal* values (U/λ/g) are hardcoded
  presets in `EkobaudatMaterialViewSet` (`views.py`) and the frontend `WALL_LAYER_PRESETS` — source is
  DIN 4108-4, NOT Ökobaudat (Ökobaudat contains no U/λ values). Keep `PRESET_METADATA`,
  thermal/window/door/roof presets, `popular_*` lists, and the frontend λ table in sync.
  (2) *LCA* values (GWP A1–A3, density, ref unit) are real ÖKOBAUDAT data: `import_ekobaudat` parses
  the official OBD_2024 export in `dashboard/data/` (one record per UUID, module A1-A3, GWP falls back
  to the `GWPtotal (A2)` column) into `EkobaudatMaterial` (~2.6k rows). The `wall_gwp` action maps
  frontend layer keys → OBD UUIDs (`LAYER_OBD_MAP`) and returns embodied carbon per m² of wall
  build-up, displayed in the Hülle tab. Re-running the import wipes and rebuilds the table.
- **CSV import** (`dashboard/csv_utils.py`): auto-detects delimiter and encoding (utf-8-sig → cp1252 →
  latin-1) and fuzzy-matches German/English column headers. Used by both the management command and the
  `/upload-ekobaudat-csv/` view.
- The served UI is `dashboard/templates/dashboard/index.html` — a ~250 KB hand-written single-file page (no
  build step). `.bak` files and a stray 30 MB `data` blob under `templates/dashboard/` are cruft, not inputs.

### Scripts & tooling
- `scripts/*.py` are standalone tools, not part of the app's runtime. Kept on purpose: the norm-verification
  scripts (`verify_din18599*.py`, `verify_din_geg.py`, `verify_din4108.py`) and PDF-extraction helpers
  (`din_page.py`, `din_table.py`, `din4108_extract.py`). One-off diagnostic scripts (`check_*.py`, door/window
  research extractors) were removed to `../_repo_cleanup_backup/`.
- `scripts/smoke_app.js` is a Playwright end-to-end smoke test for the whole UI (run `npm run smoke` with the
  dev server up); it clicks every tab and fails on any console/network error.

## Removed: TypeScript/React monorepo

The former `apps/` + `packages/` npm workspace (React + Vite frontend, Express backend, `@geg/shared` calc
library) and the `frontend/`/`backend/` prototypes were **deleted** — they were a design-reference rewrite,
never wired into the Django app. Verified safe (no Python import, template, static, settings, URL or Dockerfile
dependency) and confirmed by the full Playwright smoke test before and after removal. Archived (recoverable)
under `../_repo_cleanup_backup/`. Node tooling left in the repo is only Playwright (`package.json` →
`npm run smoke`).
