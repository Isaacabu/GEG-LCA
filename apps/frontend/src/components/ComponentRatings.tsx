import type { ComponentRating, ComponentTrafficLight, WeakSpot } from "@geg/shared";

const COLORS: Record<ComponentTrafficLight, string> = {
  green: "#22c55e",
  yellow: "#facc15",
  orange: "#fb923c",
  red: "#ef4444",
};

export function ComponentRatings({
  ratings,
  weakSpots,
}: {
  ratings: ComponentRating[];
  weakSpots: WeakSpot[];
}) {
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div>
        <h3 style={{ marginBottom: 10 }}>Bauteilbewertung</h3>
        <div className="grid grid-3" style={{ gap: 12 }}>
          {ratings.map((r) => (
            <div key={r.id} className="metric" style={{ borderColor: COLORS[r.rating] }}>
              <div className="metric-label">{r.label}</div>
              <div className="metric-value" style={{ fontSize: 22 }}>
                {r.metricValue !== null ? r.metricValue.toFixed(3) : "—"}
                <span className="metric-unit">{r.metric}</span>
              </div>
              <div className="metric-sub">
                {r.hContributionWK !== undefined
                  ? `H = ${r.hContributionWK.toFixed(2)} W/K`
                  : ""}
                {typeof r.share === "number"
                  ? ` · Anteil ${(r.share * 100).toFixed(0)} %`
                  : ""}
              </div>
              <div
                className="metric-pill"
                style={{ borderColor: COLORS[r.rating], color: COLORS[r.rating], marginTop: 8 }}
              >
                {r.rating.toUpperCase()}
              </div>
              {r.note && (
                <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>{r.note}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {weakSpots.length > 0 && (
        <div>
          <h3 style={{ marginBottom: 10 }}>Schwachstellen-Ranking</h3>
          <div style={{ display: "grid", gap: 8 }}>
            {weakSpots.map((w) => (
              <div
                key={w.id}
                className="glass"
                style={{
                  padding: "14px 18px",
                  borderColor: COLORS[w.rating],
                }}
              >
                <strong style={{ color: COLORS[w.rating] }}>
                  {w.label} · {w.rating.toUpperCase()}
                </strong>
                <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 4 }}>
                  {w.reason}
                </div>
                <div style={{ marginTop: 6, fontSize: 13 }}>
                  Empfehlung: {w.recommendation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
