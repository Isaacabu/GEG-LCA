import type {
  Construction,
  RoofCalcMode,
  RoofDormer,
  RoofInput,
  RoofInsulationPosition,
  RoofMaterial,
  RoofShading,
  RoofSurfaceCoating,
  RoofType,
  RoofVentilation,
  SummerProtection,
} from "@geg/shared";

const ROOF_TYPES: { value: RoofType; label: string }[] = [
  { value: "saddle", label: "Satteldach" },
  { value: "monopitch", label: "Pultdach" },
  { value: "flat", label: "Flachdach" },
  { value: "hipped", label: "Walmdach" },
  { value: "mansard", label: "Mansarddach" },
  { value: "tent", label: "Zeltdach" },
  { value: "shed", label: "Sheddach" },
  { value: "green", label: "Gruendach" },
  { value: "sheetMetal", label: "Blechdach" },
  { value: "industrial", label: "Industriedach" },
  { value: "custom", label: "benutzerdefiniert" },
];

const CALC_MODES: { value: RoofCalcMode; label: string }[] = [
  { value: "againstOutside", label: "Dachflaeche gegen Aussenluft" },
  { value: "topFloorCeilingAgainstUnheated", label: "oberste Geschossdecke gegen unbeheizten Dachraum" },
  { value: "heatedAtticRoof", label: "beheiztes Dachgeschoss" },
  { value: "partiallyHeatedAttic", label: "teilweise beheiztes Dachgeschoss" },
  { value: "flatDirectOverHeated", label: "Flachdach direkt ueber beheiztem Raum" },
];

const INSUL_POS: { value: RoofInsulationPosition; label: string }[] = [
  { value: "none", label: "keine Daemmung" },
  { value: "betweenRafters", label: "Zwischensparrendaemmung" },
  { value: "aboveRafters", label: "Aufsparrendaemmung" },
  { value: "belowRafters", label: "Untersparrendaemmung" },
  { value: "combined", label: "kombinierte Daemmung" },
  { value: "topCeiling", label: "Daemmung oberste Geschossdecke" },
  { value: "flatRoof", label: "Flachdachdaemmung" },
  { value: "partial", label: "teilweise gedaemmt" },
  { value: "unknown", label: "unbekannt" },
];

const MATERIALS: { value: RoofMaterial; label: string }[] = [
  { value: "claytile", label: "Ziegel" },
  { value: "concreteTile", label: "Betondachstein" },
  { value: "metal", label: "Blech" },
  { value: "slate", label: "Schiefer" },
  { value: "bitumen", label: "Bitumen" },
  { value: "epdm", label: "EPDM / Folie" },
  { value: "gravel", label: "Kiesdach" },
  { value: "green", label: "Gruendach" },
  { value: "wood", label: "Holzkonstruktion" },
  { value: "sandwich", label: "Sandwichpaneel" },
  { value: "custom", label: "benutzerdefiniert" },
];

const VENTS: { value: RoofVentilation; label: string }[] = [
  { value: "none", label: "nicht hinterlueftet" },
  { value: "ventilated", label: "hinterlueftet" },
  { value: "strongVent", label: "stark hinterlueftet" },
  { value: "unknown", label: "unbekannt" },
];

const SUMMER: { value: SummerProtection; label: string }[] = [
  { value: "low", label: "gering" },
  { value: "medium", label: "mittel" },
  { value: "good", label: "gut" },
  { value: "veryGood", label: "sehr gut" },
];

const COATINGS: { value: RoofSurfaceCoating; label: string }[] = [
  { value: "default", label: "Standard" },
  { value: "light", label: "hell" },
  { value: "dark", label: "dunkel" },
  { value: "reflective", label: "reflektierend" },
  { value: "green", label: "begruent" },
];

const SHADINGS: { value: RoofShading; label: string }[] = [
  { value: "none", label: "keine" },
  { value: "partial", label: "teilweise" },
  { value: "strong", label: "stark" },
];

const uid = () => Math.random().toString(36).slice(2, 10);

export function RoofSection({
  roof,
  setRoof,
  constructions,
  autoAreaM2,
  expertMode,
}: {
  roof: RoofInput;
  setRoof: (r: RoofInput) => void;
  constructions: Construction[];
  autoAreaM2: number;
  expertMode: boolean;
}) {
  const isFlat = roof.roofType === "flat";
  const addDormer = () => {
    const d: RoofDormer = {
      id: uid(),
      name: `Gaube ${roof.dormers.length + 1}`,
      widthM: 1.5,
      heightM: 1.2,
      uValueWm2K: 1.8,
    };
    setRoof({ ...roof, dormers: [...roof.dormers, d] });
  };
  const updateDormer = (id: string, patch: Partial<RoofDormer>) => {
    setRoof({
      ...roof,
      dormers: roof.dormers.map((d) => (d.id === id ? { ...d, ...patch } : d)),
    });
  };
  const removeDormer = (id: string) => {
    setRoof({ ...roof, dormers: roof.dormers.filter((d) => d.id !== id) });
  };

  return (
    <div style={{ opacity: roof.enabled ? 1 : 0.6 }}>
      <div className="grid grid-3" style={{ gap: 16 }}>
        <label className="field">
          <span className="field-label">Dach aktiv</span>
          <select className="select" value={roof.enabled ? "yes" : "no"}
            onChange={(e) => setRoof({ ...roof, enabled: e.target.value === "yes" })}>
            <option value="yes">ja</option>
            <option value="no">deaktiviert (ungenutzt)</option>
          </select>
        </label>
        <label className="field">
          <span className="field-label">Dachtyp</span>
          <select className="select" value={roof.roofType}
            onChange={(e) => setRoof({ ...roof, roofType: e.target.value as RoofType })}>
            {ROOF_TYPES.map((r) => (<option key={r.value} value={r.value}>{r.label}</option>))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Berechnungsart</span>
          <select className="select" value={roof.calcMode}
            onChange={(e) => setRoof({ ...roof, calcMode: e.target.value as RoofCalcMode })}>
            {CALC_MODES.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
          </select>
        </label>
        <div className="field">
          <span className="field-label">Dachflaeche [m²]</span>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <input className="input" type="number" min={0} step={0.1}
              value={roof.autoFromGeometry ? autoAreaM2 : roof.areaM2}
              disabled={roof.autoFromGeometry}
              onChange={(e) => setRoof({ ...roof, areaM2: Number(e.target.value) || 0 })} />
            <label style={{ fontSize: 11, color: "var(--muted)", display: "flex", alignItems: "center", gap: 4 }}>
              <input type="checkbox" checked={roof.autoFromGeometry}
                onChange={(e) => setRoof({ ...roof, autoFromGeometry: e.target.checked })} />
              auto
            </label>
          </div>
        </div>
        <label className="field">
          <span className="field-label">Material</span>
          <select className="select" value={roof.material}
            onChange={(e) => setRoof({ ...roof, material: e.target.value as RoofMaterial })}>
            {MATERIALS.map((m) => (<option key={m.value} value={m.value}>{m.label}</option>))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Daemmposition</span>
          <select className="select" value={roof.insulationPosition}
            onChange={(e) => setRoof({ ...roof, insulationPosition: e.target.value as RoofInsulationPosition })}>
            {INSUL_POS.map((p) => (<option key={p.value} value={p.value}>{p.label}</option>))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Daemmstaerke [mm]</span>
          <input className="input" type="number" min={0} step={10}
            value={roof.insulationThicknessMM}
            onChange={(e) => setRoof({ ...roof, insulationThicknessMM: Number(e.target.value) || 0 })} />
        </label>
        <label className="field">
          <span className="field-label">isoliert?</span>
          <select className="select" value={roof.insulated ? "yes" : "no"}
            onChange={(e) => setRoof({ ...roof, insulated: e.target.value === "yes" })}>
            <option value="yes">ja</option>
            <option value="no">nein</option>
          </select>
        </label>
        <label className="field" style={{ gridColumn: "span 2" }}>
          <span className="field-label">Dachaufbau</span>
          <select className="select" value={roof.constructionId ?? ""}
            onChange={(e) => setRoof({ ...roof, constructionId: e.target.value || null })}>
            <option value="" disabled>Dachaufbau waehlen …</option>
            {constructions.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
          </select>
        </label>
        {expertMode && (
          <>
            <label className="field">
              <span className="field-label">Hinterlueftung</span>
              <select className="select" value={roof.ventilation}
                onChange={(e) => setRoof({ ...roof, ventilation: e.target.value as RoofVentilation })}>
                {VENTS.map((v) => (<option key={v.value} value={v.value}>{v.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Neigung [°]</span>
              <input className="input" type="number" min={0} max={90} step={1}
                value={roof.pitchDeg ?? 30}
                onChange={(e) => setRoof({ ...roof, pitchDeg: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">Dachueberstand [m]</span>
              <input className="input" type="number" min={0} step={0.05}
                value={roof.overhangM ?? 0}
                onChange={(e) => setRoof({ ...roof, overhangM: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">Sommerlicher Schutz</span>
              <select className="select" value={roof.summerProtection ?? "medium"}
                onChange={(e) => setRoof({ ...roof, summerProtection: e.target.value as SummerProtection })}>
                {SUMMER.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Dachfensterflaeche [m²]</span>
              <input className="input" type="number" min={0} step={0.1}
                value={roof.rooflightAreaM2 ?? 0}
                onChange={(e) => setRoof({ ...roof, rooflightAreaM2: Number(e.target.value) || 0 })} />
            </label>
            <label className="field">
              <span className="field-label">U manuell</span>
              <input className="input" type="number" min={0} step={0.01}
                value={roof.uValueOverrideWm2K ?? 0}
                onChange={(e) => setRoof({ ...roof, uValueOverrideWm2K: Number(e.target.value) || undefined })} />
            </label>
            {isFlat && (
              <>
                <label className="field">
                  <span className="field-label">Beschichtung</span>
                  <select className="select" value={roof.coating ?? "default"}
                    onChange={(e) => setRoof({ ...roof, coating: e.target.value as RoofSurfaceCoating })}>
                    {COATINGS.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
                  </select>
                </label>
                <label className="field">
                  <span className="field-label">Beschattung</span>
                  <select className="select" value={roof.shading ?? "none"}
                    onChange={(e) => setRoof({ ...roof, shading: e.target.value as RoofShading })}>
                    {SHADINGS.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
                  </select>
                </label>
              </>
            )}
          </>
        )}
      </div>

      {!roof.insulated && (
        <div className="warning-panel" style={{ marginTop: 12 }}>
          Dach nicht isoliert - hoher Waermeverlust wahrscheinlich.
        </div>
      )}

      {expertMode && (
        <div style={{ marginTop: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <h3 style={{ margin: 0 }}>Gauben</h3>
            <button className="btn btn-ghost" type="button" onClick={addDormer}>+ Gaube</button>
          </div>
          {roof.dormers.length === 0 && (
            <p style={{ color: "var(--muted)", fontSize: 12 }}>Keine Gauben angelegt.</p>
          )}
          {roof.dormers.map((d) => (
            <div key={d.id} className="item-row">
              <div className="row-actions">
                <button className="btn-icon" title="entfernen"
                  onClick={() => removeDormer(d.id)} type="button">×</button>
              </div>
              <label className="field">
                <span className="field-label">Name</span>
                <input className="input" value={d.name}
                  onChange={(e) => updateDormer(d.id, { name: e.target.value })} />
              </label>
              <label className="field">
                <span className="field-label">B [m]</span>
                <input className="input" type="number" min={0} step={0.05} value={d.widthM}
                  onChange={(e) => updateDormer(d.id, { widthM: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">H [m]</span>
                <input className="input" type="number" min={0} step={0.05} value={d.heightM}
                  onChange={(e) => updateDormer(d.id, { heightM: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">U [W/(m²K)]</span>
                <input className="input" type="number" min={0} step={0.05} value={d.uValueWm2K}
                  onChange={(e) => updateDormer(d.id, { uValueWm2K: Number(e.target.value) || 0 })} />
              </label>
              <div className="row-foot">A = {(d.widthM * d.heightM).toFixed(3)} m²</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
