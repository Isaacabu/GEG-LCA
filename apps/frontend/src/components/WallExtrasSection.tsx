import type {
  WallExtras,
  WallFacadeColor,
  WallInsulationState,
  WallType,
} from "@geg/shared";

const WALL_TYPES: { value: WallType; label: string }[] = [
  { value: "solidMass", label: "Massivwand" },
  { value: "brick", label: "Ziegelwand" },
  { value: "concrete", label: "Betonwand" },
  { value: "aerated", label: "Porenbetonwand" },
  { value: "calciumSilicate", label: "Kalksandsteinwand" },
  { value: "timberFrame", label: "Holzständerwand" },
  { value: "halfTimber", label: "Fachwerk" },
  { value: "naturalStone", label: "Naturstein" },
  { value: "lightConstruction", label: "Leichtbau" },
  { value: "unknown", label: "unbekannt" },
  { value: "custom", label: "benutzerdefiniert" },
];

const INSULATIONS: { value: WallInsulationState; label: string }[] = [
  { value: "none", label: "keine Dämmung" },
  { value: "interior", label: "Innendämmung" },
  { value: "exterior", label: "Außendämmung / WDVS" },
  { value: "core", label: "Kerndämmung" },
  { value: "ventilatedFacade", label: "hinterlüftete Fassade" },
  { value: "partial", label: "teilweise gedämmt" },
  { value: "unknown", label: "unbekannt" },
];

const COLORS: { value: WallFacadeColor; label: string }[] = [
  { value: "light", label: "hell" },
  { value: "medium", label: "mittel" },
  { value: "dark", label: "dunkel" },
  { value: "reflective", label: "reflektierend" },
  { value: "custom", label: "benutzerdefiniert" },
];

export function WallExtrasSection({
  extras,
  setExtras,
  expertMode,
}: {
  extras: WallExtras;
  setExtras: (e: WallExtras) => void;
  expertMode: boolean;
}) {
  return (
    <div className="grid grid-3" style={{ gap: 16 }}>
      <label className="field">
        <span className="field-label">Wandtyp</span>
        <select className="select" value={extras.wallType}
          onChange={(e) => setExtras({ ...extras, wallType: e.target.value as WallType })}>
          {WALL_TYPES.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
        </select>
      </label>
      <label className="field">
        <span className="field-label">Dämmzustand</span>
        <select className="select" value={extras.insulationState}
          onChange={(e) => setExtras({ ...extras, insulationState: e.target.value as WallInsulationState })}>
          {INSULATIONS.map((i) => (<option key={i.value} value={i.value}>{i.label}</option>))}
        </select>
      </label>
      <label className="field">
        <span className="field-label">Fassadenfarbe</span>
        <select className="select" value={extras.facadeColor}
          onChange={(e) => setExtras({ ...extras, facadeColor: e.target.value as WallFacadeColor })}>
          {COLORS.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
        </select>
      </label>
      {expertMode && (
        <>
          <label className="field">
            <span className="field-label">ΔU Wärmebrücke</span>
            <input className="input" type="number" min={0} step={0.01}
              value={extras.thermalBridgeDeltaUWm2K}
              onChange={(e) => setExtras({ ...extras, thermalBridgeDeltaUWm2K: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">U manuell [W/(m²K)]</span>
            <input className="input" type="number" min={0} step={0.01}
              value={extras.uValueOverrideWm2K ?? 0}
              onChange={(e) => setExtras({ ...extras, uValueOverrideWm2K: Number(e.target.value) || undefined })} />
          </label>
        </>
      )}
    </div>
  );
}
