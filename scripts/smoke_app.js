// Playwright-Smoke-Test für die GESAMTE App (alle Tabs).
// Voraussetzung: Dev-Server läuft (python manage.py runserver 8000).
// Aufruf: node scripts/smoke_app.js
//
// Klickt jeden Tab durch, löst die Berechnungen in Abhängigkeitsreihenfolge aus
// (Hülle → Anlage → PV → Bilanz → DIN 4108), prüft, dass je ein Ergebnis erscheint,
// sammelt JS-Konsolen-/Netzwerkfehler und legt Screenshots unter scripts/_smoke/ ab.
//
// Die „…auswerten"-Buttons wurden durch das Live-Update (markStale/scheduleAuto)
// ersetzt – der Test stößt die Pipeline deshalb über den zentralen Orchestrator
// window.recompute(stufe) an (derselbe Hook wie der Bilanz-Button) und prüft
// zusätzlich, dass ein Heizsystem-Wechsel per Karte automatisch neu rechnet.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.BASE_URL || "http://localhost:8000/projekt/";
const OUT = path.join(__dirname, "_smoke");
fs.mkdirSync(OUT, { recursive: true });

// Bekannte, zu tolerierende Fremdfehler (derzeit leer). Bei künftigen unvermeidbaren
// Drittfehlern hier eintragen; sonst meldet der Test sie.
const KNOWN = [];
const isKnown = (s) => KNOWN.some((k) => s.includes(k));

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 1500 } });
    const errors = [];
    page.on("console", (m) => { if (m.type() === "error" && !isKnown(m.text())) errors.push("console: " + m.text()); });
    page.on("pageerror", (e) => { if (!isKnown(e.message)) errors.push("pageerror: " + e.message); });
    page.on("response", (r) => { if (r.status() >= 400 && !isKnown(r.url())) errors.push(r.status() + ": " + r.url()); });
    let gebaeudePost = null;  // saveProject() legt ein Gebäude an (nutzt das „Bautechnik"-Backend)
    page.on("response", (r) => { if (r.request().method() === "POST" && r.url().includes("/api/geb")) gebaeudePost = r.status(); });

    let pass = true;
    const step = (ok, name) => { console.log((ok ? "  ✓ " : "  ✗ ") + name); pass = pass && ok; };

    // Wartet, bis ein Ergebnis-Element eine Zahl enthält (kein „—"/leer).
    async function waitResult(id, label, shot) {
        try {
            await page.waitForFunction((eid) => {
                const e = document.getElementById(eid);
                return e && /\d/.test(e.innerText) && e.innerText.indexOf("—") < 0;
            }, id, { timeout: 9000 });
            if (shot) await page.screenshot({ path: path.join(OUT, shot) });
            const txt = await page.textContent("#" + id);
            step(true, label + " → " + (txt || "").trim());
        } catch (e) {
            if (shot) await page.screenshot({ path: path.join(OUT, shot) });
            step(false, label + " (kein Ergebnis in #" + id + ")");
        }
    }
    const openTab = async (ctrl) => { await page.click(`button[aria-controls="${ctrl}"]`); await page.waitForSelector(`#${ctrl}.active`, { timeout: 5000 }); await page.waitForTimeout(250); };

    await page.goto(BASE, { waitUntil: "networkidle" });
    step(true, "Seite geladen");

    // 1) Gebäudedaten (nur Defaults, keine Berechnung)
    await openTab("daten");
    step(await page.isVisible("#bgf"), "Tab Gebäudedaten");

    // 2) Gebäudehülle – Pipeline anstoßen (rechnet Hülle + Anlage + Bilanz durch)
    await openTab("huelle");
    await page.evaluate(() => window.recompute('huelle'));
    await waitResult("specific_heat_result", "Gebäudehülle (Heizwärmebedarf)", "10_huelle.png");

    // 3) Anlagentechnik – von der Pipeline automatisch mitgerechnet
    await openTab("anlage");
    await waitResult("system_total_end", "Anlagentechnik (Endenergie)", "11_anlage.png");
    // Live-Update: Heizsystem-Kartenklick muss automatisch neu rechnen –
    // das letzte Systemergebnis muss danach zur Wärmepumpe gehören.
    await page.click('.heat-card[data-heat="heatpump"]');
    try {
        await page.waitForFunction(() =>
            window.lastSystemResult && window.lastSystemResult.din
            && window.lastSystemResult.din.heating_system === 'heatpump',
            { timeout: 9000 });
        step(true, "Anlagentechnik: Heizsystem-Wechsel rechnet automatisch neu");
    } catch (e) {
        step(false, "Anlagentechnik: keine Neuberechnung nach Heizsystem-Wechsel");
    }
    await page.click('.heat-card[data-heat="gas"]');   // zurück auf Standard
    await page.waitForFunction(() =>
        window.lastSystemResult && window.lastSystemResult.din
        && window.lastSystemResult.din.heating_system === 'gas',
        { timeout: 9000 }).catch(() => {});

    // 4) Photovoltaik – PV ist standardmäßig deaktiviert (Ja/Nein-Gate), erst „Ja" wählen
    await openTab("pv");
    await page.click('#pv_gate_yes');
    await page.waitForSelector('#pv_body', { state: "visible", timeout: 5000 });
    await page.waitForTimeout(250);
    await page.evaluate(() => window.recompute('pv'));
    await waitResult("pv_annual_yield", "Photovoltaik (Jahresertrag)", "12_pv.png");
    step(true, "PV-Gate: Ja zeigt PV-Inhalt + Modell");

    // 5) Energiebilanz
    await openTab("bilanz");
    await page.click('button:has-text("Energiebilanz aktualisieren")');
    await waitResult("hb_result", "Energiebilanz (Heizwärmebedarf)", "13_bilanz.png");

    // 6) DIN 4108 (Tab-Button ruft initDin4108)
    await openTab("din4108");
    step(await page.isVisible("#d48-mws"), "Tab DIN 4108 sichtbar");
    await page.click('button:has-text("Aus Gebäudedaten & Hülle")');
    await page.waitForTimeout(400);
    const note = await page.textContent("#d48-prefill-note");
    step(note && note.includes("übernommen"), "DIN 4108: Prefill übernimmt vorhandene Eingaben");
    await page.click('button:has-text("Mindestwärmeschutz prüfen")');
    await page.waitForSelector("#d48-mws-res .d48-badge", { timeout: 5000 });
    await page.screenshot({ path: path.join(OUT, "14_din_mws.png") });
    step(true, "DIN 4108: Mindestwärmeschutz");
    await page.click('[data-d48="som"]');
    await page.click('button:has-text("Sommernachweis berechnen")');
    await page.waitForSelector("#d48-som-res .d48-badge", { timeout: 5000 });
    step((await page.textContent("#d48-som-res")).includes("S_vorh"), "DIN 4108: Sommerlicher Wärmeschutz");
    await page.click('[data-d48="tau"]');
    await page.click('button:has-text("Tauwasser berechnen")');
    await page.waitForSelector("#d48-tau-res .d48-badge", { timeout: 5000 });
    step((await page.textContent("#d48-tau-res")).includes("Tauwasser M_c"), "DIN 4108: Tauwasser (Glaser)");
    await page.click('[data-d48="wbl"]');
    await page.click('button:has-text("Luftdichtheit prüfen")');
    await page.waitForSelector("#d48-n50-res .d48-badge", { timeout: 5000 });
    await page.screenshot({ path: path.join(OUT, "15_din_wbl.png") });
    step(true, "DIN 4108: Luftdichtheit");

    // 7) Aktive Header-Features, die das verbliebene „Bautechnik"-Backend nutzen
    //    (Absicherung nach Entfernung des toten Bautechnik-Tabs)
    await page.click('button:has-text("Projekt speichern")');
    await page.waitForTimeout(1500);
    step(gebaeudePost !== null && gebaeudePost < 400, "Projekt speichern → POST /api/gebäude/ " + gebaeudePost);
    let popupOk = false;
    try {
        const [pp] = await Promise.all([
            page.waitForEvent("popup", { timeout: 6000 }),
            page.click('button:has-text("Bericht (PDF)")'),
        ]);
        await pp.waitForLoadState("domcontentloaded").catch(() => {});
        popupOk = (await pp.title()).includes("Bericht");
        await pp.close().catch(() => {});
    } catch (e) {}
    step(popupOk, "Bericht (PDF) öffnet Druckfenster");

    // 8) Keine JS-/Netzwerkfehler über den gesamten Durchlauf
    step(errors.length === 0, "keine JS-/Netzwerkfehler" + (errors.length ? " — " + errors.slice(0, 8).join(" | ") : ""));

    await browser.close();
    console.log("\nScreenshots: " + OUT);
    console.log(pass ? "SMOKE-TEST BESTANDEN ✅" : "SMOKE-TEST FEHLGESCHLAGEN ❌");
    process.exit(pass ? 0 : 1);
})().catch((e) => { console.error(e); process.exit(1); });
