import type { HeatingDemandResult } from "@geg/shared";

const LABEL: Record<HeatingDemandResult["trafficLight"], string> = {
  green: "Sehr gut",
  yellow: "Mittel",
  orange: "Kritisch",
  red: "Schlecht",
};

export function TrafficLight({
  result,
}: {
  result: HeatingDemandResult | null;
}) {
  if (!result) {
    return (
      <div className="traffic">
        <div className="traffic-led" />
        <div className="traffic-text">
          <strong>Energieampel</strong>
          <span>noch keine Berechnung verfuegbar</span>
        </div>
      </div>
    );
  }
  return (
    <div className="traffic">
      <div className={`traffic-led ${result.trafficLight}`} />
      <div className="traffic-text">
        <strong>
          {LABEL[result.trafficLight]} ({result.specificDemandGrossKWhM2A.toFixed(1)} kWh/(m²·a))
        </strong>
        <span>
          Grenzen Projektansatz: &lt;50 gruen · &lt;100 gelb · &lt;150 orange · sonst rot
        </span>
      </div>
    </div>
  );
}
