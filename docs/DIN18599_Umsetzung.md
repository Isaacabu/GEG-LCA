# DIN V 18599 – Umsetzungs-Spezifikation

Stand: Teil 2 (Kern) verifiziert direkt aus dem PDF (Seitenzahlen = gedruckte Seiten).
Ziel: Die auf der Website angezeigten Berechnungsergebnisse sollen nach DIN V 18599
berechnet werden (Monatsbilanzverfahren), nicht mehr per Gradstunden-Pauschale.

## 1. Kernverfahren Teil 2 – verifiziert (S. 27, 40)

**Heizwärmebedarf (Nutzwärmebedarf), Gleichung (1):**
```
Q_h,b = Q_sink − η · Q_source − ΔQ_c,b
```
- `Q_sink`  = Summe der Wärmesenken (Transmission + Lüftung + Abstrahlung), §5.3
- `Q_source`= Summe der Wärmequellen (solar + intern + Transmission/Lüftung-Gewinne), §5.4
- `η`       = monatlicher Ausnutzungsgrad der Wärmequellen, §5.5
- `ΔQ_c,b`  = Korrektur durch reduzierten Betrieb (Nacht/Ferien); für durchgehenden Betrieb = 0

**Kühlbedarf, Gleichung (2):** `Q_c,b = (1 − η) · Q_source`

**Ausnutzungsgrad (S. 40):**
```
γ = Q_source / Q_sink                          (Wärmequellen-/Senkenverhältnis)
η = (1 − γ^a) / (1 − γ^(a+1))   für γ ≠ 1       (24)
η = a / (a + 1)                 für γ = 1       (25)
a = a₀ + τ / τ₀                                 (26)
```
Für die **Monatsbilanz** (Gl. 144, im Text bestätigt): `a₀ = 1`, `τ₀ = 16 h`  ⇒ `a = 1 + τ/16h`

**Zeitkonstante der Zone (S. 40):**
```
τ = C_wirk / H            (22)     C_wirk = wirksame Wärmekapazität (§6.7.1)
H = H_T + H_V             (23)     Summe der Transfer-Koeffizienten Transmission + Lüftung
```

**Monatswerte & Jahressumme:** `Q_h,b,mth = d_mth · Q_h,b` (Gl. 4), `Q_h,b,a = Σ_mth Q_h,b,mth`
→ Die Bilanz wird **für jeden der 12 Monate** mit den jeweiligen Klima-/Randbedingungen
gerechnet und aufsummiert. Das ist der zentrale Unterschied zum jetzigen Code.

## 2. Aktuell (falsch) vs. DIN (korrekt)

| | Jetziger Code (`views.calculate`) | DIN V 18599-2 |
|---|---|---|
| Auflösung | 1 Jahreswert | 12 Monatsbilanzen |
| Heizwärme | `H_T · Gradstunden / 1000` | `Q_sink − η·Q_source` je Monat |
| Gewinne | Solar pauschal abgezogen | Solar + intern, gewichtet mit Ausnutzungsgrad η(γ,τ) |
| Lüftung | fehlt im genutzten Endpunkt | `H_V` Teil der Senken |
| Interne Gewinne | fehlen | aus Teil 10 je Nutzungsprofil |
| Klima | fester Gradstunden-Wert | Monats-Außentemp. + Solarstrahlung (Teil 1) |

## 3. Teil 2 – Detailformeln (verifiziert aus PDF, S. 47–89)

Pro **Monat m** wird gerechnet; `t_m` = Tage·24 h (Ergebnis in Wh, /1000 → kWh).

**Transmission (§6.2, S. 51–52):**
```
H_T = Σ_j (A_j · U_j · F_x,j)                              (47, 40)
Q_T,m = H_T · (θ_i − θ_e,m) · t_m       (Senke wenn θ_i > θ_e,m)   (45)
```
- `U_j` enthält Wärmebrückenzuschlag: `ΔU_WB = 0,10 W/(m²K)` ohne Nachweis (Standard),
  `0,15` bei innenliegender Dämmung + Massivdecke, `0,05`/`0,03` mit Nachweis n. DIN 4108 Bbl 2 (S. 52).
- `F_x` = Temperatur-Korrekturfaktor, **Tabelle 5** (S. 47, nicht erdberührt):
  Außenwand/Fenster/Dach = **1,0**; Dachgeschossdecke/Abseite = **0,8**; zu unbeheizt = **0,5**;
  zu niedrig beheizt (12–19 °C) = **0,35**; Glasvorbau: Einfach 0,8 / Zweischeiben 0,7 / WSV 0,5.
  **Tabelle 6** (S. 48, erdberührt): R-/B'-abhängig, typisch **0,30–0,55**.
- Das deckt sich mit dem Frontend: es sendet bereits `U_eff = U · F_x` (`getEffectiveU`).

**Lüftung (§6.3, S. 57):**
```
H_V = n · V · 0,34 Wh/(m³K)                                (63)
Q_V,m = H_V · (θ_i − θ_e,m) · t_m                          (61)
```
- `n` = Luftwechselrate (Infiltration + Nutzung/Fenster; mechanisch mit Wärmerückgewinnung reduziert).

**Solare Wärmequellen (§6.4, S. 72–73):**
```
Q_S,m = Σ_orient ( A_w · g · F_F · F_V · F_S · I_S,m,orient )   (112, 113)
```
- `g` = Gesamtenergiedurchlassgrad (Fenster-g-Wert), `F_F` ≈ 0,7 (Rahmenanteil),
  `F_V` = 0,9 (nicht senkrechter Einfall), `F_S` = Verschattung (Default ≈ 0,9),
  `I_S,m,orient` = monatliche Solarstrahlung je Orientierung (aus Teil 10/Teil 1).

**Wirksame Wärmekapazität (§6.7.1, S. 89):**
```
C_wirk = c · A_NGF      c = 50 (leicht) / 90 (mittel) / 130 (schwer)  Wh/(m²K)   (135–137)
```

**Interne Wärmequellen (§6.5/6.6):** `Q_I,m = q_I · A_NGF · t_betrieb,m` mit `q_I`, Betriebszeit aus **Teil 10**.

## 4. Noch zu extrahieren

- **Teil 10** Nutzungsrandbedingungen je Profil: Solltemp. θ_i, interne Wärmequellen q_I (Personen+Geräte),
  Luftwechsel n, Betriebszeiten/Nutzungstage – Wohnen + Nichtwohnen (Büro, Schule).
- **Teil 1** Referenzklima Deutschland: Monats-Außentemp. θ_e,m + Solarstrahlung I_S,m je Orientierung,
  Höhenkorrektur, Primärenergie-/CO₂-Faktoren.

## 4b. Teil 10 – Nutzungsrandbedingungen (verifiziert, S. 17, 36–43)

Interne Wärmequellen sind als **tägliche flächenbezogene Wärmezufuhr** `q_I` [Wh/(m²·d)] angegeben
(Personen + Arbeitshilfen, „mittel"-Spalte = Standard). Monatswert: `Q_I,m = q_I · A_NGF · d_Nutz,m`,
wobei `d_Nutz,m` = Nutzungstage im Monat (anteilig aus jährlichen Nutzungstagen).

| Profil | θ_i,h [°C] | Absenkung [K] | Nutzungstage/a | q_I (gering/mittel/hoch) [Wh/(m²·d)] | Luftwechsel |
|---|---|---|---|---|---|
| Wohnen EFH | 20 | 4 | 365 | 45 (fest) | n = 0,5 h⁻¹ (0,45 bedarfsgef.) |
| Wohnen MFH | 20 | 4 | 365 | 90 (fest) | n = 0,5 h⁻¹ |
| Einzelbüro (A.1) | 21 | 4 | 250 | 40 / **73** / 132 | V̇_Geb 2,5 m³/(h·m²) |
| Gruppenbüro (A.2) | 21 | 4 | 250 | 40 / **73** / 132 | 2,5 |
| Großraumbüro (A.3) | 21 | 4 | 250 | 60 / **102** / 166 | 2,5 |
| Besprechung (A.4) | 21 | 4 | 250 | 74 / **101** / 152 | 2,5 |
| Klassenzimmer/Schule (A.8) | 21 | 4 | 200 | 96 / **120** / 150 | 2,5 |

Weitere Wohngebäude-Werte (Tabelle 4): TWW-Nutzenergie `q_w,b = max[16,5 − (A_NGF,WE·0,05); 8,5] kWh/(m²a)`,
Anwendungsstrom `q_el = 63 Wh/(m²d)`, Verschmutzungsfaktor `F_V = 1`.
Luftwechsel NWG: effektiver Wert aus V̇_A,Geb / Raumhöhe (vereinfachter konstanter Monatsansatz, dokumentiert).

## 4c. Teil 1 + Teil 10 Anhang E – Klima & Faktoren (verifiziert)

**Referenzklima Deutschland / Referenzort Potsdam (Teil 10, Tabelle E.6, S. 92).**
Monatliche Außentemperatur θ_e [°C] und mittlere Strahlungsintensität I_S [W/m², **24-h-Mittel**):

```
Monat:        Jan  Feb  Mär  Apr  Mai  Jun  Jul  Aug  Sep  Okt  Nov  Dez
θe [°C]:      1,0  1,9  4,7  9,2 14,1 16,7 19,0 18,6 14,3  9,5  4,1  0,9
I_S horiz.:    29   44   97  189  221  241  210  180  127   77   31   17   (Dach)
I_S Süd 90°:   59   47   98  147  132  124  113  127  123  106   39   29
I_S Ost 90°:   25   29   68  134  137  150  138  115   83   55   20   12
I_S West 90°:  17   24   60  114  127  136  117  105   79   47   19   11
I_S Nord 90°:  10   18   31   58   75   83   81   57   41   25   13    7
```
**Umrechnung (verifiziert gegen Norm-Jahreswerte):**
`I_S,monat [kWh/m²] = I_S[W/m²] · 24 h · d_mth / 1000`
- Gegenprobe horizontal: Ø122 W/m² · 8760 h = 1069 ≈ 1072 kWh/(m²a) (Norm) ✓
- Gegenprobe Süd 90°: Ø95,3 · 8760 = 835 ≈ 838 (Norm) ✓

Tage/Monat: 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31.

**Primärenergie- & CO₂-Faktoren (Teil 1, Tabelle A.1, S. 78):**

| Energieträger | f_P (gesamt) | f_P (n. ern.) | CO₂ [g/kWh] |
|---|---|---|---|
| Erdgas | 1,1 | 1,1 | 240 |
| Heizöl | 1,1 | 1,1 | 310 |
| Holz/Pellets | 1,2 | 0,2 | 40 |
| Fernwärme (KWK, fossil) | 0,7 | 0,7 | (KWK-abhängig) |
| Strom (netzbezogen) | 2,8 | 2,4 (DIN) | 560 |

> Hinweis Strom: GEG 2024 (Anlage 4) setzt für Netzstrom f_P,n.ern. = **1,8** (rechtlich maßgeblich),
> DIN V 18599-1:2018 Tabelle A.1 nennt **2,4**. Im Tool als Konstante hinterlegt + dokumentiert.
> Heizsystem-Faktoren der Website stimmen für Gas (1,1 / 240) und Pellet (0,2 / 40) bereits exakt.

## 5. Geplante Umsetzung (stufenweise)

- **Stufe 1 – Heizwärmebedarf nach Monatsbilanz** (Teil 2 + 10 + 1): ersetzt den Gradstunden-Kern,
  speist die angezeigten Werte (H, Solar, Q_h,b, spezifisch, Bewertung).
- **Stufe 2 – Warmwasser (Teil 8) + Lüftungsanlage (Teil 6)** in der Anlagentechnik.
- **Stufe 3 – Beleuchtung (Teil 4) + Kühlung (Teil 3)** (nur Nichtwohngebäude).

## 6. Status & Umsetzung

**Stufe 1 ist umgesetzt und verifiziert.** ✅

- Rechenkern: `dashboard/services/din18599.py` (`calculate_heat_demand`) – Monatsbilanzverfahren,
  Klimadaten Potsdam, Profile aus Teil 10, Faktoren aus Teil 1.
- Angeschlossen an den **aktiv genutzten** Endpunkt `dashboard/views.calculate` (`/calculate/`).
  Das alte Gradstundenverfahren und die tote `din_v18599.py` wurden **entfernt**.
- Liefert zusätzlich die DIN-Kontextfelder, die das Frontend schon erwartet
  (`usage_label`, `climate_location_label`, `internal_gains_density`, `n_persons`).

**Verifikation** (`scripts/verify_din18599.py`, Referenz-EFH 150 m², GEG-nah, Stand nach
Eingabe-Korrekturen):
- H_T = 126,22 W/K = 88·0,24 + 100·0,20 + 100·0,175 + 30·1,10 + 2·1,30 + **0,10·320 (ΔU_WB)**
  (Fassaden brutto 120 m², Fenster/Tür 32 m² abgezogen → Wände netto 88 m²; von Hand ✓)
- H_V = 66,3 W/K, τ = 70,1 h
- Monatsphysik korrekt: Winter η ≈ 1,0 (Gewinne voll nutzbar), Sommer Q_h = 0
- Ergebnis: Q_h,b,a = 11 046 kWh/a → **73,6 kWh/(m²a)** (plausibel mit Pauschal-ΔU_WB 0,10)
- Nichtwohngebäude (Klassenzimmer): θ_i = 21 °C, 200 Nutzungstage → ~84 kWh/(m²a)

**Eingabe-Pipeline-Korrekturen (nach Nutzer-Feedback „unrealistische Werte"):**
1. **Fenster-/Türabzug:** Geometrie liefert Brutto-Fassaden; der Rechenkern zieht Fenster und
   Türen je Orientierung ab (vorher Doppelzählung der Öffnungsflächen).
2. **Wärmebrücken:** ΔU_WB = 0,10 W/(m²K) auf die gesamte Hüllfläche ergänzt (Gl. 47 / GEG-
   Pauschale ohne Gleichwertigkeitsnachweis; 0,05 bei Planung nach DIN 4108 Bbl 2 → späterer
   UI-Schalter).
3. **Luftvolumen:** geliefertes Geometrie-Volumen ist brutto (V_e) → V_Luft = 0,76·V_e
   (≤ 3 Vollgeschosse) bzw. 0,80·V_e nach DIN V 18599-1 (vorher ~25 % zu hohe Lüftungsverluste).
4. **Profil-Auflösung:** Frontend-Varianten („Schulgebäude", „Bürogebäude", „nicht_wohngebaeude" …)
   waren dem Backend unbekannt → stiller Rückfall aufs **EFH-Profil** (im Screenshot des Nutzers als
   „Wohngebäude (EFH) – Schulgebäude" sichtbar). Mapping vervollständigt; Nutzungen ohne eigenes
   Profil (Hotel, Einzelhandel …) auf das nächstliegende gemappt (dokumentierte Näherung).
5. **F_x durchgängig:** Frontend sendet jetzt `*_fx` je Orientierung + Boden. Fenster/Türen einer
   Wand erben deren F_x (Innenwand-Fenster zählen nicht mehr als Außenverluste); der
   Wärmebrückenzuschlag wird F_x-gewichtet (Gl. 47: Σ(U_i + ΔU_WB)·A_i·F_x,i) – Flächen an
   beheizte Nachbarräume fallen komplett aus der Umfassungsfläche heraus. Boden-Randbedingung
   („grenzt an" + Temperatur) wirkt jetzt tatsächlich (vorher ignoriert, stiller Fallback U = 0,25).
6. **Höhenkorrektur:** `elevation_m` wirkt jetzt: Δθ = 0,0065 K/m über Stationshöhe Potsdam (81 m);
   z. B. Augsburg 500 m → −2,7 K auf alle Monatsmittel (vorher ignoriert).
7. **NWG-Luftwechsel nutzungszeitgewichtet:** Profil-Luftwechsel gilt nur während der Nutzungszeit
   (neu: `usage_hours` je Profil; Klassenzimmer 7 h/200 d), außerhalb Infiltration 0,15 h⁻¹ →
   n_eff Klassenzimmer ≈ 0,25 statt konstant 0,8 (vorher ~3-fach überhöhte Lüftungsverluste bei NWG).

**Validierung am realen Fall (Hochschul-Klassenraum 111 m², Augsburg, nur Ost-Fassade außen):**
falsch modelliert/alte Bugs: 167 kWh/(m²a) „Kritisch" → korrekt modelliert mit Fixes:
H_T = 45,8 W/K, n_eff = 0,25, **39,7 kWh/(m²a) „Sehr gut"** – plausibel.
Hinweis Bedienung: Bei Einzelraum-Betrachtung nur tatsächliche Außenbauteile ansetzen
(Innenwände/-fenster/-türen über Randbedingung „beheizt" → F_x = 0).

## 11. UI-/Berechnungs-Audit (alle Tabs)

**Hülle:**
- Boden bietet jetzt **komplette Aufbauten** statt Einzelmaterialien (Passivhaus 0,15 … Altbau
  ungedämmt 1,30) – die nackte Betonplatte (U 3,77) als einzige Option erzeugte ~300 kWh/(m²a).
- **Dach-Randbedingung** neu (Tab. 5): Außenluft 1,0 · unbeheizter Dachraum 0,8 · beheizt darüber 0.
- Ergebniszeile: „Wärmeverluste brutto" / **„Heizwärmebedarf netto Q_h,b"** (jetzt sichtbar) /
  „Spezifisch netto" – vorher stand brutto neben netto-spezifisch ohne Kennzeichnung.
- Tür-Preset „Stahlzarge Innentür" als ⚠ nicht-Hülle markiert.

**PV (Korrektur der Doppelverluste):** Der spezifische Ertrag (950 kWh/kWp·a) enthält bereits die
Systemverluste (Performance Ratio); zusätzlich wurden ×0,85 (Systemwirkungsgrad) ×0,85 (Verluste)
abgezogen → **Ertrag ~30 % zu niedrig**. Feld „Systemwirkungsgrad" entfernt, nur noch „zusätzliche
Verschattung" (Default 5 %). Neu: **Orientierungsfaktoren** Dach 1,0 · Süd-Fassade 0,70 ·
O/W-Fassade 0,55 (vorher bekamen senkrechte Fassaden den vollen Dachertrag). CO₂-Faktor 0,56
(GEG) statt 0,45.

**Energiebilanz (Endenergie-konsistent):** Vorher wurden Nutzenergie (Q_h,b) und Endenergie
addiert, WP-Strom fehlte im Strom, PV verrechnete nur gegen Hilfsstrom, CO₂ nur Strom. Jetzt:
Brennstoff-Endenergie + Strom (Anlagentechnik inkl. WP + Haushaltsstrom-Eingabefeld) −
PV-Eigenverbrauch; CO₂ gesamt = Anlagen-CO₂ + Haushalt·0,56 − PV·0,56. Frontend nutzt das
gespeicherte Anlagentechnik-Ergebnis (`window.lastSystemResult`).

**Gebäudedaten:** veralteter Gradstunden-Hinweis durch DIN-Monatsbilanz-Beschreibung ersetzt;
„Anzahl Personen"/„Betriebsstunden" als *informativ* gekennzeichnet (Profilwerte nach Teil 10
sind maßgeblich).

## 12. Output-Benennung & Verständlichkeit (UX-Pass)

Durchgängiges Muster für alle Ergebnisfelder:
- **Benennung:** einfacher deutscher Begriff + DIN-Symbol in Klammern, z. B.
  „Heizwärmebedarf (Q_h,b)", „Endenergie Heizung (Q_f)", „Primärenergie je m² (q_p)",
  „Wärmeverlust-Koeffizient (H_T)", „Hilfsenergie Strom (W_f)".
- **ⓘ-Tooltips** (reines CSS, `data-tip`): jede Ergebnis-Box erklärt in Alltagssprache, was der
  Wert bedeutet, nennt die DIN-Quelle und typische Richtwerte.
- **Ampel-Bewertung** über zentralen Helper `setKpi(id, wert, einheit, {good, mid,
  lowerIsBetter, bench})`: Wert + Box-Rand werden grün/gelb/rot gefärbt, darunter erscheint eine
  Richtwert-Zeile (z. B. „≤40 sehr gut (Neubau) · 40–80 mittel · >80 hoch").
  Bewertet werden nur *spezifische* Kennwerte (je m²) und die JAZ – Absolutwerte sind nicht
  benchmarkfähig. Schwellen: Heizwärmebedarf 40/80 · Endenergie 50/100 · Primärenergie 60/120
  (= SYSTEM_RATING_THRESHOLDS) · JAZ ≥4/≥3 (höher = besser) · Gesamt-Endenergie 75/150 ·
  CO₂ 10/25 kg/(m²a).
- **Energiebilanz-Tab** neu gegliedert in ① Gebäudehülle → ② Anlagentechnik → ③ Strom & PV →
  ④ Gesamtbilanz (neu: Endenergie gesamt, Endenergie/m², CO₂ gesamt, CO₂/m² mit Ampel);
  Haushaltsstrom-Eingabe direkt im Strom-Abschnitt, Hinweistext zur Tab-Reihenfolge.
- Doppelte Ergebnis-Box „Endenergie / Verbrauch gesamt" entfernt (identisch mit „Endenergie
  gesamt"); „Heizwärmebedarf netto Q_h,b" im Hülle-Tab jetzt sichtbar (war hidden).

## 13. Ausbau: Nachtabsenkung (Teil 2), Beleuchtung (Teil 4), PV (Teil 9) ✅

**Nachtabsenkung / reduzierter Nachtbetrieb (Teil 2, Gl. 28–30):** in `din18599.py` integriert.
`θ_i,h = max(θ_i,soll − f_NA·(t_NA/24)·(θ_i,soll − θ_e), θ_i,soll − Δθ_i,NA)` mit
`f_NA = 0,26·exp(−τ/250)` (Heizungsabschaltung, EFH lt. Teil 10 Fußn. b) bzw. `0,13·exp(−τ/250)`
(Absenkung, MFH/NWG); t_NA = 24 − Heizbetriebsdauer (Wohnen 17 h, Büro 13 h, Schule 9 h);
Δθ_i,NA = 4 K. Referenz-EFH: 73,6 → **67,8 kWh/(m²a)** (−8 %, plausibel). Abschaltbar über
`night_setback=false`. Wochenend-/Ferienbetrieb (6.1.2.3) weiterhin offen.

**Beleuchtung (Teil 4, Tabellenverfahren 5.4.2):** `dashboard/services/din18599_licht.py`.
`p = p_j,lx(k, Beleuchtungsart)·E_m·k_A·k_Lampe` (Tab. 5 mit k-Interpolation; Lampenfaktoren
Tab. 6: LED-Leuchte 0,49 · LED-Ersatz 0,53 · T5 0,80 · LSL-EVG 1,0);
`F_Prä = 1 − F_A·C_Prä,kon` (Gl. 40; 0,5/0,95); effektive Zeiten Gl. (4)–(6) mit Profilwerten aus
Teil 10 Anhang A (Büro: 500 lx, 2543/207 h, F_t 0,7 · Klassenzimmer: 300 lx, 1400/0 h, F_t 0,9).
F_TL als dokumentierter Anhaltswert je Kontrollart (gedimmt 0,55 / geschaltet 0,70 / manuell 0,80)
statt detailliertem C_TL-Verfahren. Nur NWG; fließt in Endenergie/PE/CO₂ der Anlagentechnik ein
(Strom). Beispiel Klassenzimmer 111 m², LED gedimmt + Präsenz: **2,35 kWh/(m²a)** ✓.

**Photovoltaik (Teil 9, Gl. 64–67 + Anhang B):** `calculate_pv` ersetzt das MVP-Modell.
`Q_el,prod,PV = E_sol·(P_pk/1 kW/m²)·f_perf` monatlich; `P_pk = k_pk·A` (Tab. B.2 ab 2017:
mono 0,182 / poly 0,166 kW/m²); f_perf Tab. B.1 (0,70/0,75/0,80 je Belüftung). Strahlung je
Orientierung aus Tab. E.6 (Fassaden exakt 90°; Dach-Süd-Näherung 0,72·horizontal + 0,48·Süd-90°
≈ Süd-45°-Zeile, Jahressumme ~1 170 kWh/m²a). 40 m² mono belüftet → 7,28 kWp, **836 kWh/kWp** ✓
(= 1 171·0,75·0,95). Frontend ruft den Endpunkt auf (Zelltyp/Montage-Auswahl statt „Modultyp").

**Werkzeuge** (Norm-Auswertung, reproduzierbar):
- `scripts/din_page.py <teil> <von> <bis>` – rendert Normseiten als Bild (`scripts/_din_render/`)
- `scripts/din_table.py <teil> <seite>` – extrahiert Tabellen koordinatenbasiert (für exakte Werte)

**Offene Punkte für höhere Genauigkeit (spätere Stufen):**
- Echte 15 Klimaregionen (Teil 10 Anhang E). Umgesetzt ist stattdessen: Höhenkorrektur
  (0,0065 K/m über Potsdam 81 m) + optionale Bundesland-Skalierung (`climate.py`,
  DWD-Jahresmittel – **kein** Norm-/Referenzklima-Verfahren; für den Referenzklima-
  Nachweis Bundesland auf Standard lassen).
- Detaillierte Verschattung F_S (Horizont/Überstand) statt Pauschalwert 0,9.
- Opake solare Gewinne / langwellige Abstrahlung (§6.4.1) – nicht angesetzt.
- (Nachtabsenkung ist umgesetzt, s. §13; Wochenend-/Ferienbetrieb 6.1.2.3 offen.)

---

# Stufe 2 – Anlagentechnik (Teil 8 Warmwasser, Teil 5 Heizung, Teil 6 Lüftung)

## 7. Teil 8 – Trinkwarmwasser (extrahierte Normgrundlagen)

Bilanzkette (Abschnitt 4.4 / Gl. in 4.3): `Q_w,outg = Q_w,b + Q_w,ce + Q_w,d + Q_w,s`,
Endenergie über Erzeuger; Hilfsenergie `W_w = W_w,ce + W_w,d + W_w,s + W_w,gen`.

### 7.1 Nutzenergie Q_w,b (aus Teil 10)

- **Wohnen** (Tab. 4, Fußnote d): `q_w,b = max[16,5 − A_NGF,WE·0,05; 8,5] kWh/(m²a)`
  (A_NGF,WE = NGF einer mittleren Wohneinheit; EFH = ganzes Haus).
  Monatlich: `Q_w,b = q_w,b/365 · d_mth · A_NGF`.
- **NWG** (Tab. 7, flächenbezogen Wh/(m²·d), monatlich `Q_w,b = q_w,b,d · d_nutz·d_mth/365 · A`):
  Büro 30 · Schule ohne Duschen 130 · Schule mit Duschen 500 (je Klassenraumfläche) ·
  Hotel mittel 350 · Restaurant 920 (Gastraum). Bürowert < 0,2 kWh/Person·d ⇒ darf vernachlässigt werden (Fußn. b).

### 7.2 Übergabe (6.1, S. 28)

**Q_w,ce = 0, W_w,ce = 0** (Auslaufverluste stecken in Q_w,b). Korrektur Gl. (12): `Q*_w,b = f_Zapf·Q_w,b`
mit f_Zapf = 0,98 (Thermostatarmaturen an Dusche/Wanne) bzw. 1,05 (hydraulischer Durchlauferhitzer).

### 7.3 Verteilung (6.2, S. 29–38)

Grundgleichung (13): `Q_w,d,i = (1/1000)·U_i·L_i·(θ_w,av − θ_I)·d_op,mth·t_op,day` [kWh/Monat]

**Randbedingungen (Tab. 6, S. 27):** θ_I beheizt = 20 °C (unbeheizt 13 °C); mit Zirkulation θ_w,av = 57,5 °C;
ohne Zirkulation θ_w,av = 25·U^(−0,2) °C (24 h/d, halbe V/S-Längen s. u.); Anbindeleitung dezentral
elektronisch geregelt: 20·U^(−0,2); Speicher θ_s,av = 55 °C; Kaltwasser θ_K = 10 °C; Δθ_Z = 5 K.
Mit Zirkulation: Betrieb t_op,day = z (Pumpenlaufzeit), Rest des Tages (24−z) mit θ_w,av = 25·U^(−0,2)
und halber Zirkulationslänge.

**U-Werte (Tab. 8, S. 31)** [W/(m·K)]: gedämmt nach 1995: V = 0,200; S/SL = 0,255
(1980–95: 0,2/0,3–0,4; vor 1980: 0,4; ungedämmt A_NGF ≤ 200 m²: 1,0).

**Standardlängen (Tab. 10, S. 33, Einzonen-Gebäude, Gruppe 1 = Wohnen):**
- Netztyp I (Steigstrangtyp, Standard): `L_v = 0,11·(A_NGF/n_G)^1,24`, `L_s = 0,005·A_NGF^1,38`,
  `L_A = 0,09·A_NGF^1,00` (Gruppe 2 Büro: L_v = 5,40·(A/N)^0,49, L_s = 0,025·A^0,97, L_A = 0,02·A;
  Gruppe 3 Schule: wie G2, aber L_A = 2,39·A^0,43).
- **Ohne Zirkulation** (6.2.2.3, S. 35): L_v und L_s **halbieren**, L_A unverändert.
- V (Verteilung) liegt standardmäßig im **unbeheizten** Bereich (Keller, θ_I = 13 °C, Netztyp I),
  S/SL im beheizten Bereich (Verluste = ungeregelter Wärmeeintrag Q_I,w nach Gl. 15).

**Hilfsenergie Zirkulationspumpe (6.2.2.4, S. 35–37):**
`W_w,d = W_w,d,hydr · e_w,d,aux` (16); `W_w,d,hydr = P_hydr/1000 · d_op,mth · z` (17);
Laufzeit `z = 10 + 1/(0,07 + 50/A_NGF)` h/d, EFH ≤ 24 h, MFH 16…24 h (18);
`P_hydr = 0,2778·Δp·V̇` W (19) mit `V̇ = P_w,d,A/(1,15·Δθ_Z·1000)` m³/h (20),
`P_w,d,A = Σ U_i·L_i·(57,5 − θ_i,h,soll)` W (21), `Δp = 0,1·L_max + 12 + 1` kPa (22; Speicher 1 kPa,
Durchfluss 15 kPa), `L_max = 2·(L_char + 2,5 + n_G·h_G)` (23);
`e_w,d,aux = f_e·(C_p1 + C_p2)` (24), `f_e = (1,25 + (200/P_hydr)^0,5)·b`, b = 1;
Tab. 11: ungeregelt C_p1 = 0,25, C_p2 = 0,94; geregelt 0,50/0,63.

### 7.4 Speicherung (6.3.1, S. 39–40)

`Q_w,s = f_con · ((θ_s,av − θ_I)/45) · d_op,mth · Q_s,P0,day` (25), f_con = 1,2 (Speicher beim Erzeuger
im selben Raum, sonst getrennte Berechnung), (55−20)/45 = 0,778.
Bereitschaftsverlust neu (≤ 1000 l): `Q_s,P0,day = 0,8 + 0,02·V_s^0,77` kWh/d (26)
(> 1000 l: 0,39·V_s^0,35 + 0,5 (27); stetig bei 1000 l ✓). Elektrische Speicher-WP: P_s,P0 = 49 W bei 50 °C (Tab. B.2).

### 7.5 Erzeugung (6.4)

**Heizkessel (6.4.12, S. 80–82, Standardwerte S. 89–91):**
- Nennwirkungsgrad: `η_k,Pn = (A + B·log10(P_n))/100` (122), Tab. 30:
  Brennwertkessel Öl/Gas nach 1994: A = 92, B = 1; „verbessert" ab 1999: A = 94, B = 1;
  NT-Kessel Gas nach 1994: A = 88,5, B = 1,5; Pelletkessel m. Puffer nach 1994: A = 92, B = 0,5;
  Pellet-Brennwert m. Puffer: A = 100, B = 1.
- TWW-Korrektur: `η_k,Pn,w = η_k,Pn + K·(50 − θ_s,av)` (105), K nach Tab. 26/27 (Brennwert: Temperatur-
  korrekturfaktor; vereinfacht K = 0,001/K für Brennwert).
- Bereitschaftsverlust: `q_P0,70 = (E·P_n^F)/100` (123), Tab. 31: Brennwert nach 1994: E = 4,0, F = −0,4;
  NT-Gas nach 1994: E = 4,5, F = −0,4; Pellet nach 1994: E = 3,0, F = −0,2.
  Temperaturumrechnung: `q_P0,θ = q_P0,70·((θ_gen,av − θ_I)/50)` (106), θ_gen,av = 50 °C (Zirkulation läuft)
  bzw. 40 °C (Durchlauferhitzer/Kombi ohne Zirkulation).
- Tageslaufzeit Nennleistung: `t_w,Pn,day = Q_w,outg/(P_n·d_op,mth)` (107).
- Verluste: `Q_w,gen = q_w,gen,Pn,day·… + Q_w,gen,P0,day·…` (102–104) mit
  `q_w,gen,Pn,day = (f_Hs/Hi/η_k,Pn,w − 1)·Q_w,outg/d_op,mth` und
  `Q_w,gen,P0,day = q_P0,θ·P_n·(t_op,day − t_w,Pn,day)·f_Hi/Hs`-Logik; f_Hs/Hi Gas = 1,11, Öl = 1,06, Pellet = 1,08.
- Hilfsenergie (111): `W_w,gen = P_aux,Pn·t_w,Pn,day·d_op,mth + P_aux,P0·(24 − t_w,Pn,day)·d_op,mth`,
  Tab. 32: Gebläsebrenner P_aux,Pn = 45·P_n^0,48 /1000 kW, P_aux,P0 = 0,015 kW.
- Strahlungsverluste im Aufstellraum beheizt: Anteil q_k,B = 0,75·q_P0,θ (109) als ungeregelter Eintrag.

**Fernwärme (6.4.16, S. 95–97):** `Q_w,gen = H_DS·(θ_DS − θ_I)·d_mth/365` (131),
`H_DS = B_DS·P_DS^(1/3)` (132), `θ_DS = D_DS·θ_prim + (1−D_DS)·θ_sek` (133).
Tab. 34 (Warmwasser niedrige Temp.): θ_prim = 105 °C, D_DS = 0,6; Tab. 35 B_DS (Dämmklasse 3,
WW niedrige Temp.): B_DS = 4,0. Hilfsenergie ≈ 0 (vernachlässigt; nur W_h,gen = 10 kWh/a bei
Vorlauftemperaturregelung).

**Wärmepumpe TWW (Anhang B, S. 101–103):** Standard-Leistungszahl bei 50 °C:
**COP_w,t = 3,06** (Tab. B.1); Abluft-WP: 3,8. Elektrische Deckung Speicherverluste P_s,P0 = 49 W (50 °C).
Endenergie vereinfachte Bilanz: `Q_w,f = Q_w,outg/COP_w,t` + Speicher-Standby elektrisch.

**Nicht umgesetzt (kein UI-Input vorhanden):** Solarthermie (6.4.2/6.4.3), KWK, Durchlauferhitzer-
Sonderfälle, Mehrkesselanlagen → dokumentierte Vereinfachung.

## 8. Teil 5 – Heizungsanlagen (extrahierte Normgrundlagen)

Prozesskette: `Q_h,outg = Q_h,b + Q_h,ce + Q_h,d + Q_h,s` → Erzeuger → Endenergie (Hs-bezogen bei
Brennstoffen). Belastungsgrade (Gl. 8–11): `β_h,ce = Q_h,b/(Φ_h,max·t_h)`,
`β_h,d = (Q_h,b+Q_h,ce)·f_hydr/(Φ_h,max·t_h)` usw.; f_hydr = 1,06/1,02/1,00 (Tab. 6: kein/üblicher/
statisch abgeglichener hydraulischer Abgleich). Φ_h,max = Gebäudeheizlast ≈ (H_T+H_V)·(θ_i − θ_e,Ausl)
(θ_e,Ausl Potsdam = −14 °C; dokumentierte Näherung).

### 8.1 Übergabe (6.2, S. 43–57)

`Q_h,ce = Q_h,b · Δθ_ce/(θ_i,h − θ_e)` (34); `Δθ_ce = Δθ_str + Δθ_ctr + Δθ_emb + Δθ_rad + …` (35).
**Tab. 10 (Heizkörper):** Δθ_ctr,1: ungeregelt 2,5 · Führungsraum 2,0 · elektromech. RT-Regelung 1,8 ·
P-Regler (vor 1988) 1,4 · P-Regler 1K 1,2 · PI 1,2 · PI optimiert 0,9. Δθ_str = (Δθ_str,1+Δθ_str,2)/2 (42):
60 K (90/70): 1,2 · 42,5 K (70/55): 0,7 · 30 K (55/45): 0,5 (Ein-Rohr alt: 1,6/1,2). Δθ_rad: Radiator
Innenwand 1,3 · Außenwand 0,3 · vor Glas o. Strahlungsschutz ~1,9. Δθ_emb = 0.
**Tab. 11 (Flächenheizung):** Δθ_ctr wie oben; Δθ_emb = (Δθ_emb,1+Δθ_emb,2)/2 (43): Nasssystem ~0,35 ·
Trockensystem ~0,2; Verluste über angrenzende Flächen: ohne Mindestdämmung +1,4 · mit +0,5 ·
100 % besser +0,1. Hilfsenergie Regelung: `W_C = P_C,aux·d_mth·24/1000` (45), Tab. 20:
0,1 W (elektromotorisch) – 1,0 W (elektrothermisch) je Antrieb; Thermostatventil = 0.

### 8.2 Mittlere Heizmedien-/Heizkreistemperatur (5.3, S. 37–39)

`θ_HK,av(β) = 0,5·(θ_VL,av + θ_RL,av)` (12); Zweirohr (14/16):
`θ_VL/RL,av(β) = (θ_VA/RA − θ_i,h,soll)·β^(1/n) + θ_i,h,soll`, Heizflächenexponent n = 1,3 (Heizkörper) /
1,1 (FBH). Temperaturadaption (18/19): β_h,ad = 0,7·β (unbegrenzte Vorlauf-Adaption) bzw. 0,9·β
(begrenzt). Auslegung: 70/55, 55/45 (Heizkörper), 35/28 (FBH). Brennwert nutzt θ_RL,av.

### 8.3 Verteilung (6.3, S. 60–69)

`Q_h,d,i = (1/1000)·U_i·L_i·(θ_HK,av − θ_I)·t_h,rL` (52). Tab. 24: θ_I = 20 °C beheizt / 13 °C unbeheizt /
22 °C außerhalb Heizperiode. Tab. 25 Gruppen: G1 = Wohnen, Büro, Hotels…; G2 = Schulen….
**Tab. 26 Standardlängen Netztyp I** (gegen BBSR-Endbericht „Leitungslängen“ delta-q verifiziert ✓):
G1: `L_V = 30 + 2,3·A_NGF^0,79` · `L_S = 2,56·A_NGF^0,1 + 0,0006·A_NGF·h_G·n_G` · `L_A = 0,06·A_NGF^1,13`
G2: `L_V = 30 + 1,5·A^0,79` · `L_S = 0,0050·A + 1,50·H^1,0` · `L_A = 0,05·A`.
U-Werte Tab. 27 = Tab. 8 aus Teil 8 (gedämmt nach 1995: V 0,200; S/A 0,255).
Hinweis: Standardlängen sind normseitig bewusst konservativ (vgl. BBSR-Bericht) – bei EFH dominiert L_V.
**Pumpe (6.3.2):** `W_h,d = P_hydr/1000·β_h,d·t_h·f_dLPM·f_Sch · e_h,d,aux` (56) mit
`P_hydr = 0,2778·Δp·V̇` (57), `V̇ = Φ_h,max/(1,15·Δθ_HK)` (58),
`Δp = 0,13·L_max + 2 + Δp_FBH(25) + Δp_gen + Δp_WMZ + Δp_Strang` (59; Gas-BW < 35 kW: Δp_gen = 20·V̇²),
`L_max = 2·(L_char + B_char/2 + n_G·h_G + 10)` (60);
`e_h,d,aux = f_e·(C_P1 + C_P2·β_h,d⁻¹)·(EEI/0,25)` (61), `f_e = 1,25 + (200/P_hydr)^0,5` (62, b = 1);
Tab. 28: ungeregelt 0,25/0,75 · Δp_konst 0,75/0,25 · Δp_variabel 0,90/0,10. f_dLPM = 1/0,75/0,45.

### 8.4 Speicher (6.4, S. 70–71)

`Q_h,s = f_con·((θ_h,s − θ_I)/45)·d_op,mth·Q_s,P0,day` (68) – Q_s,P0,day wie Teil 8 Gl. (26).
Nur bei Puffer (Pellet/WP) relevant; Gas-Brennwert/Fernwärme: kein Speicher (Standardfall).

### 8.5 Erzeuger Heizkessel (6.5.4, S. 120–143)

Standardwerte (6.5.4.3.7): `η_k,Pn = (A + B·log10 P_n)/100` (217), `η_k,Pint = (C + D·log10 P_n)/100` (218),
`q_P0,70 = E·P_n^F/100` (219). **Tab. 49:** Brennwert nach 1994: A 92/B 1/C 98/D 1; „verbessert" ab 1999:
94/1/103/1; NT-Gas nach 1994: 88,5/1,5/86?/1,5; Pellet m. Puffer: 92/0,5/91/0,8; Pellet-Brennwert m.
Puffer: 100/1/98/1. **Tab. 50:** Brennwert nach 1994: E 4,0/F −0,4; NT 4,5/−0,4; Pellet 3,0…4,0/−0,2.
Temperaturkorrektur (185/186): `η_gen,Pn = η_k,Pn + K·(70 − θ_HK,av)`,
`η_gen,Pint = η_k,Pint + L·(θ_Test,Pint − θ_RL,av)` (Brennwert: θ_RL, Test Pint = 30 °C); Tab. 39: Brennwert
Gas K = L = 0,002; NT 0,0004/0,0004; Standard 0/0,0004. `q_P0,θ = q_P0,70·(θ_HK,av − θ_I)/50` (184).
Verlustleistungen: `P_gen,P0 = q_P0,θ·(P_n/η_k,Pn)·f_Hs/Hi` (183);
`P_gen,Pint = (f_Hs/Hi − η_gen,Pint)/η_gen,Pint · β_Pint·P_n` (187, β_Pint = 0,3);
`P_gen,Pn = (f_Hs/Hi − η_gen,Pn)/η_gen,Pn · P_n` (188). Tagesverluste linear interpoliert über β_h,gen
(179/180), `β_h,gen = P_d,in/P_n` (154), `P_d,in = Q_h,outg/(d_h,rB·(t_h,rL,day − t_w,Pn,day))` (181).
Rückgewinnbar: `q_s,θ = 0,5·q_P0,θ` (Gas-Spezial) bzw. 0,75 (übrige) → Q_I,h,gen (191).
Hilfsenergie (220): `P_aux,x = (G + H·P_n^n)/1000` kW; Tab. 51: Gebläsebrenner Pn: 0/45/0,48;
P0: 15/0/0 (= 15 W). f_Hs/Hi: Erdgas 1,11 · Heizöl 1,06 · Holz/Pellet 1,08.

### 8.6 Fernwärme (6.5.9, S. 158–159) & Wärmepumpe

Fernwärme identisch zu Teil 8: Gl. (242–244), Tab. 61: Warmwasser-Netz niedrige Temp.:
θ_prim = 105 °C, D_DS = 0,6; Tab. 62: B_DS = 4,0 (Dämmklasse 3). Hilfsenergie ≈ 0.
**Elektro-WP – dokumentierte Vereinfachung:** Das Norm-BIN-Verfahren (Anhang B/C, stundenbasierte
Wetterklassen + Produkt-Prüfpunktfelder) ist ohne Produktdaten nicht anwendbar. Stattdessen
Monatsmodell über Carnot-Gütegrad: `η_g = COP_Prüf/COP_Carnot(Prüfpunkt)` (Prüfpunkt A2/W35 bzw.
B0/W35), dann je Monat `COP_m = η_g·T_sink/(T_sink − T_source,m)` mit T_sink = θ_HK,av(β_m)+Spreizung/2
(aus 8.2) und T_source = θ_e,m (Luft) bzw. Erdreich ~ konst. **TWW-COP: dasselbe Carnot-Modell mit
Senke θ_s,av = 55 °C (min ΔT 10 K), also monatlich variabel** – abweichend vom Norm-Standardwert
COP_w,t = 3,06 fix bei 50 °C (Teil 8 Anhang B); im Winter konservativer, im Sommer günstiger. →
liefert realistische Jahresarbeitszahlen; exaktes BIN-Verfahren als späterer Ausbau dokumentiert.

## 9. Teil 6 – Wohnungslüftung (extrahierte Normgrundlagen)

**Zulufttemperatur mit WRG (5.2.2, Gl. 14/15):**
`θ_V,mech = θ_e + η_t,unit·(θ_eta − θ_e)` mit θ_eta = Ablufttemperatur ≈ θ_i (20 °C) und
η_t,unit = Wärmebereitstellungsgrad des Geräts (UI: > 60 % / > 80 %).
→ Lüftungswärmesenke in Teil 2 aufgeteilt: `Q_v = 0,34·V·[n_inf·(θ_i − θ_e) + n_mech·(θ_i − θ_V,mech)]`,
d. h. mechanischer Anteil wird mit Faktor (1 − η_WRG) gewichtet.

**Anlagenluftwechsel (5.3 + Standardwerte S. 72):** n_mech = 0,4 h⁻¹ (nicht bedarfsgeführt) /
0,35 h⁻¹ (bedarfsgeführt); Betrieb 24 h/d, alle Tage. Infiltration n_inf = 0,1 h⁻¹ (Anlage, dichte
Hülle) → Summe 0,5 h⁻¹ konsistent mit Teil 10. Abluftanlage ohne WRG: Senke wie freie Lüftung.

**Ventilator-Hilfsenergie (9.3, Gl. 60/61):**
`W_fan = 0,001·(1 + f_Zuschläge)·SPI·n_mech·V·t_rv,mech` [kWh/Monat], t = 24·d_mth.
**Tab. 19 SPI [W/(m³/h)]** (AC / DC-EC): Abluft zentral 0,20/0,10 · Zu-/Abluft zentral mit WÜT
0,55/0,35 · Zu-/Abluft dezentral 0,35/0,20 · Zu-/Abluft zentral mit Abluft-WP 0,65/0,45.
Frostschutz-/EWÜT-Zuschläge f = 0 im Standardfall (ohne E-WÜT/S-KOL).

## 10. Status Stufe 2 – umgesetzt & verifiziert ✅

- **Rechenkern:** `dashboard/services/din18599_anlage.py` (`calculate_system_din`) –
  monatliche Prozesskette Heizung (Teil 5) + TWW (Teil 8) + Lüftung (Teil 6) mit den oben
  dokumentierten Standardwerten. `views.calculate_system` (`/calculate-system/`) ist dünner Wrapper.
- **Lüftungskopplung:** Das Frontend sendet die Hüllendaten (`envelope`) mit. Bei mechanischer
  Lüftung wird die Teil-2-Bilanz mit **n_zone = n_inf = 0,1 h⁻¹** neu gerechnet; der maschinell
  geförderte Anteil `n_rlt = n_eff − n_inf` (mit `n_eff = n_inf + n_mech·(1 − η_WRG)`, Teil 6
  Gl. 14/15) wird **separat als RLT-Luftaufbereitung** über denselben Erzeuger bilanziert
  (Zuschläge: Kanäle außerhalb der Hülle ×1,10, Auslässe an der Außenwand ×1,03 – Näherungswerte,
  keine Teil-6-Tabellenwerte). Abweichung zum reinen n_eff-Ansatz: der RLT-Anteil nimmt nicht an
  der η(γ)-Gewinnverrechnung teil und kennt keine Heizgrenze (fällt in allen Monaten mit
  θ_e < θ_i an) → in Übergangsmonaten leicht konservativ. WRG senkt den Heizwärmebedarf korrekt
  (Referenz-EFH: ~−3 900 kWh/a bei η = 0,8). Die frühere **Gradstunden-Doppelzählung der
  Lüftungsverluste wurde entfernt.**
- **Frontend:** `calculateSystem()` sendet envelope + Lüftungssystem (Mapping auf Teil-6-Schlüssel),
  AC/DC, η_WRG, Wärmeübergabe-Auswahl (neu, ersetzt das η-Eingabefeld); Warmwasser/Hilfsstrom-Felder
  sind jetzt berechnete (readonly) Anzeigen und versorgen den Energiebilanz-Tab.
- **Verifikation** (`scripts/verify_din18599_anlage.py`, Referenz-EFH 150 m², handgeprüft):
  - Q_w,b = max(16,5−7,5; 8,5)·150·0,98 = **1 323 kWh/a** ✓; Speicher 139 l → Q_s,P0 = 1,69 kWh/d ✓
  - Gas-Brennwert: Endenergie 105 kWh/(m²a) (norm-konservative Verteilverluste, s. u.)
  - Pellet: PE 27 kWh/(m²a) · Fernwärme: PE 76 · WP (COP 3,5, FBH): **JAZ 4,14**, PE 43
  - Kessel-Hilfsenergie 313 kWh/a, Heizungspumpe 50, Ventilator (WRG, DC) 478 kWh/a ✓ (SPI 0,35)
- **Hinweis Verteilverluste:** Die Norm-Standardlängen (Tab. 26: L_V = 30 + 2,3·A^0,79) sind bewusst
  konservativ (BBSR-Endbericht delta-q bestätigt Überschätzung ggü. realen Netzen). Bei detaillierter
  Rohrnetzplanung Längen direkt eingeben (künftiges Feature) oder `heating_distribution_inside`
  setzen (Leitungen in der Hülle → Verluste großteils rückgewinnbar).
- **Energieträger-Faktoren:** Endenergie Brennstoffe Hi-bezogen (Kette intern Hs, Umrechnung f_Hs/Hi);
  f_P nach GEG 2024 (Strom 1,8), CO₂ nach GEG Anlage 9 (Strom 0,56 kg/kWh – ersetzt die alten 0,40).
- **Offen für später:** Solarthermie (Teil 8 6.4.3), WP-BIN-Verfahren (Teil 5 Anhang B/C),
  reale Rohrlängen-Eingabe, Kühlung (Teil 3). Nachtabsenkung (§13) und Beleuchtung (Teil 4,
  §13) sind umgesetzt.

## 14. Norm-Review Juli 2026: korrigierte Fehler ✅

Ein systematischer Review (Code vs. eigene Norm-Extraktion) fand und behob vier Fehler:

1. **Solare Gewinne ~10 % zu niedrig** (`din18599.py`): Es wurden vier Abminderungsfaktoren
   multipliziert (F_F·F_S·F_W·F_V = 0,7·0,9·0,9·**0,9**), obwohl Teil 10 Tab. 4 für Wohnen
   Verschmutzung **F_V = 1** setzt (§4b oben). F_SOILING = 1,0 korrigiert → Q_h,b sinkt
   (Referenz-EFH: 69,7 → 67,8 kWh/(m²a); Solargewinne +11 %).
2. **Fernwärme-Primärenergiefaktor 0,7 → 0,6** (`din18599_anlage.py`, `constants.py`):
   0,7 war der EnEV-/DIN-18599-1-Wert; GEG 2024 Anlage 4 nennt für Fernwärme aus KWK
   (fossil) **0,6** – konsistent zum verwendeten CO₂-Faktor 0,18 (Anlage 9).
3. **Fenster in F_x=0-Wänden** (`din18599.py`): Fenster in Wänden an beheizte Nachbarräume
   (Einzelraum-Fall) erhielten volle Solargewinne, obwohl sie transmissionsseitig korrekt
   aus der Hülle fielen → solare Gewinne jetzt nur für Orientierungen mit F_x > 0.
4. **Zirkulations-Laufzeit z** (`din18599_anlage.py`): Der MFH-Mindestwert z ≥ 16 h (Gl. 18)
   galt nur für die Pumpen-Hilfsenergie, nicht für die Verlust-Betriebszeit → jetzt ein
   gemeinsames `z_circ` für beide.

Zusätzlich Doku/Code-Widersprüche bereinigt: Lüftungskopplung (§10), WP-TWW-COP (§8.6),
Nachtabsenkung/Klimaregionen (Status §6/§13). Bekannte, bewusst offene Abweichungen:
BGF als Bezugsfläche statt NGF (Eingabefeld heißt BGF; alle flächenbezogenen Teil-10-Werte
sind NGF-bezogen – bei BGF-Eingabe werden interne Gewinne/TWW/Kennwerte um ~10–20 %
verschoben), PV-Eigenverbrauch als pauschale Jahresquote, Beleuchtung ohne k_WF/k_R und
ohne Wärmequellen-Rückkopplung.
