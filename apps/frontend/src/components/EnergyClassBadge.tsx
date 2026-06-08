import type { EnergyClass } from "@geg/shared";

const COLORS: Record<EnergyClass, string> = {
  "A+": "#11a04a",
  A: "#22c55e",
  B: "#84cc16",
  C: "#eab308",
  D: "#facc15",
  E: "#fb923c",
  F: "#f97316",
  G: "#ef4444",
  H: "#b91c1c",
};

export function EnergyClassBadge({
  cls,
  spec,
}: {
  cls: EnergyClass | null;
  spec?: number | null;
}) {
  if (!cls) {
    return (
      <div className="traffic">
        <div className="traffic-led" />
        <div className="traffic-text">
          <strong>Energieklasse</strong>
          <span>noch keine Berechnung</span>
        </div>
      </div>
    );
  }
  const color = COLORS[cls];
  return (
    <div className="traffic" style={{ borderColor: color }}>
      <div
        className="traffic-led"
        style={{ background: color, boxShadow: `0 0 16px ${color}` }}
      />
      <div className="traffic-text">
        <strong>
          Klasse {cls}
          {typeof spec === "number"
            ? ` · ${spec.toFixed(1)} kWh/(m²·a)`
            : ""}
        </strong>
        <span>
          A+ ≤ 30 · A ≤ 50 · B ≤ 75 · C ≤ 100 · D ≤ 130 · E ≤ 160 · F ≤ 200 · G ≤ 250 · H &gt; 250
        </span>
      </div>
    </div>
  );
}
