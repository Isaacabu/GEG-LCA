# GEG AAA CLEAN

Vereinfachte, normnahe Gebaeudehuellen- und Heizbedarfsberechnung nach
GEG- / DIN-V-18599-Logik fuer Uni-Projektzwecke. **Kein zertifizierter
Normrechner.** TypeScript-Monorepo (Backend + Frontend + Shared Calculations).
Keine Default-U-Werte, keine stillen Fallbacks.

## Struktur

```
GEG_AAA_CLEAN/
  package.json              # npm workspaces
  apps/
    backend/                # Express + TypeScript, Port 4001
    frontend/               # React + Vite + TypeScript, Port 5173
      public/assets/        # Bilder (logo, hero, wave, hud) ablegen
  packages/
    shared/                 # Domain-Typen + Berechnungen + Validation + Tests
```

## Voraussetzungen

* Node.js 20 oder neuer
* npm 10 oder neuer

## Installation (einmalig)

```powershell
cd C:\Users\ismai\Desktop\THA\GEG_AAA_CLEAN
npm install
```

## Lokal starten

Zwei Terminals:

```powershell
npm run dev:backend     # http://localhost:4001/api/health
npm run dev:frontend    # http://localhost:5173 (proxied /api)
```

## Tests

```powershell
npm run test
```

28 Tests, alle gruen. Abdeckung: U-Wert (Schichten + fixed), H = A·U·Fx,
Netto-Wandflaeche, A_eff Window, Solar-Gewinn, Ampel, Lueftung,
Gewinn-Ausnutzungsfaktor, Etagen-Geometrie, vollstaendige Envelope-Bilanz,
Heizwaermebedarf.

## API-Endpunkte

| Methode | Pfad                                | Beschreibung |
|---------|-------------------------------------|--------------|
| GET     | /api/health                         | Healthcheck |
| GET     | /api/materials                      | Materialdatenbank |
| GET     | /api/constructions                  | Bauteilkatalog (alle) |
| GET     | /api/constructions/walls            | nur Aussenwaende |
| GET     | /api/constructions/roofs            | nur Daecher |
| GET     | /api/constructions/floors           | nur Boeden |
| GET     | /api/constructions/windows          | nur Fenster |
| GET     | /api/constructions/doors            | nur Tueren |
| POST    | /api/calculate/u-value              | U-Wert aus Bauteil |
| POST    | /api/calculate/envelope             | komplette Huellenbilanz |
| POST    | /api/calculate/solar-gains          | A_eff + Solargewinn pro Fenster |
| POST    | /api/calculate/heating-demand       | Envelope + Heizwaermebedarf + Ampel |

## Berechnung

### U-Wert (`calculateUValue`)
```
R_total = R_si + Sum(d_i / lambda_i) + R_se
U = 1 / R_total
```
Surface resistances per `ElementType` (DIN EN ISO 6946, Projektwerte):

| Bauteil       | R_si | R_se |
|---------------|------|------|
| externalWall  | 0.13 | 0.04 |
| roof          | 0.10 | 0.04 |
| floor         | 0.17 | 0.04 |
| window / door | 0.13 | 0.04 |

Modus `fixedUValue` uebernimmt einen festen U-Wert (z. B. Fenster mit Herstellerangabe).
Fehler werfen, keine stillen Fallbacks.

### H_T pro Wand
```
A_netto = max(0, A_brutto - A_Fenster - A_Tuer)
H = A_netto * U * Fx
```

### Korrekturfaktoren Fx (Projektwerte)

| boundaryType   | Fx  |
|----------------|-----|
| outside        | 1.0 |
| heatedRoom     | 0.0 |
| unheatedRoom   | 0.5 |
| corridor       | 0.5 |
| basement       | 0.6 |
| ground         | 0.6 |
| none           | 0.0 |

### Fenster: A_eff + Solar
```
A_eff = A * g * F_F * F_S * F_dirt * F_w     (alle Faktoren in [0, 1])
Q_solar = A_eff * I_orient   (kWh/a)
```
I_orient: Globalstrahlung vertikal pro Orientierung waehrend der Heizperiode
(Projektwerte fuer Deutschland):

| Orientierung | I [kWh/m^2*a] |
|--------------|---------------|
| Nord         | 100           |
| Ost / West   | 175           |
| Sued         | 350           |

### Tueren
H = A * U * Fx. Beheizter Raum: H = 0 (kein Fake). Keine boundary: ignored.

### Boden / Dach
U aus Schichtaufbau oder festem Bauteilwert. H_Boden = A * U * Fx (Fx aus
boundaryType, typ. ground/basement 0.6). H_Dach = A * U * 1.0 fuer
Aussenluftberuehrung.

### Lueftung
```
H_V = n * V * 0.34       (W/K)
V = Grundflaeche * Gesamtwandhoehe
```

### Heizwaermebedarf (vereinfacht)
```
Q_T = H_T * G_t          mit G_t = 84 kKh/a
Q_V = H_V * G_t
Q_g = Q_solar + Q_intern
Q_intern = 22 kWh/(m^2*a) * A_ref   (Projektpauschale Wohnen)
eta_gn = (1 - gamma^a) / (1 - gamma^(a+1))   mit a = 2, gamma = Q_g / Q_loss
Q_H,netto = max(0, Q_T + Q_V - eta_gn * Q_g)
Q_H,brutto = Q_H,netto / Anlageneffizienz
```

### Ampel (vereinfachte Projektgrenzen)

| Bereich kWh/(m^2*a) | Status |
|---------------------|--------|
| < 50                | gruen  |
| < 100               | gelb   |
| < 150               | orange |
| sonst               | rot    |

## Warum nur EIN Aussenwandaufbau-Feld

In einer normnahen Rechnung hat eine Aussenwand denselben Aufbau, unabhaengig
von der Himmelsrichtung. Die Orientierung gibt nur die Flaeche und den
angrenzenden Bereich. Daher: ein UI-Feld "Aussenwandaufbau". Der dort
berechnete U-Wert wird auf alle vier Orientierungen angewendet, pro
Orientierung entscheidet `boundaryType` ueber H_T.

Damit ist der Bug aus dem alten Screenshot weg: vorher hat das Projekt eine
konstante 0.28 W/(m^2*K) eingesetzt, obwohl oben "—" stand. Hier gibt es
diesen Default nicht. Fehlt der Aufbau, ist H_T null.

## Frontend-Struktur (Tabs)

1. **Dashboard** — Hero + KPI-Karten
2. **Gebaeudedaten** — Laenge, Breite, Etagen, Wandhoehe pro Etage, automatische
   Flaechen / Volumen / A_ref
3. **Gebaeudehuelle** — Accordion mit Aussenwaende · Fenster · Tueren · Boden ·
   Dach · Lueftung; Live-Bilanz und Ampel
4. **Ergebnisse** — H_T pro Bauteil, solare Gewinne, Heizwaermebedarf
   netto/brutto, spezifisch, Ampel

## Assets

Lege folgende Bilder unter `apps/frontend/public/assets/` ab:

* `hero-building.png` — Hero-Gebaeude (Dashboard, in HeroBuildingVisual)
* `wave-bg.png` — animierter Hintergrund (AnimatedWaveBackground)
* `hud-icons.png` — 4x3 Sprite, Floating-Icons (FloatingHudIcons)
* `logo.png` — Logo in der TopNavigation (BrandLogo)

Fehlen die Dateien, fallen die Komponenten automatisch auf SVG-Defaults zurueck
(kein Layout-Bruch, keine roten Image-Icons).

## Bekannte Vereinfachungen

* Korrekturfaktoren Fx sind Projektwerte, nicht Temperaturdifferenz-getrieben
* Erdreich-Boden wird wie unbeheizter Raum mit Fx = 0.6 behandelt (kein g-Faktor)
* Waermebrueckenzuschlag DeltaU_WB noch nicht modelliert
* Heizperiode G_t pauschal 84 kKh/a (Deutschland-Projektwert)
* Innere Gewinne pauschal 22 kWh/(m^2*a) (Wohnnutzung)
* Anlageneffizienz als ein Faktor (Erzeugung x Verteilung kombiniert)
* Steildachflaechen werden nicht orientierungsabhaengig solar gewertet

## Naechste sinnvolle Schritte

1. Waermebruecken DeltaU_WB als Pauschalzuschlag (z. B. 0.05 oder 0.10 W/(m^2*K))
2. H_T' = H_T / A_huell aus konsolidierter Huellflaeche
3. Standortabhaengige G_t (Klimadaten)
4. Solare Gewinne fuer Steildach-Flaechen (geneigt, eigener Strahlungsfaktor)
5. Eigene Schichtaufbauten im UI editierbar (nicht nur Katalog)
6. Persistente Projektdaten (lokale SQLite oder File-Storage)
