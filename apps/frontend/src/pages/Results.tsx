import { GlassCard } from "../components/GlassCard.js";
import { EnergyResults } from "../components/EnergyResults.js";
import { EnvelopeSummary } from "../components/EnvelopeSummary.js";
import { WarningPanel } from "../components/WarningPanel.js";
import { ComponentRatings } from "../components/ComponentRatings.js";
import type { BuildingStore } from "../hooks/useBuildingStore.js";
import { useEnvelopeCalc } from "../hooks/useEnvelopeCalc.js";

export function Results({ store }: { store: BuildingStore }) {
  const { envelope, heating, error } = useEnvelopeCalc(store);
  return (
    <>
      <GlassCard eyebrow="ZUSAMMENFASSUNG" title="Energiebilanz und Bewertung">
        {error && <WarningPanel items={[error]} />}
        {envelope && envelope.warnings.length > 0 && (
          <WarningPanel title="Hinweise" items={envelope.warnings} />
        )}
        {heating && heating.notes.length > 0 && (
          <WarningPanel title="Berechnungsannahmen" items={heating.notes} />
        )}
        <div style={{ marginTop: 16 }}>
          <EnergyResults envelope={envelope} heating={heating} />
        </div>
      </GlassCard>

      <GlassCard eyebrow="BEWERTUNG" title="Bauteil-Ampel & Schwachstellen">
        {heating ? (
          <ComponentRatings
            ratings={heating.componentRatings}
            weakSpots={heating.weakSpots}
          />
        ) : (
          <p style={{ color: "var(--muted)" }}>Noch keine Bewertung verfuegbar.</p>
        )}
      </GlassCard>

      <GlassCard eyebrow="WAENDE" title="Transmission pro Orientierung">
        {envelope ? (
          <EnvelopeSummary envelope={envelope} />
        ) : (
          <p style={{ color: "var(--muted)" }}>
            Bitte erst Gebaeudedaten und Aussenwandaufbau in Schritt 03 setzen.
          </p>
        )}
      </GlassCard>
    </>
  );
}
