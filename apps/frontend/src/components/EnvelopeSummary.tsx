import type { EnvelopeResult, WallOrientation } from "@geg/shared";
import { MetricCard } from "./MetricCard.js";

function fmt(n: number | null, digits = 2): string {
  if (n === null || !Number.isFinite(n)) return "—";
  return n.toFixed(digits);
}

const ORIENTATION_LABEL: Record<WallOrientation, string> = {
  north: "Nord",
  south: "Süd",
  east: "Ost",
  west: "West",
};

const BOUNDARY_LABEL: Record<string, string> = {
  outside: "Außenluft",
  heatedRoom: "beheizter Raum",
  unheatedRoom: "unbeheizter Raum",
  corridor: "Flur",
  basement: "Keller",
  ground: "Erdreich",
  none: "ignoriert",
};

export function EnvelopeSummary({ envelope }: { envelope: EnvelopeResult }) {
  return (
    <div className="grid grid-4">
      {envelope.wallResultsByOrientation.map((w) => {
        const pill =
          w.status === "complete"
            ? { text: "berechnet", variant: "success" as const }
            : w.status === "ignored"
              ? { text: BOUNDARY_LABEL[w.boundaryType] ?? "ignoriert" }
              : w.status === "incomplete"
                ? { text: "unvollstaendig", variant: "warning" as const }
                : { text: "fehler", variant: "error" as const };
        return (
          <MetricCard
            key={w.orientation}
            label={`${ORIENTATION_LABEL[w.orientation]} · ${BOUNDARY_LABEL[w.boundaryType]}`}
            value={w.hTransmissionWK === null ? "—" : fmt(w.hTransmissionWK)}
            unit="W/K"
            status={w.status}
            pill={pill}
          />
        );
      })}
    </div>
  );
}
