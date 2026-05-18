import type {
  Orientation,
  WindowFrame,
  WindowGlazing,
  WindowInstall,
  WindowItem,
  WindowShadingKind,
  WindowType,
} from "@geg/shared";

const ORIENTATIONS: { value: Orientation; label: string }[] = [
  { value: "north", label: "Nord" },
  { value: "northeast", label: "Nord-Ost" },
  { value: "east", label: "Ost" },
  { value: "southeast", label: "Sued-Ost" },
  { value: "south", label: "Sued" },
  { value: "southwest", label: "Sued-West" },
  { value: "west", label: "West" },
  { value: "northwest", label: "Nord-West" },
  { value: "horizontal", label: "horizontal / Dachfenster" },
];

const TYPES: { value: WindowType; label: string }[] = [
  { value: "casement", label: "Einfachfenster" },
  { value: "boxWindow", label: "Kastenfenster" },
  { value: "compositeWindow", label: "Verbundfenster" },
  { value: "doubleWindow", label: "Doppelfenster" },
  { value: "tiltTurn", label: "Dreh-Kipp" },
  { value: "fixed", label: "Festverglasung" },
  { value: "sliding", label: "Schiebefenster" },
  { value: "rooflight", label: "Dachfenster" },
  { value: "floorToCeiling", label: "bodentiefes Fenster" },
  { value: "balconyDoor", label: "Balkonfenster" },
  { value: "shopfront", label: "Schaufenster" },
  { value: "custom", label: "benutzerdefiniert" },
];

const GLAZINGS: { value: WindowGlazing; label: string; defaultU: number; defaultG: number }[] = [
  { value: "single", label: "Einfachverglasung", defaultU: 5.0, defaultG: 0.85 },
  { value: "double-old", label: "2-fach alt", defaultU: 2.8, defaultG: 0.75 },
  { value: "double-thermal", label: "2-fach Waermeschutz", defaultU: 1.3, defaultG: 0.6 },
  { value: "triple-thermal", label: "3-fach Waermeschutz", defaultU: 0.9, defaultG: 0.5 },
  { value: "solarControl", label: "Sonnenschutzglas", defaultU: 1.1, defaultG: 0.35 },
  { value: "safety", label: "Sicherheitsglas", defaultU: 1.4, defaultG: 0.55 },
  { value: "unknown", label: "unbekannt", defaultU: 2.0, defaultG: 0.6 },
  { value: "custom", label: "benutzerdefiniert", defaultU: 1.3, defaultG: 0.6 },
];

const FRAMES: { value: WindowFrame; label: string }[] = [
  { value: "wood", label: "Holz" },
  { value: "pvc", label: "Kunststoff" },
  { value: "alu", label: "Alu (ohne therm. Trennung)" },
  { value: "aluTherm", label: "Alu (therm. getrennt)" },
  { value: "woodAlu", label: "Holz-Alu" },
  { value: "steel", label: "Stahl" },
  { value: "unknown", label: "unbekannt" },
];

const INSTALL: { value: WindowInstall; label: string }[] = [
  { value: "oldUnrenovated", label: "Altbau unsaniert" },
  { value: "normal", label: "normal" },
  { value: "lowThermalBridge", label: "waermebrueckenarm" },
  { value: "leakyJoints", label: "undichte Anschluesse" },
  { value: "newSeal", label: "neue Abdichtung" },
  { value: "unknown", label: "unbekannt" },
];

const SHADINGS: { value: WindowShadingKind; label: string; defaultF: number }[] = [
  { value: "none", label: "keine", defaultF: 1.0 },
  { value: "interiorBlind", label: "Innenrollo", defaultF: 0.65 },
  { value: "exteriorShutter", label: "Aussenrollladen", defaultF: 0.3 },
  { value: "venetian", label: "Raffstore", defaultF: 0.35 },
  { value: "awning", label: "Markise", defaultF: 0.4 },
  { value: "roofOverhang", label: "Dachueberstand", defaultF: 0.7 },
  { value: "balconyOverhang", label: "Balkonueberstand", defaultF: 0.6 },
  { value: "neighbourBuilding", label: "Nachbargebaeude", defaultF: 0.7 },
  { value: "trees", label: "Baeume", defaultF: 0.6 },
  { value: "partial", label: "teilverschattet", defaultF: 0.75 },
  { value: "manual", label: "manuell", defaultF: 0.9 },
];

export function WindowList({
  windows,
  add,
  update,
  remove,
  duplicate,
  expertMode,
}: {
  windows: WindowItem[];
  add: (o?: Orientation) => void;
  update: (id: string, patch: Partial<WindowItem>) => void;
  remove: (id: string) => void;
  duplicate: (id: string) => void;
  expertMode: boolean;
}) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, gap: 12, flexWrap: "wrap" }}>
        <p style={{ color: "var(--muted)", fontSize: 13, maxWidth: 720 }}>
          A = Anzahl × Breite × Hoehe. A_eff = A · g · F_F · F_S · F_dirt · F_w.
          Solare Gewinne pro Orientierung (Nord/Sued/Ost/West, Zwischenrichtungen, horizontal).
        </p>
        <button className="btn btn-ghost" onClick={() => add("south")}>+ Fenster</button>
      </div>
      {windows.length === 0 && (
        <p style={{ color: "var(--muted)" }}>Noch keine Fenster angelegt.</p>
      )}
      {windows.map((w) => {
        const area =
          Math.max(0, w.count) * Math.max(0, w.widthM) * Math.max(0, w.heightM);
        return (
          <div key={w.id} className="item-row">
            <div className="row-actions">
              <button
                className="btn-icon ghost"
                title="duplizieren"
                onClick={() => duplicate(w.id)}
                type="button"
              >
                ⎘
              </button>
              <button
                className="btn-icon"
                title="entfernen"
                onClick={() => remove(w.id)}
                type="button"
              >
                ×
              </button>
            </div>

            <label className="field">
              <span className="field-label">Name</span>
              <input className="input" value={w.name}
                onChange={(e) => update(w.id, { name: e.target.value })} />
            </label>
            <label className="field">
              <span className="field-label">Orientierung</span>
              <select className="select" value={w.orientation}
                onChange={(e) => update(w.id, { orientation: e.target.value as Orientation })}>
                {ORIENTATIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Anzahl</span>
              <input className="input" type="number" min={0} step={1} value={w.count}
                onChange={(e) => update(w.id, { count: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">B [m]</span>
              <input className="input" type="number" min={0} step={0.05} value={w.widthM}
                onChange={(e) => update(w.id, { widthM: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">H [m]</span>
              <input className="input" type="number" min={0} step={0.05} value={w.heightM}
                onChange={(e) => update(w.id, { heightM: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">Typ</span>
              <select className="select" value={w.type}
                onChange={(e) => update(w.id, { type: e.target.value as WindowType })}>
                {TYPES.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Verglasung</span>
              <select className="select" value={w.glazing}
                onChange={(e) => {
                  const g = e.target.value as WindowGlazing;
                  const preset = GLAZINGS.find((x) => x.value === g)!;
                  update(w.id, {
                    glazing: g,
                    uValueWm2K: g === "custom" ? w.uValueWm2K : preset.defaultU,
                    gValue: g === "custom" ? w.gValue : preset.defaultG,
                  });
                }}>
                {GLAZINGS.map((g) => (<option key={g.value} value={g.value}>{g.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Rahmen</span>
              <select className="select" value={w.frame}
                onChange={(e) => update(w.id, { frame: e.target.value as WindowFrame })}>
                {FRAMES.map((f) => (<option key={f.value} value={f.value}>{f.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">U_w</span>
              <input className="input" type="number" min={0} step={0.05} value={w.uValueWm2K}
                onChange={(e) => update(w.id, { uValueWm2K: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">g</span>
              <input className="input" type="number" min={0} max={1} step={0.05} value={w.gValue}
                onChange={(e) => update(w.id, { gValue: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">Verschattung</span>
              <select className="select" value={w.shadingKind}
                onChange={(e) => {
                  const v = e.target.value as WindowShadingKind;
                  const preset = SHADINGS.find((x) => x.value === v)!;
                  update(w.id, {
                    shadingKind: v,
                    shadingFactor: v === "manual" ? w.shadingFactor : preset.defaultF,
                  });
                }}>
                {SHADINGS.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
              </select>
            </label>
            {expertMode && (
              <>
                <label className="field">
                  <span className="field-label">F_S</span>
                  <input className="input" type="number" min={0} max={1} step={0.05}
                    value={w.shadingFactor}
                    onChange={(e) => update(w.id, { shadingFactor: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">F_F</span>
                  <input className="input" type="number" min={0} max={1} step={0.05}
                    value={w.frameFactor}
                    onChange={(e) => update(w.id, { frameFactor: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">F_dirt</span>
                  <input className="input" type="number" min={0} max={1} step={0.05}
                    value={w.dirtFactor}
                    onChange={(e) => update(w.id, { dirtFactor: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">F_w</span>
                  <input className="input" type="number" min={0} max={1} step={0.05}
                    value={w.nonPerpFactor}
                    onChange={(e) => update(w.id, { nonPerpFactor: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">Rahmenanteil</span>
                  <input className="input" type="number" min={0} max={1} step={0.05}
                    value={w.frameShareFraction}
                    onChange={(e) => update(w.id, { frameShareFraction: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">Einbau</span>
                  <select className="select" value={w.install}
                    onChange={(e) => update(w.id, { install: e.target.value as WindowInstall })}>
                    {INSTALL.map((i) => (<option key={i.value} value={i.value}>{i.label}</option>))}
                  </select>
                </label>
                {w.orientation === "horizontal" && (
                  <label className="field">
                    <span className="field-label">Neigung [°]</span>
                    <input className="input" type="number" min={0} max={90} step={1}
                      value={w.tiltDeg ?? 30}
                      onChange={(e) => update(w.id, { tiltDeg: Number(e.target.value) || 0 })} />
                  </label>
                )}
              </>
            )}

            <div className="row-foot">
              <span>A = {area.toFixed(3)} m²</span>
              <span>
                A_eff = {(area * w.gValue * w.frameFactor * w.shadingFactor * w.dirtFactor * w.nonPerpFactor).toFixed(3)} m²
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
