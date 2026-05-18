import type {
  BoundaryType,
  Construction,
  FloorBoundaryRole,
  FloorInsulation,
  FloorItem,
} from "@geg/shared";

const BOUNDARIES: { value: BoundaryType; label: string }[] = [
  { value: "ground", label: "Erdreich" },
  { value: "basement", label: "Keller unbeheizt" },
  { value: "heatedRoom", label: "beheizter Raum / Keller beheizt" },
  { value: "unheatedRoom", label: "unbeheizter Raum" },
  { value: "outside", label: "Aussenluft" },
];

const ROLES: { value: FloorBoundaryRole; label: string }[] = [
  { value: "groundSlab", label: "Bodenplatte auf Erdreich" },
  { value: "basementCeiling", label: "Kellerdecke gegen unbeheizten Keller" },
  { value: "floorToOutside", label: "Boden gegen Aussenluft" },
  { value: "floorToGarage", label: "Boden gegen Garage" },
  { value: "crawlSpace", label: "Boden gegen Kriechkeller" },
  { value: "interFloor", label: "Zwischendecke beheizt" },
  { value: "floorOverArchway", label: "Boden über Durchfahrt" },
  { value: "topFloorCeiling", label: "oberste Geschossdecke" },
  { value: "custom", label: "benutzerdefiniert" },
];

const INSUL: { value: FloorInsulation; label: string }[] = [
  { value: "none", label: "keine Dämmung" },
  { value: "aboveSlab", label: "oberhalb der Bodenplatte" },
  { value: "belowSlab", label: "unterhalb der Bodenplatte" },
  { value: "perimeter", label: "Perimeterdämmung" },
  { value: "basementCeiling", label: "Kellerdeckendämmung" },
  { value: "partial", label: "teilweise gedämmt" },
  { value: "unknown", label: "unbekannt" },
];

export function FloorSection({
  floors,
  add,
  update,
  remove,
  duplicate,
  constructions,
  autoAreaM2,
  expertMode,
}: {
  floors: FloorItem[];
  add: () => void;
  update: (id: string, patch: Partial<FloorItem>) => void;
  remove: (id: string) => void;
  duplicate: (id: string) => void;
  constructions: Construction[];
  autoAreaM2: number;
  expertMode: boolean;
}) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, gap: 12, flexWrap: "wrap" }}>
        <p style={{ color: "var(--muted)", fontSize: 13, maxWidth: 720 }}>
          Boeden / Zwischendecken pro Bauteil. Deaktivieren z. B. wenn das Dachgeschoss
          ungenutzt ist und nur die oberste Geschossdecke zaehlt.
        </p>
        <button className="btn btn-ghost" onClick={() => add()}>+ Bodenbauteil</button>
      </div>
      {floors.length === 0 && (
        <p style={{ color: "var(--muted)" }}>Noch keine Bodenbauteile angelegt.</p>
      )}
      {floors.map((f) => (
        <div key={f.id} className="item-row" style={{ opacity: f.enabled ? 1 : 0.55 }}>
          <div className="row-actions">
            <button className="btn-icon ghost" title="duplizieren"
              onClick={() => duplicate(f.id)} type="button">⎘</button>
            <button className="btn-icon" title="entfernen"
              onClick={() => remove(f.id)} type="button">×</button>
          </div>

          <label className="field" style={{ gridColumn: "span 2" }}>
            <span className="field-label">Name</span>
            <input className="input" value={f.name}
              onChange={(e) => update(f.id, { name: e.target.value })} />
          </label>
          <label className="field">
            <span className="field-label">Etage</span>
            <input className="input" type="number" min={0} step={1} value={f.storyIndex}
              onChange={(e) => update(f.id, { storyIndex: Math.max(0, Math.round(Number(e.target.value) || 0)) })} />
          </label>
          <label className="field">
            <span className="field-label">Bauteiltyp</span>
            <select className="select" value={f.role}
              onChange={(e) => update(f.id, { role: e.target.value as FloorBoundaryRole })}>
              {ROLES.map((r) => (<option key={r.value} value={r.value}>{r.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">grenzt an</span>
            <select className="select" value={f.boundaryType}
              onChange={(e) => update(f.id, { boundaryType: e.target.value as BoundaryType })}>
              {BOUNDARIES.map((b) => (<option key={b.value} value={b.value}>{b.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Aufbau</span>
            <select className="select" value={f.constructionId ?? ""}
              onChange={(e) => update(f.id, { constructionId: e.target.value || null })}>
              <option value="" disabled>Bodenaufbau waehlen …</option>
              {constructions.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
            </select>
          </label>
          <div className="field">
            <span className="field-label">Flaeche [m²]</span>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <input className="input" type="number" min={0} step={0.1}
                value={f.autoFromGeometry ? autoAreaM2 : f.areaM2}
                disabled={f.autoFromGeometry}
                onChange={(e) => update(f.id, { areaM2: Number(e.target.value) || 0 })} />
              <label style={{ fontSize: 11, color: "var(--muted)", display: "flex", alignItems: "center", gap: 4 }}>
                <input type="checkbox" checked={f.autoFromGeometry}
                  onChange={(e) => update(f.id, { autoFromGeometry: e.target.checked })} />
                auto
              </label>
            </div>
          </div>
          <label className="field">
            <span className="field-label">aktiv</span>
            <select className="select" value={f.enabled ? "yes" : "no"}
              onChange={(e) => update(f.id, { enabled: e.target.value === "yes" })}>
              <option value="yes">ja</option>
              <option value="no">nein (deaktiviert)</option>
            </select>
          </label>
          {expertMode && (
            <>
              <label className="field">
                <span className="field-label">Daemmzustand</span>
                <select className="select" value={f.insulation}
                  onChange={(e) => update(f.id, { insulation: e.target.value as FloorInsulation })}>
                  {INSUL.map((i) => (<option key={i.value} value={i.value}>{i.label}</option>))}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Daemmstaerke [mm]</span>
                <input className="input" type="number" min={0} step={10}
                  value={f.insulationThicknessMM ?? 0}
                  onChange={(e) => update(f.id, { insulationThicknessMM: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">Slab-Dicke [m]</span>
                <input className="input" type="number" min={0} step={0.01}
                  value={f.slabThicknessM ?? 0}
                  onChange={(e) => update(f.id, { slabThicknessM: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">Perim. gegen Erdreich [m]</span>
                <input className="input" type="number" min={0} step={0.1}
                  value={f.perimeterAgainstGroundM ?? 0}
                  onChange={(e) => update(f.id, { perimeterAgainstGroundM: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">U manuell</span>
                <input className="input" type="number" min={0} step={0.01}
                  value={f.uValueOverrideWm2K ?? 0}
                  onChange={(e) => update(f.id, { uValueOverrideWm2K: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">FBH</span>
                <select className="select" value={f.floorHeating ? "yes" : "no"}
                  onChange={(e) => update(f.id, { floorHeating: e.target.value === "yes" })}>
                  <option value="no">keine</option>
                  <option value="yes">vorhanden</option>
                </select>
              </label>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
