import type { BuildingStore } from "../hooks/useBuildingStore.js";
import { GlassCard } from "../components/GlassCard.js";
import { NumberField } from "../components/NumberField.js";
import { MetricCard } from "../components/MetricCard.js";
import type { WallOrientation } from "@geg/shared";

const ORIENT_LABEL: Record<WallOrientation, string> = {
  north: "Nord",
  south: "Süd",
  east: "Ost",
  west: "West",
};

export function BuildingData({ store }: { store: BuildingStore }) {
  const { geometry, setGeometry, grossArea, totalHeight, volume, referenceArea, wallOrientations } = store;
  return (
    <>
      <GlassCard eyebrow="GEOMETRIE" title="Gebäudedaten"
        right={<span className="tag">Schritt 02</span>}
      >
        <div className="grid grid-4">
          <NumberField label="Länge" unit="m" value={geometry.lengthM}
            onChange={(v) => setGeometry({ ...geometry, lengthM: v })} />
          <NumberField label="Breite" unit="m" value={geometry.widthM}
            onChange={(v) => setGeometry({ ...geometry, widthM: v })} />
          <NumberField label="Etagen" unit="" value={geometry.floors} step={1} min={1}
            onChange={(v) => setGeometry({ ...geometry, floors: Math.max(1, Math.round(v)) })} />
          <NumberField label="Wandhöhe pro Etage" unit="m" value={geometry.storyHeightM}
            onChange={(v) => setGeometry({ ...geometry, storyHeightM: v })} />
        </div>
        <div className="divider" />
        <div className="grid grid-4">
          <MetricCard label="Grundfläche" value={grossArea.toFixed(2)} unit="m²" />
          <MetricCard label="Gesamtwandhöhe" value={totalHeight.toFixed(2)} unit="m" />
          <MetricCard label="Beheiztes Volumen" value={volume.toFixed(2)} unit="m³" />
          <MetricCard label="A_ref" value={referenceArea.toFixed(2)} unit="m²" />
        </div>
      </GlassCard>

      <GlassCard eyebrow="ABLEITUNG" title="Wandbruttoflächen pro Orientierung">
        <div className="grid grid-4">
          {wallOrientations.map((w) => (
            <MetricCard
              key={w.orientation}
              label={ORIENT_LABEL[w.orientation]}
              value={w.grossAreaM2.toFixed(2)}
              unit="m²"
            />
          ))}
        </div>
      </GlassCard>
    </>
  );
}
