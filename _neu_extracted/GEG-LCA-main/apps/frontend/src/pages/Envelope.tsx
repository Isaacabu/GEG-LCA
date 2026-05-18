import { useEffect, useMemo, useState } from "react";
import type {
  BoundaryType,
  Construction,
  UValueResult,
  WallOrientation,
} from "@geg/shared";
import { WALL_ORIENTATION_LABELS } from "@geg/shared";
import { api } from "../api/client.js";
import { GlassCard } from "../components/GlassCard.js";
import { MetricCard } from "../components/MetricCard.js";
import { SelectField } from "../components/SelectField.js";
import { LayerStackView } from "../components/LayerStackView.js";
import { WarningPanel } from "../components/WarningPanel.js";
import { Accordion } from "../components/Accordion.js";
import { WindowList } from "../components/WindowList.js";
import { DoorList } from "../components/DoorList.js";
import { FloorSection } from "../components/FloorSection.js";
import { RoofSection } from "../components/RoofSection.js";
import { EnvelopeSummary } from "../components/EnvelopeSummary.js";
import { TrafficLight } from "../components/TrafficLight.js";
import { EnergyClassBadge } from "../components/EnergyClassBadge.js";
import { WallExtrasSection } from "../components/WallExtrasSection.js";
import { HvacSection } from "../components/HvacSection.js";
import { CustomLayerBuilder } from "../components/CustomLayerBuilder.js";
import type { BuildingStore } from "../hooks/useBuildingStore.js";
import { useEnvelopeCalc } from "../hooks/useEnvelopeCalc.js";

const BOUNDARY_OPTIONS: { value: BoundaryType; label: string }[] = [
  { value: "outside", label: "Außenluft" },
  { value: "heatedRoom", label: "beheizter Nachbarraum" },
  { value: "unheatedRoom", label: "unbeheizter Raum" },
  { value: "corridor", label: "Treppenhaus / Flur" },
  { value: "basement", label: "Keller" },
  { value: "ground", label: "Erdreich" },
  { value: "none", label: "ignorieren" },
];

function fmt(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

export function Envelope({ store }: { store: BuildingStore }) {
  const [externalWalls, setExternalWalls] = useState<Construction[]>([]);
  const [floors, setFloors] = useState<Construction[]>([]);
  const [roofs, setRoofs] = useState<Construction[]>([]);
  const [uResult, setUResult] = useState<UValueResult | null>(null);
  const [uError, setUError] = useState<string | null>(null);

  const { envelope, heating, error: calcError } = useEnvelopeCalc(store);

  useEffect(() => {
    Promise.all([
      api.listByElement("walls"),
      api.listByElement("floors"),
      api.listByElement("roofs"),
    ])
      .then(([w, f, r]) => {
        setExternalWalls(w.items);
        setFloors(f.items);
        setRoofs(r.items);
      })
      .catch((e) => setUError(e instanceof Error ? e.message : String(e)));
  }, []);

  useEffect(() => {
    setUResult(null);
    if (!store.externalWallConstructionId) return;
    api
      .calcUValue(store.externalWallConstructionId)
      .then((r) => setUResult(r))
      .catch((e) => setUError(e instanceof Error ? e.message : String(e)));
  }, [store.externalWallConstructionId]);

  const externalWallOptions = useMemo(
    () => externalWalls.map((c) => ({ value: c.id, label: c.name })),
    [externalWalls],
  );

  const planArea = store.grossArea;

  return (
    <>
      <Accordion
        items={[
          {
            id: "walls",
            eyebrow: "A",
            title: "Außenwände",
            defaultOpen: true,
            meta: envelope?.externalWallUValueWm2K ? (
              <span className="tag">U = {envelope.externalWallUValueWm2K.toFixed(3)}</span>
            ) : (
              <span className="tag neutral">U noch nicht definiert</span>
            ),
            body: (
              <>
                <WallExtrasSection
                  extras={store.wallExtras}
                  setExtras={store.setWallExtras}
                  expertMode={store.expertMode}
                />
                <div className="divider" />
                <div className="grid grid-2" style={{ gap: 16 }}>
                  <SelectField
                    label="Außenwandaufbau (Katalog)"
                    value={store.externalWallConstructionId}
                    placeholder="Außenwandaufbau wählen …"
                    options={externalWallOptions}
                    onChange={(v) => store.setExternalWallConstructionId(v)}
                  />
                </div>
                <div className="divider" />
                {uResult ? (
                  <LayerStackView uResult={uResult} />
                ) : (
                  <p style={{ color: "var(--muted)" }}>
                    Wähle einen Außenwandaufbau, oder setze im Experten-Modus
                    einen U-Wert direkt. Kein Default-U-Wert.
                  </p>
                )}
                <div className="divider" />
                <h3 style={{ marginBottom: 12 }}>Schichtweiser Aufbau (Ökobaudat)</h3>
                <CustomLayerBuilder
                  layers={store.customWallLayers}
                  onChange={store.setCustomWallLayers}
                />
                <div className="divider" />
                <h3 style={{ marginBottom: 12 }}>Orientierungen (Grenzbedingung)</h3>
                <div className="grid grid-4">
                  {store.wallOrientations.map((w) => (
                    <div key={w.orientation} className="metric">
                      <div className="metric-label">
                        {WALL_ORIENTATION_LABELS[w.orientation as WallOrientation]}
                      </div>
                      <div className="metric-value" style={{ fontSize: 22 }}>
                        {w.grossAreaM2.toFixed(2)}
                        <span className="metric-unit">m²</span>
                      </div>
                      <div style={{ marginTop: 10 }}>
                        <SelectField<BoundaryType>
                          label="grenzt an"
                          value={store.overrides[w.orientation as WallOrientation].boundaryType}
                          options={BOUNDARY_OPTIONS}
                          onChange={(v) =>
                            store.setBoundary(w.orientation as WallOrientation, v)
                          }
                        />
                      </div>
                    </div>
                  ))}
                </div>
                {uError && <WarningPanel items={[uError]} />}
                {envelope && (
                  <div style={{ marginTop: 16 }}>
                    <EnvelopeSummary envelope={envelope} />
                  </div>
                )}
              </>
            ),
          },
          {
            id: "windows",
            eyebrow: "B",
            title: "Fenster",
            meta: envelope ? (
              <span className="tag gold">Sum H = {fmt(envelope.windowsTotalWK)} W/K</span>
            ) : null,
            body: (
              <WindowList
                windows={store.windows}
                add={store.addWindow}
                update={store.updateWindow}
                remove={store.removeWindow}
                duplicate={store.duplicateWindow}
                expertMode={store.expertMode}
              />
            ),
          },
          {
            id: "doors",
            eyebrow: "C",
            title: "Türen",
            meta: envelope ? (
              <span className="tag">Sum H = {fmt(envelope.doorsTotalWK)} W/K</span>
            ) : null,
            body: (
              <DoorList
                doors={store.doors}
                add={store.addDoor}
                update={store.updateDoor}
                remove={store.removeDoor}
                duplicate={store.duplicateDoor}
                expertMode={store.expertMode}
              />
            ),
          },
          {
            id: "floor",
            eyebrow: "D",
            title: "Boden / Bodenplatte / Zwischendecken",
            meta: envelope?.floorsTotalWK ? (
              <span className="tag">Sum H = {fmt(envelope.floorsTotalWK)} W/K</span>
            ) : (
              <span className="tag neutral">noch nicht gewaehlt</span>
            ),
            body: (
              <FloorSection
                floors={store.floors}
                add={store.addFloor}
                update={store.updateFloor}
                remove={store.removeFloor}
                duplicate={store.duplicateFloor}
                constructions={floors}
                autoAreaM2={planArea}
                expertMode={store.expertMode}
              />
            ),
          },
          {
            id: "roof",
            eyebrow: "E",
            title: "Dach",
            meta: envelope?.roof?.uValueWm2K
              ? <span className="tag">U = {envelope.roof.uValueWm2K.toFixed(3)}</span>
              : <span className="tag neutral">noch nicht gewaehlt</span>,
            body: (
              <RoofSection
                roof={store.roof}
                setRoof={store.setRoof}
                constructions={roofs}
                autoAreaM2={planArea}
                expertMode={store.expertMode}
              />
            ),
          },
          {
            id: "hvac",
            eyebrow: "F",
            title: "Lüftung & Anlagentechnik",
            body: (
              <HvacSection
                ventilation={store.ventilation} setVentilation={store.setVentilation}
                heating={store.heating} setHeating={store.setHeating}
                hotWater={store.hotWater} setHotWater={store.setHotWater}
                distribution={store.distribution} setDistribution={store.setDistribution}
                pv={store.pv} setPv={store.setPv}
                expertMode={store.expertMode}
              />
            ),
          },
        ]}
      />

      <div style={{ height: 16 }} />

      <GlassCard
        eyebrow="LIVE"
        title="Live-Bilanz"
        right={
          <div style={{ display: "flex", gap: 10 }}>
            <EnergyClassBadge
              cls={heating?.energyClass ?? null}
              spec={heating?.specificDemandGrossKWhM2A ?? null}
            />
            <TrafficLight result={heating} />
          </div>
        }
      >
        {calcError && <WarningPanel items={[calcError]} />}
        <div className="kpi-row">
          <MetricCard
            label="U-Wert Aussenwand"
            value={envelope?.externalWallUValueWm2K ? fmt(envelope.externalWallUValueWm2K, 3) : "—"}
            unit="W/(m²K)"
            sub={
              envelope?.externalWallUValueMethod === "layers"
                ? "aus Schichtaufbau"
                : envelope?.externalWallUValueMethod === "fixedUValue"
                  ? "aus festem Bauteilwert"
                  : envelope?.externalWallUValueMethod === "override"
                    ? "manuell uebersteuert"
                    : "Aussenwandaufbau fehlt"
            }
          />
          <MetricCard
            label="H_T gesamt"
            value={envelope ? fmt(envelope.hTTotalWK) : "—"}
            unit="W/K"
          />
          <MetricCard
            label="Endenergie"
            value={heating ? fmt(heating.endEnergyKWhA, 1) : "—"}
            unit="kWh/a"
          />
          <MetricCard
            label="CO2 / Klasse"
            value={heating ? fmt(heating.co2EmissionsKgA, 0) : "—"}
            unit="kg/a"
            sub={heating ? `Klasse ${heating.energyClass}` : "—"}
          />
        </div>
        <p style={{ color: "var(--muted)", fontSize: 12, marginTop: 12 }}>
          Vereinfachte, normnahe Berechnung nach GEG-/DIN-V-18599-Logik fuer Projektzwecke.
        </p>
      </GlassCard>
    </>
  );
}
