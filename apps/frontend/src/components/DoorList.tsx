import type {
  BoundaryType,
  DoorItem,
  DoorMaterial,
  DoorOpeningFrequency,
  DoorSealCondition,
  DoorType,
  Orientation,
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
];

const DOOR_TYPES: { value: DoorType; label: string; defaultU: number }[] = [
  { value: "entrance", label: "Haustuer", defaultU: 1.4 },
  { value: "apartmentEntrance", label: "Wohnungseingangstuer", defaultU: 1.8 },
  { value: "sideEntrance", label: "Nebeneingangstuer", defaultU: 2.0 },
  { value: "basement", label: "Kellertuer", defaultU: 2.5 },
  { value: "garage", label: "Garagentor", defaultU: 3.0 },
  { value: "balcony", label: "Balkontuer", defaultU: 1.4 },
  { value: "terrace", label: "Terrassentuer", defaultU: 1.3 },
  { value: "fire", label: "Brandschutztuer", defaultU: 2.0 },
  { value: "glass", label: "Glastuer", defaultU: 1.6 },
  { value: "sectional", label: "Sektionaltor", defaultU: 1.3 },
  { value: "rollup", label: "Rolltor", defaultU: 5.0 },
  { value: "sliding", label: "Schiebetuer", defaultU: 1.8 },
  { value: "industrial", label: "Industrietor", defaultU: 2.5 },
  { value: "custom", label: "benutzerdefiniert", defaultU: 1.8 },
];

const MATERIALS: { value: DoorMaterial; label: string }[] = [
  { value: "woodSolid", label: "Holz massiv" },
  { value: "woodInsulated", label: "Holz gedaemmt" },
  { value: "pvc", label: "Kunststoff" },
  { value: "aluUninsulated", label: "Alu ungedaemmt" },
  { value: "aluInsulated", label: "Alu gedaemmt" },
  { value: "steelUninsulated", label: "Stahl ungedaemmt" },
  { value: "steelInsulated", label: "Stahl gedaemmt" },
  { value: "glass", label: "Glas" },
  { value: "composite", label: "Verbund" },
  { value: "unknown", label: "unbekannt" },
];

const SEALS: { value: DoorSealCondition; label: string }[] = [
  { value: "veryTight", label: "sehr dicht" },
  { value: "normal", label: "normal dicht" },
  { value: "slightlyLeaky", label: "leicht undicht" },
  { value: "veryLeaky", label: "stark undicht" },
  { value: "noSeal", label: "keine Dichtung" },
  { value: "unknown", label: "unbekannt" },
];

const FREQS: { value: DoorOpeningFrequency; label: string }[] = [
  { value: "rare", label: "selten" },
  { value: "normal", label: "normal" },
  { value: "frequent", label: "haeufig" },
  { value: "veryFrequent", label: "sehr haeufig" },
  { value: "publicTraffic", label: "Publikumsverkehr" },
  { value: "manual", label: "manuell" },
];

const BOUNDARIES: { value: BoundaryType; label: string }[] = [
  { value: "outside", label: "Aussenluft" },
  { value: "unheatedRoom", label: "unbeheizter Keller / Raum" },
  { value: "basement", label: "Keller" },
  { value: "corridor", label: "Treppenhaus / Flur" },
  { value: "heatedRoom", label: "beheizter Raum" },
];

export function DoorList({
  doors,
  add,
  update,
  remove,
  duplicate,
  expertMode,
}: {
  doors: DoorItem[];
  add: (o?: Orientation) => void;
  update: (id: string, patch: Partial<DoorItem>) => void;
  remove: (id: string) => void;
  duplicate: (id: string) => void;
  expertMode: boolean;
}) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, gap: 12, flexWrap: "wrap" }}>
        <p style={{ color: "var(--muted)", fontSize: 13, maxWidth: 720 }}>
          Türen werden automatisch von der jeweiligen Wandfläche abgezogen.
          Gegen beheizten Raum gibt es keinen H-Wert.
        </p>
        <button className="btn btn-ghost" onClick={() => add("south")}>+ Tür</button>
      </div>
      {doors.length === 0 && (
        <p style={{ color: "var(--muted)" }}>Noch keine Türen angelegt.</p>
      )}
      {doors.map((d) => {
        const area =
          Math.max(0, d.count) * Math.max(0, d.widthM) * Math.max(0, d.heightM);
        return (
          <div key={d.id} className="item-row">
            <div className="row-actions">
              <button
                className="btn-icon ghost"
                title="duplizieren"
                onClick={() => duplicate(d.id)}
                type="button"
              >⎘</button>
              <button
                className="btn-icon"
                title="entfernen"
                onClick={() => remove(d.id)}
                type="button"
              >×</button>
            </div>
            <label className="field">
              <span className="field-label">Name</span>
              <input className="input" value={d.name}
                onChange={(e) => update(d.id, { name: e.target.value })} />
            </label>
            <label className="field">
              <span className="field-label">Orientierung</span>
              <select className="select" value={d.orientation}
                onChange={(e) => update(d.id, { orientation: e.target.value as Orientation })}>
                {ORIENTATIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Anzahl</span>
              <input className="input" type="number" min={0} step={1} value={d.count}
                onChange={(e) => update(d.id, { count: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">B [m]</span>
              <input className="input" type="number" min={0} step={0.05} value={d.widthM}
                onChange={(e) => update(d.id, { widthM: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">H [m]</span>
              <input className="input" type="number" min={0} step={0.05} value={d.heightM}
                onChange={(e) => update(d.id, { heightM: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">Typ</span>
              <select className="select" value={d.doorType}
                onChange={(e) => {
                  const t = e.target.value as DoorType;
                  const preset = DOOR_TYPES.find((x) => x.value === t)!;
                  update(d.id, {
                    doorType: t,
                    uValueWm2K: t === "custom" ? d.uValueWm2K : preset.defaultU,
                  });
                }}>
                {DOOR_TYPES.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Material</span>
              <select className="select" value={d.material}
                onChange={(e) => update(d.id, { material: e.target.value as DoorMaterial })}>
                {MATERIALS.map((m) => (<option key={m.value} value={m.value}>{m.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">U [W/(m²K)]</span>
              <input className="input" type="number" min={0} step={0.05} value={d.uValueWm2K}
                onChange={(e) => update(d.id, { uValueWm2K: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">grenzt an</span>
              <select className="select" value={d.boundaryType}
                onChange={(e) => update(d.id, { boundaryType: e.target.value as BoundaryType })}>
                {BOUNDARIES.map((b) => (<option key={b.value} value={b.value}>{b.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Dichtung</span>
              <select className="select" value={d.sealCondition}
                onChange={(e) => update(d.id, { sealCondition: e.target.value as DoorSealCondition })}>
                {SEALS.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
              </select>
            </label>
            {expertMode && (
              <>
                <label className="field">
                  <span className="field-label">Glasanteil [%]</span>
                  <input className="input" type="number" min={0} max={100} step={1}
                    value={d.glassFractionPct}
                    onChange={(e) => update(d.id, { glassFractionPct: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">Dicke [m]</span>
                  <input className="input" type="number" min={0} step={0.005}
                    value={d.thicknessM ?? 0}
                    onChange={(e) => update(d.id, { thicknessM: Number(e.target.value) || 0 })} />
                </label>
                <label className="field">
                  <span className="field-label">Schwelle gedaemmt</span>
                  <select className="select" value={d.thresholdInsulated ? "yes" : "no"}
                    onChange={(e) => update(d.id, { thresholdInsulated: e.target.value === "yes" })}>
                    <option value="yes">ja</option>
                    <option value="no">nein</option>
                  </select>
                </label>
                <label className="field">
                  <span className="field-label">Oeffnung</span>
                  <select className="select" value={d.openingFrequency}
                    onChange={(e) => update(d.id, { openingFrequency: e.target.value as DoorOpeningFrequency })}>
                    {FREQS.map((f) => (<option key={f.value} value={f.value}>{f.label}</option>))}
                  </select>
                </label>
              </>
            )}
            <div className="row-foot">
              <span>A = {area.toFixed(3)} m²</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
