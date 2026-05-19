import type { EnvelopeResult, HeatingDemandResult, Orientation } from "@geg/shared";
import { ORIENTATION_LABELS } from "@geg/shared";
import { MetricCard } from "./MetricCard.js";
import { TrafficLight } from "./TrafficLight.js";
import { EnergyClassBadge } from "./EnergyClassBadge.js";

function fmt(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

export function EnergyResults({
  envelope,
  heating,
}: {
  envelope: EnvelopeResult | null;
  heating: HeatingDemandResult | null;
}) {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid grid-2" style={{ gap: 12 }}>
        <EnergyClassBadge
          cls={heating?.energyClass ?? null}
          spec={heating?.specificDemandGrossKWhM2A ?? null}
        />
        <TrafficLight result={heating} />
      </div>

      <div>
        <h3 style={{ marginBottom: 12 }}>Transmissionswaermeverluste</h3>
        <div className="kpi-row">
          <MetricCard label="H Waende" value={envelope ? fmt(envelope.wallsTotalWK) : "—"} unit="W/K" />
          <MetricCard label="H Fenster" value={envelope ? fmt(envelope.windowsTotalWK) : "—"} unit="W/K" />
          <MetricCard label="H Türen" value={envelope ? fmt(envelope.doorsTotalWK) : "—"} unit="W/K" />
          <MetricCard
            label="H Boeden"
            value={envelope ? fmt(envelope.floorsTotalWK) : "—"}
            unit="W/K"
          />
        </div>
        <div className="kpi-row" style={{ marginTop: 14 }}>
          <MetricCard
            label="H Dach"
            value={envelope?.roof ? fmt(envelope.roof.hTransmissionWK) : "—"}
            unit="W/K"
          />
          <MetricCard
            label="H_T gesamt"
            value={envelope ? fmt(envelope.hTTotalWK) : "—"}
            unit="W/K"
            pill={
              envelope && envelope.hTTotalWK > 0
                ? { text: "berechnet", variant: "success" }
                : undefined
            }
          />
          <MetricCard
            label="Hᵥ Lüftung"
            value={heating ? fmt(heating.hVEffectiveWK) : "—"}
            unit="W/K"
            sub={heating ? `H_V_brutto ${heating.hVWK.toFixed(2)}` : "—"}
          />
          <MetricCard
            label="Heizperiode G_t"
            value="84"
            unit="kKh/a"
            sub="vereinfachter Projektwert"
          />
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 12 }}>Solare Gewinne</h3>
        <div className="kpi-row">
          {(["north", "south", "east", "west"] as Orientation[]).map((o) => (
            <MetricCard
              key={o}
              label={ORIENTATION_LABELS[o]}
              value={envelope ? fmt(envelope.solarGainsByOrientation[o] ?? 0) : "—"}
              unit="kWh/a"
            />
          ))}
        </div>
        <div className="kpi-row" style={{ marginTop: 14 }}>
          <MetricCard
            label="Solar gesamt"
            value={envelope ? fmt(envelope.solarGainsTotalKWhA) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="innere Gewinne"
            value={heating ? fmt(heating.internalGainsKWhA) : "—"}
            unit="kWh/a"
            sub="22 kWh/(m²·a) × A_ref (Projektansatz)"
          />
          <MetricCard
            label="genutzte Gewinne"
            value={heating ? fmt(heating.usedGainsKWhA) : "—"}
            unit="kWh/a"
            sub={heating ? `η_gn = ${heating.utilisationFactor.toFixed(3)}` : "—"}
          />
          <MetricCard
            label="Q_T + Q_V"
            value={
              heating
                ? fmt(heating.transmissionLossKWhA + heating.ventilationLossKWhA)
                : "—"
            }
            unit="kWh/a"
          />
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 12 }}>Bilanzierung</h3>
        <div className="kpi-row">
          <MetricCard
            label="Q_H netto"
            value={heating ? fmt(heating.heatingDemandNetKWhA, 1) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="Erzeugungsverluste"
            value={heating ? fmt(heating.generationLossKWhA, 1) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="Verteilverluste"
            value={heating ? fmt(heating.distributionLossKWhA, 1) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="Speicherverluste"
            value={heating ? fmt(heating.storageLossKWhA, 1) : "—"}
            unit="kWh/a"
          />
        </div>
        <div className="kpi-row" style={{ marginTop: 14 }}>
          <MetricCard
            label="Warmwasserbedarf"
            value={heating ? fmt(heating.hotWaterDemandKWhA, 1) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="Hilfsenergie"
            value={heating ? fmt(heating.auxiliaryEnergyKWhA, 1) : "—"}
            unit="kWh/a"
            sub="Pumpen + Ventilatoren"
          />
          <MetricCard
            label="PV / Solar-Anrechnung"
            value={heating ? `-${fmt(heating.solarOffsetKWhA, 1)}` : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="Endenergie / Q_H brutto"
            value={heating ? fmt(heating.endEnergyKWhA, 1) : "—"}
            unit="kWh/a"
          />
        </div>
        <div className="kpi-row" style={{ marginTop: 14 }}>
          <MetricCard
            label="Primaerenergie"
            value={heating ? fmt(heating.primaryEnergyKWhA, 1) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="CO2-Ausstoss"
            value={heating ? fmt(heating.co2EmissionsKgA, 1) : "—"}
            unit="kg/a"
          />
          <MetricCard
            label="spezifisch netto"
            value={heating ? fmt(heating.specificDemandNetKWhM2A, 1) : "—"}
            unit="kWh/(m²·a)"
          />
          <MetricCard
            label="spezifisch brutto"
            value={heating ? fmt(heating.specificDemandGrossKWhM2A, 1) : "—"}
            unit="kWh/(m²·a)"
          />
        </div>
      </div>
    </div>
  );
}
