# DIN 4108 – Umsetzungs-Spezifikation

Stand: vier Nachweise umgesetzt und gegen die Normtexte verifiziert.
Ziel: Die Energiebilanz nach DIN V 18599 (siehe `DIN18599_Umsetzung.md`) wird um die
**bauphysikalischen Nachweise der DIN 4108** ergänzt – Mindestwärmeschutz, sommerlicher
Wärmeschutz, Tauwasserschutz und Wärmebrücken/Luftdichtheit.

- **Rechenkern:** `dashboard/services/din4108.py`
- **Endpunkte:** `dashboard/views.py` (`/calculate-mindestwaermeschutz/`,
  `/calculate-sommerlicher-waermeschutz/`, `/calculate-tauwasser/`, `/calculate-luftdichtheit/`,
  `/din4108-materialien/`) → `dashboard/urls.py`
- **Frontend:** Tab „📋 DIN 4108" in `templates/dashboard/index.html` (vier Unterbereiche)
- **Verifikation:** `scripts/verify_din4108.py` (24 Plausibilitäts-/Referenzprüfungen, alle grün)
- **Norm-Extraktion (reproduzierbar):** `scripts/din4108_extract.py <teil> <von> <bis>`
  legt den Text einer PDF-Seitenspanne unter `scripts/_din4108_text/` ab. Die PDFs liegen
  lokal unter `DIN_4108/` (urheberrechtlich, nicht committen).

---

## Feature 1 – Mindestwärmeschutz von Bauteilen (DIN 4108-2:2026-05, §5)

Prüft je Bauteil, ob der Wärmedurchlasswiderstand R den Mindestwert **Tabelle 3** erreicht
(Schutz vor Tauwasser/Schimmel an der Innenoberfläche). Eingabe R direkt oder U-Wert
(R = 1/U − R_si − R_se, R_si = 0,13, R_se = 0,04).

**Tabelle 3 – Mindestwerte R_min [m²·K/W]** (verifiziert, S. 16–17):

| Bauteil | R_min |
|---|---|
| Wand, beheizter Raum | 1,20 |
| Wand, niedrig beheizter Raum | 0,55 |
| Dachschräge gegen Außenluft | 1,20 |
| Decke n. oben / Flachdach gegen Außenluft | 1,20 |
| Decke zu belüftetem Raum (Dachschräge/Abseite) | 0,90 |
| Decke zu nicht beheiztem / bekriechbarem Raum | 0,90 |
| Decke zw. gedämmten Dachschrägen/Abseiten | 0,35 |
| Decke n. unten gegen Außenluft/Tiefgarage/Durchfahrt | 1,75 |
| Decke gegen nicht beheizten Kellerraum | 0,90 |
| Sohlplatte ans Erdreich (bis 5 m Raumtiefe) | 0,90 |
| Boden über nicht belüftetem Hohlraum ans Erdreich | 0,90 |
| Wohnungs-/Gebäudetrennwand, Treppenraum-Trennwand | 0,07 |
| Wohnungstrenndecke / versch. Nutzung | 0,35 |

Sonderfälle (§5.1.1/5.1.2): m′ < 100 kg/m² → R ≥ **1,75**; opake Ausfachung transparenter
Bauteile → R ≥ **1,2** (U_p ≤ 0,73); thermisch inhomogen (Holzständer) → Gefach R_G ≥ 1,75
**und** Bauteil R_c,op ≥ 1,0.

Funktion: `pruefe_mindestwaermeschutz(data)` → je Bauteil `{r_bauteil, r_min, erfuellt, color}`.

## Feature 2 – Sommerlicher Wärmeschutz (DIN 4108-2:2026-05, §8.4)

Sonneneintragskennwert-Verfahren: Nachweis erfüllt, wenn **S_vorh ≤ S_zul**.

```
S_vorh = Σ_j (A_w,j · g_tot,j) / A_G        (Gl. 2)
g_tot = g · F_C (· F_S)                      (Gl. 3)
S_zul = S1 + S2 + S3 + S4 + S5 + S6          (Gl. 4 / Tab. 8)
```

- **S1** Grundwert aus **Tabelle 8** je Klimaregion (A/B/C, neu in 2026 – Bild 1),
  Nutzung (Wohn/Nichtwohn), Bauart (leicht/mittel/schwer) und Nachtlüftung
  (ohne / erhöht n≥2 / hoch n≥5). Vollständige Matrix in `S1_TABELLE` hinterlegt.
- **S2** = a − b·f_wg (Fensterflächenanteil-Korrektur): Wohn a=0,060 b=0,231; NWG a=0,030 b=0,115.
- **S3** = 0,03·(A_w,g≤0,40 / A_w) bei Sonnenschutzglas.
- **S4** = −0,035·f_neig (Fenster 0°–60° gegen Horizontale).
- **S5** = 0,10·f_nord (Nord/NO/NW mit Neigung > 60° oder dauerverschattet).
- **S6** = passive Kühlung: leicht 0,02 / mittel 0,04 / schwer 0,06.

Bauart-Einstufung (Tab. 8 Fußnote b): leicht C_wirk/A_G < 50, mittel 50–130, schwer > 130 Wh/(K·m²).
F_C-Anhaltswerte (Tab. 10/11/13, Kategorie „allgemein") in `FC_ANHALT`: außen ≈ 0,24–0,25,
Scheibenzwischenraum ≈ 0,31–0,35, innen ≈ 0,90–0,95. **Verzicht auf Nachweis** (Tab. 7):
f_wg ≤ 7 % (Neigung 0–60°) bzw. 10 % (NW–Süd–NO senkrecht) / 15 % (sonst Nord senkrecht).

Funktion: `berechne_sommerlicher_waermeschutz(data)` → `{s_vorh, s_zul, anteile{S1..S6}, erfuellt, verzicht_moeglich}`.

## Feature 3 – Tauwasser / Periodenbilanz-(Glaser-)Verfahren (DIN 4108-3:2024-03, Anhang A)

Eindimensionale Diffusionsbilanz über den Schichtaufbau (innen→außen).

**Klimarandbedingungen (Tabelle A.3):** R_si = 0,25, R_se = 0,04;
Tauperiode innen 20 °C/50 % → p_i = 1168 Pa, außen −5 °C/80 % → p_e = 321 Pa, t_c = 2160 h;
Verdunstungsperiode p_i = p_e = 1200 Pa, Sättigung im Tauwasserbereich p_sat = 1700 Pa
(Wand/Decke/helles Dach) bzw. 2000 Pa (unverschattetes dunkles Dach), t_ev = 2160 h.

**Formeln (Anhang C):** s_d = μ·d (Gl. C.5); g = δ₀·Δp/s_d mit δ₀ = 2·10⁻¹⁰ kg/(m·s·Pa) (C.10);
Temperaturverteilung θ_k = θ_i − q·(R_si + ΣR) (C.2–C.4); Sättigungsdampfdruck (C.15/C.16):
`p_sat = 610,5·exp(17,269·θ/(237,3+θ))` für θ≥0, `…21,875·θ/(265,5+θ)` für θ<0
(gegen Tabelle C.1 verifiziert: p_sat(20)=2337, p_sat(−5)=401, p_sat(0)=611).

**Lokalisierung der Tauebenen:** Die tatsächliche Dampfdruck­gerade im s_d-Diagramm wird als
**untere konvexe Hülle** der Stützpunkte {(0, p_i), (s_d,k, p_sat,k), (s_d,T, p_e)} bestimmt
(`_lower_convex_hull`, Andrew's monotone chain). Knickpunkte der Hülle = Kondensationsebenen –
das deckt die vier Norm-Fälle a–d (kein/eine/zwei Ebenen/ein Bereich) einheitlich ab.
Tauwassermasse je Ebene M_c = (g_in − g_out)·t_c; Verdunstung M_ev über Abgabe zu beiden
Oberflächen (p_sat,Verd, Gl. A.12–A.15).

**Bewertung (§5.2.2):** zulässig, wenn kein Tauwasser **oder** M_c ≤ M_ev **und** M_c ≤ 1,0 kg/m².

λ/μ-Bemessungswerte: **DIN 4108-4:2020-11, Tab. 1 + 2** (`MATERIAL_DB`, je Stoff trockener und
feuchter μ-Wert; im Glaser ist der für die Schichtposition ungünstigere zu verwenden, Anhang A.2.3).
Verifiziert: diffusionsoffene WDVS-Wand → tauwasserfrei; Innendämmung + Bitumensperre außen → Tauwasser erkannt.

Funktion: `berechne_tauwasser_glaser(data)` → `{u_wert, profil[], tauebenen[], mc_total, mev_total, erfuellt}`.

## Feature 4 – Wärmebrücken (Beiblatt 2) + Luftdichtheit (DIN 4108-7)

**Wärmebrückenzuschlag ΔU_WB** (DIN 4108 Bbl 2:2019-06, §5.2 – Wert nach DIN V 18599-2):
kein Nachweis 0,10 · Innendämmung+Massivdecke 0,15 · Anschlüsse n. Bbl 2 **Kategorie A 0,05** ·
**Kategorie B 0,03**. Der gewählte Wert wird per „In Heizbedarf übernehmen" in das Feld
`delta_u_wb` des Hülle-Tabs geschrieben und fließt damit direkt in die DIN-V-18599-Heizbilanz ein
(schließt den in `DIN18599_Umsetzung.md` §6 vorgemerkten „späteren UI-Schalter").
Vernachlässigungskriterien §5.5 dokumentiert (z. B. durchlaufende Dämmschicht R ≥ 2,5 m²K/W).

**Luftdichtheit n50** (DIN 4108-7:2026-04, §5; deckungsgleich GEG 2024): Grenzwert
n50 ≤ **3,0 h⁻¹** ohne, **1,5 h⁻¹** mit RLT-Anlage (Empfehlung ≤ 1,0); q_E50 ≤ 4,5 / 2,0
m³/(h·m²) bei V > 1500 m³. Zusätzlich informativer Infiltrations-Luftwechsel
n_inf ≈ n50·e (e ≈ 0,07, windschwach/einseitig).

Funktionen: `waermebruecken_zuschlag(option)`, `pruefe_luftdichtheit(data)`.

---

## Bewusst dokumentierte Vereinfachungen

- **Sommer:** nur das vereinfachte Sonneneintragskennwert-Verfahren (§8.4), nicht die
  thermische Gebäudesimulation (§8.5). F_C als Anhaltswert „allgemein" je Verglasung
  (Tab. 10/11/13 enthalten zusätzlich Klassen nach Lichttransmission/Reflexion).
- **Tauwasser:** Periodenbilanz-(Glaser-)Verfahren mit Blockklima (kein Monatsbilanzverfahren
  nach DIN EN ISO 13788 / kein hygrothermisches Modell nach Anhang D). μ als Einzel-
  Bemessungswert je Schicht (Default = feuchter Wert); ruhende Luftschichten s_d = 0,01 m.
- **Mindestwärmeschutz:** Tabellenverfahren (Tab. 3); der alternative Nachweis über
  θ_si,min = 17 °C bzw. der detaillierte Wärmebrücken-f_Rsi-Nachweis (§6) ist nicht implementiert.
- **Luftdichtheit:** Grenzwertabgleich + Infiltrationsschätzung; keine Kopplung des n_inf
  in die 18599-Lüftungsbilanz (diese nutzt ihren eigenen Luftwechsel-Ansatz).
