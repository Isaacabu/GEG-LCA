# Analyse: Einheiten & Kennwerte der GEG-LCA-Website

**Auftrag:** Prüfung *aller Einheiten* auf der Website nach **Korrektheit** (physikalische
Einheiten) sowie **Relevanz / Bedeutung / Wichtigkeit** (angezeigte Kennwerte).
**Referenzmaßstab:** ZUB Helena bzw. der amtliche GEG-Energieausweis nach DIN V 18599.
**Umfang:** `dashboard/templates/dashboard/index.html`, alle 7 Tabs.
**Status:** Umgesetzt am 05.07.2026 (siehe Abschnitt 6 „Umsetzungsstand"). Offen ist nur noch der
Referenzgebäude-Vergleich (B-Gap-2).

---

## 0. Kurzfassung (Executive Summary)

Die inhaltliche Kennwert-Auswahl der Website ist fachlich **überwiegend gut** und deckt die
wichtigsten DIN-V-18599-/GEG-Größen ab. Es gibt zwei Baustellen:

1. **Einheiten-Schreibweise ist uneinheitlich (Hauptbefund).** Dieselbe physikalische Größe
   wird an verschiedenen Stellen unterschiedlich geschrieben — teils sogar *im selben Panel*.
   Beispiel: sichtbarer HTML-Text `kWh/(m²·a)` (Zeile 3185), aber der direkt daneben per
   JavaScript eingesetzte Wert trägt das Suffix `kWh/m²a` (Zeile 7636/7984). Insgesamt
   koexistieren **vier** Schreibweisen für den spezifischen Energiebedarf und **zwei** für den
   U-Wert. Das ist der größte, leicht behebbare Qualitätsmangel.

2. **Zwei GEG-Pflicht-/Kernkennwerte fehlen**, die ZUB Helena zwingend ausweist:
   der **spezifische Transmissionswärmeverlust H_T′** (in W/(m²·K)) und der **Vergleich
   Ist-Wert ↔ Anforderungswert (Referenzgebäude)**. Aktuell zeigt die Seite nur H_T als
   Absolutwert (W/K) und keine GEG-Anforderungsgrenze.

Priorisierte Empfehlungen stehen in **Abschnitt 4**, offene Entscheidungen in **Abschnitt 5**.

---

## 1. Methodik & Referenzmaßstab

**Was ZUB Helena / der GEG-Energieausweis als Bezug liefert.** ZUB Helena rechnet mit dem
18599-Kern des Fraunhofer IBP und erstellt sämtliche GEG-Nachweise (Wohn- und
Nichtwohngebäude). Der amtliche Energieausweis weist verpflichtend aus:

| GEG-Kennwert | Einheit (amtliche Notation) |
|---|---|
| Jahres-Primärenergiebedarf Q_p″ | kWh/(m²·a) |
| Endenergiebedarf | kWh/(m²·a) |
| Spez. Transmissionswärmeverlust H_T′ | W/(m²·K) |
| CO₂-Emissionen | kg/(m²·a) |
| Energieeffizienzklasse | A+ … H |
| **Anforderungswert (Referenzgebäude)** neben jedem Ist-Wert | — |

**Notationsstandard (DIN / SI).** Fachlich korrekt ist die Klammer-plus-Mittelpunkt-Form:

| Größe | Soll-Schreibweise |
|---|---|
| Wärmedurchgangskoeffizient U, ΔU_WB | **W/(m²·K)** |
| Wärmeleitfähigkeit λ | **W/(m·K)** |
| Längenbez. Wärmebrücke ψ | **W/(m·K)** |
| Wärmedurchlasswiderstand R, R_si/R_se | **m²·K/W** |
| Flächenbez. Wärmekapazität c | **Wh/(m²·K)** |
| Spez. Energiebedarf | **kWh/(m²·a)** |
| Spez. CO₂-Emission | **kg/(m²·a)** |
| Spez. PV-Ertrag | **kWh/(kWp·a)** |
| Luftwechselrate n₅₀ | **h⁻¹** |

> Hinweis: Reine Kosmetik? Nein — für einen GEG-Nachweis ist die **einheitliche, normkonforme**
> Darstellung ein Qualitäts- und Glaubwürdigkeitsmerkmal. Profi-Tools wie ZUB Helena sind hier
> pedantisch konsistent.

---

## 2. Teil A — Physikalische Einheiten (Korrektheit & Konsistenz)

Alle Einheiten sind **physikalisch korrekt** (richtige Einheit für die jeweilige Größe, keine
Dimensionsfehler). Hochzahlen sind durchgängig als Unicode `²`/`³` gesetzt (kein `^2`/`m2`).
Das Problem ist ausschließlich die **uneinheitliche Schreibweise**. Befunde nach Schwere:

### 🔴 A1 — Spezifischer Energiebedarf: 4 Varianten (höchste Priorität)
Für ein und dieselbe Größe koexistieren:

| Variante | Vorkommen (Zeilen) |
|---|---|
| `kWh/(m²·a)` (Soll) | 3164, 3185, Kommentar 7846 |
| `kWh/m²a` | JS 7636, 7796, 7941, 7984, 8872, 9131 ← **die tatsächlich gerenderten Werte** |
| `kWh/m²·a` | Kommentar 8803 |
| `kWh/(m²a)` | Skalierungstabelle 4066 |

**Kritisch:** Im Energiebilanz-Panel steht der sichtbare Einheiten-Span als `kWh/(m²·a)`
(3185), aber die per JS daneben gesetzten Werte (Heizwärmebedarf, q_p) als `kWh/m²a`
(7636/7984). Der Nutzer sieht **zwei Schreibweisen derselben Einheit nebeneinander**.

### 🔴 A2 — U-Wert / ΔU_WB: `W/m²K` vs `W/(m²·K)`
- Dominant: `W/m²K` (ohne Klammern/Mittelpunkt) — u. a. 1977–1986, 2341, 2411, 2546, 3477,
  5384, 5436, 5469, 11579–11582, 12651, 12698.
- Abweichend: `W/(m²·K)` — 2365 (ψ Fenster gesamt), 4394 (Wärmebrücken-Panel).
- → ΔU_WB steht in *daten/din4108* als `W/m²K`, im *Fenster-Panel* als `W/(m²·K)`.

### 🟠 A3 — CO₂-/GWP-Einheiten uneinheitlich (3 Schreibweisen für dieselbe Größe)
- Graue Emissionen: `kg CO₂e/m²` (JS 5531, 6133, 6176) vs. Spaltenheader `CO₂ kg/m²`
  (2173, 2523, 2614) vs. Tooltip `kg/m²` (5538, 6138, 6178).
- Betriebs-CO₂: `kg CO₂/a` (PV, 2897) vs. `kg/a` (Bilanz, JS 8866/9145) — mal mit, mal ohne „CO₂".
- „CO₂-Äquivalent" ausgeschrieben (3766) vs. „CO₂e" (4032, 11830) vs. bloß „CO₂" (2897).

### 🟠 A4 — Spez. PV-Ertrag: `kWh / kWp·a` vs `kWh/kWp·a`
- Nur die PV-Hero-Kachel (2896) hat Leerzeichen um den Schrägstrich; überall sonst
  `kWh/kWp·a` (3004, 3104, JS 8201/8253/8266/…). Soll normkonform: **kWh/(kWp·a)**.

### 🟡 A5 — Klammer-Stil je Tab uneinheitlich
- `din4108`-Tab: eckige Klammern `[m²K/W]`, `[W/m²K]`, `[kg/m²]`, `[m]`, `[°C]`, `[h⁻¹]`,
  `[m³]` (3477, 3504, 3508, 3535, 3570–3572).
- `huelle`/`daten`: runde Klammern `(m²)`, `(W/m²K)`, `(°C)`, `(W/K)`.
- → Eckig vs. rund ist rein stilistisch, sollte aber vereinheitlicht werden.

### 🟡 A6 — λ und ψ ohne Klammern; ψ = λ-Schreibweise trotz anderer Größe
- λ durchgängig `W/mK` (statt `W/(m·K)`) — in sich konsistent, aber inkonsistent zur
  U-Wert-Klammerung.
- ψ (linearer Wärmebrückenkoeffizient) wird **ebenfalls** als `W/mK` gelabelt (2375–2377,
  4406) — gleiche Schreibweise wie λ, obwohl andere physikalische Größe. Soll: `W/(m·K)`.

### 🟡 A7 — Kleinere Stilbrüche
- Spaltenheader in „Einheit-vor-Symbol"-Stil (`CO₂ kg/m²`, `λ W/mK`, `R m²K/W`, 2171–2173)
  weichen vom übrigen „Wert + Einheit"-Stil ab.
- Luftwechsel: `h⁻¹` (Superscript, 3570) vs. `m³/(h·m²)` (Schrägstrich, 12729) — zwei
  Notationsstile für „pro Stunde" (beide korrekt).
- Flächenbez. Wärmekapazität `Wh/m²K` (3502) — analog A2 ohne Klammern.

---

## 3. Teil B — Kennwerte (Relevanz / Bedeutung / Wichtigkeit)

Bewertung jedes angezeigten Kennwerts gegen den GEG-/ZUB-Helena-Maßstab.
Legende: **🟢 essenziell** (Pflicht/Kern) · **🔵 nützlich** · **⚪ optional/Detail** ·
**❌ fehlend (relevant)**.

### Tab 1 — 🏢 Gebäudedaten
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| Gebäudevolumen / BGF / Hüllfläche A | m³ / m² | 🟢 | Bezugsgrößen für alle spez. Kennwerte — korrekt. |
| Raum-Soll-Temperatur | °C | 🟢 | Randbedingung 18599. |
| Wärmebrückenzuschlag ΔU_WB | W/(m²·K) | 🟢 | Fließt in H_T; gut, dass wählbar. |
| Interne Gewinne (gesamt / je Person) | W | 🔵 | Sinnvolle Transparenz. |
| Personendichte | m²/Person | ⚪ | Detail, ok. |

### Tab 2 — 🏠 Gebäudehülle
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| U-Werte Wand/Dach/Boden/Fenster/Tür | W/(m²·K) | 🟢 | Kern der Hüllbilanz. |
| H_T-Aufteilung (Wand/Fenster/Dach/Boden/WB) | W/K | 🟢 | Sehr gute Transparenz der Verlustpfade. |
| **H_T′ (spez. Transmissionsverlust)** | **W/(m²·K)** | ❌ | **Fehlt.** GEG-Pflichtkennwert für Wohngebäude (Höchstwert je Gebäudetyp). Nur H_T gesamt vorhanden. → siehe B-Gap-1. |
| Wand-/Dach-/Boden-GWP (A1–A3) | kg CO₂e/m² | 🔵 | Guter Brückenschlag zur LCA; über GEG hinaus. |
| Solargewinn / Heizwärmebedarf (spez.) | kWh/a · kWh/(m²·a) | 🟢 | Kernergebnis. |
| R_si/R_se Oberflächenübergang | m²·K/W | ⚪ | Detail, korrekt. |

### Tab 3 — ⚙️ Anlagentechnik
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| Endenergie / Primärenergie (Anlage) | kWh/a | 🟢 | Kern Stufe 2 (Teil 5/8/6). |
| Spez. CO₂ | kg/(m²·a) | 🟢 | GEG-relevant. |
| COP A2/W35 | – | 🔵 | Sinnvolle WP-Eingabe. |
| Beleuchtungs-Endenergie (nur NWG) | kWh/(m²·a) | 🔵 | Korrekt auf NWG begrenzt (Teil 4). |

### Tab 4 — ☀️ Photovoltaik
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| Installierte Leistung | kWp | 🟢 | |
| Jahresertrag / Eigenverbrauch / Einspeisung | kWh/a | 🟢 | |
| Spez. Ertrag | kWh/(kWp·a) | 🔵 | Guter Vergleichskennwert. |
| CO₂ gespart / finanzieller Nutzen | kg CO₂/a · €/a | ⚪ | Nette Ergänzung, nicht GEG-normativ. |

### Tab 5 — 🟢 Energiebilanz
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| Endenergiebedarf je m² | kWh/(m²·a) | 🟢 | Energieausweis-Kernwert. |
| Primärenergie Q_p (+ q_p spez.) | kWh/a · kWh/(m²·a) | 🟢 | Energieausweis-Kernwert. |
| Energieeffizienzklasse | A+…H | 🟢 | Nach GEG Anlage 10 — sehr gut. |
| CO₂ (gesamt / je m²) | kg/a · kg/(m²·a) | 🟢 | |
| **Anforderungswert / Referenzgebäude** | — | ❌ | **Fehlt.** ZUB Helena stellt jedem Ist-Wert den zulässigen Höchstwert gegenüber (Q_p″, H_T′). Ohne diesen Vergleich fehlt die „bestanden/nicht bestanden"-Aussage. → B-Gap-2. |
| Kostenbilanz (€/a) | €/a | ⚪ | Wirtschaftlichkeit — über GEG hinaus, ok. |

### Tab 6 — 📋 DIN 4108
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| Mindestwärmeschutz R/U/m′ | m²·K/W · W/(m²·K) · kg/m² | 🟢 | Teil 2 Tab. 3 — korrekt. |
| Sonneneintragskennwert (Sommer) | – | 🟢 | Teil 2 §8.4. |
| Tauwasser M_c / M_ev, s_d, θ_si | kg/m² · m · °C | 🟢 | Glaser — fachlich stark. |
| Luftdichtheit n₅₀ / q_E50 | h⁻¹ · m³/(h·m²) | 🟢 | Teil 7. |
| ΔU_WB (Beiblatt 2) | W/(m²·K) | 🟢 | Speist Hülle-Tab — gute Verzahnung. |

### Tab 7 — 🌍 Ökobilanz (LCA)
| Kennwert | Einheit | Relevanz | Bemerkung |
|---|---|---|---|
| Funktionelle Einheit | 1 m² BGF · a | 🟢 | Korrekt deklariert. |
| Spez. graue Emissionen | kg CO₂e/(m²·a) + kg CO₂e/m² gesamt | 🟢 | Kern der LCA. |
| GWP (A1–A3) je Bauteil | kg CO₂e | 🟢 | ÖKOBAUDAT-basiert. |
| Weitere Wirkungskategorien (AP/EP/PE) | – | ⚪ | Bewusst nicht ausgewertet (dokumentiert, 3766) — ok als Scope-Grenze. |

---

## 4. Priorisierte Empfehlungen

### P1 — Einheiten-Schreibweise projektweit vereinheitlichen (größter Nutzen, geringes Risiko)
- Eine **Soll-Notation** festlegen (Tabelle in Abschnitt 1) und durchziehen.
- Zuerst **A1** (spez. Energiebedarf, 4 Varianten) und **A2** (U-Wert) — das sind die
  sichtbarsten. Idealerweise die Einheiten-Strings an *einer* Stelle zentralisieren, damit
  HTML-Span und JS-Suffix nicht mehr auseinanderlaufen (Ursache von A1).
- Danach **A3** (CO₂/GWP) und **A4** (PV-Ertrag).

### P2 — Fehlende GEG-Kernkennwerte ergänzen
- **B-Gap-1: H_T′** = H_T / A (Hüllfläche liegt bereits vor) in W/(m²·K) — kleiner Rechen-/
  Anzeigeaufwand, hoher fachlicher Gewinn.
- **B-Gap-2: Anforderungswert-Vergleich** (Ist ↔ zulässiger Höchstwert für Q_p″ / H_T′).
  Größer, weil das Referenzgebäude-Verfahren dahintersteht — als eigenes Arbeitspaket bewerten.

### P3 — Kosmetik / Konsistenz
- **A5** (eckige vs. runde Klammern je Tab), **A6** (λ/ψ-Klammerung), **A7** (Header-Stil).
- Rein optische Angleichung, kann gebündelt am Ende laufen.

---

## 5. Offene Entscheidungen für euch / den Projektleiter

1. **Soll-Notation:** normkonform mit Mittelpunkt & Klammern `W/(m²·K)`, `kWh/(m²·a)`
   (Empfehlung, wie ZUB Helena) — oder die schlankere Form `W/m²K` überall? *Eine* Regel.
2. **Klammern:** runde `( )` oder eckige `[ ]` als projektweiter Standard?
3. **H_T′ ergänzen?** (klein, empfohlen)
4. **Anforderungswert/Referenzgebäude:** aufnehmen (eigenes AP) oder bewusst außerhalb des
   Projektscopes lassen?
5. Nach eurer Entscheidung setze ich die freigegebenen Punkte direkt im Code um.

---

## 6. Umsetzungsstand (05.07.2026)

Beschlossene Soll-Notation: **normkonform mit Mittelpunkt + Klammern**; Einheiten in Labels/
Tabellenköpfen in **eckigen Klammern** `[…]` (Variante 3). Umgesetzt in
`dashboard/templates/dashboard/index.html` und `dashboard_home.html`:

| Befund | Änderung | Status |
|---|---|---|
| A1 spez. Energiebedarf | alle 4 Varianten → `kWh/(m²·a)` (inkl. Landing-Page) | ✅ |
| A2 U-Wert / ΔU_WB | `W/m²K` → `W/(m²·K)`; Labels `[W/(m²·K)]` | ✅ |
| A3 CO₂/GWP | `CO₂ kg/m²`→`kg CO₂e/m²` · `kg/a`→`kg CO₂/a` · `kg/m²a`→`kg/(m²·a)` · Faktoren `kg CO₂/kWh` | ✅ |
| A4 PV-Ertrag | → `kWh/(kWp·a)` | ✅ |
| A6 λ/ψ | `W/mK` → `W/(m·K)`; Labels `[W/(m·K)]`; R: `m²K/W` → `m²·K/W` | ✅ |
| A7 Spaltenköpfe | `λ [W/(m·K)]`, `R [m²·K/W]`, GWP-Header `kg CO₂e/m²` | ✅ |
| A5 Klammern | Einheiten-Labels vereinheitlicht auf `[…]` (DIN-4108-Stil als Standard übernommen) | ✅ |
| Sonstiges | `Wh/m²K` → `Wh/(m²·K)` (Speichermasse) | ✅ |
| **B-Gap-1 H_T′** | Neue Zeile „H_T′ spezifisch" in der H_T-Tabelle (Hülle-Tab), berechnet in `syncHtTable()` als H_T ÷ Hüllfläche A, Anzeige in `W/(m²·K)` inkl. GEG-Tooltip | ✅ |
| **B-Gap-2 Referenzgebäude** | Ist ↔ Anforderungswert-Vergleich (Q_p″, H_T′-Höchstwerte) | ⬜ offen (eigenes Arbeitspaket) |
| Uppercase-Bug Spaltenköpfe | CSS `text-transform:uppercase` machte aus Einheiten „KG CO₂E/M²" (m≠M, k≠K!) — Einheiten-Spalten ausgenommen | ✅ |
| **Normativer Befund CO₂e** | GEG Anlage 9 rechnet in CO₂-**Äquivalenten** (amtl. Energieausweis: „kg CO₂-Äquivalent/(m²·a)"). Betriebs-CO₂ daher von `kg CO₂/a`, `kg/(m²·a)`, `kg CO₂/kWh` auf **`kg CO₂e/…`** umgestellt — konsistent mit dem LCA-Tab. | ✅ |

Verifiziert am ausgelieferten HTML (`/projekt/`): 0 Alt-Schreibweisen, H_T′-Zeile vorhanden.

---

*Quellen (Referenzmaßstab):*
- [ZUB Helena — Produktseite, ZUB-Systems](https://www.zub-systems.de/en/produkte/helena)
- [ZUB Helena Ultra, ZUB-Systems](https://www.zub-systems.de/en/produkte/helena/ultra)
- [Informationen zum GEG 2024 und zur Umsetzung in ZUB Helena](https://www.zub-systems.de/de/news/informationen-zum-geg-2024-und-zur-umsetzung-zub-helena)
- Codebasis: `dashboard/templates/dashboard/index.html` (Zeilenangaben im Dokument).
