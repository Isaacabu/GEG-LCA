export function InteractiveBuildingHero({
  onHotspot,
}: {
  onHotspot?: (id: "roof" | "wall" | "window" | "door" | "floor") => void;
}) {
  const handle = (id: "roof" | "wall" | "window" | "door" | "floor") => () =>
    onHotspot?.(id);

  return (
    <div className="building-hero">
      <svg viewBox="0 0 800 360" role="img" aria-label="Gebaeudeschnitt">
        <defs>
          <linearGradient id="bgGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#0e1c33" />
            <stop offset="100%" stopColor="#07111f" />
          </linearGradient>
          <linearGradient id="wallGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#1d3457" />
            <stop offset="100%" stopColor="#11203a" />
          </linearGradient>
          <linearGradient id="roofGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.35" />
          </linearGradient>
        </defs>

        <rect x="0" y="0" width="800" height="360" fill="url(#bgGrad)" />

        {/* Boden / Floor */}
        <g className="hotspot" onClick={handle("floor")}>
          <rect x="60" y="300" width="680" height="14" fill="#0b1830" />
          <line
            x1="60"
            y1="307"
            x2="740"
            y2="307"
            stroke="#22d3ee"
            strokeOpacity="0.25"
            strokeDasharray="4 6"
          />
          <text x="80" y="335" fill="#9aa7b7" fontSize="11" letterSpacing="2">
            BODEN
          </text>
        </g>

        {/* Wand / Wall */}
        <g className="hotspot" onClick={handle("wall")}>
          <rect x="120" y="120" width="560" height="180" fill="url(#wallGrad)" />
          <rect
            x="120"
            y="120"
            width="560"
            height="180"
            fill="none"
            stroke="#22d3ee"
            strokeOpacity="0.25"
          />
          <text x="135" y="140" fill="#9aa7b7" fontSize="11" letterSpacing="2">
            AUSSENWAND
          </text>
        </g>

        {/* Dach / Roof */}
        <g className="hotspot" onClick={handle("roof")}>
          <polygon
            points="100,120 700,120 660,70 140,70"
            fill="url(#roofGrad)"
          />
          <polygon
            points="100,120 700,120 660,70 140,70"
            fill="none"
            stroke="#22d3ee"
            strokeOpacity="0.4"
          />
          <text x="350" y="100" fill="#06121f" fontSize="11" letterSpacing="2">
            DACH
          </text>
        </g>

        {/* Fenster / Windows */}
        <g className="hotspot" onClick={handle("window")}>
          <rect x="200" y="170" width="80" height="80" fill="#0e1c33" stroke="#f6b94b" strokeWidth="2" />
          <line x1="240" y1="170" x2="240" y2="250" stroke="#f6b94b" strokeOpacity="0.7" />
          <line x1="200" y1="210" x2="280" y2="210" stroke="#f6b94b" strokeOpacity="0.7" />
          <rect x="520" y="170" width="80" height="80" fill="#0e1c33" stroke="#f6b94b" strokeWidth="2" />
          <line x1="560" y1="170" x2="560" y2="250" stroke="#f6b94b" strokeOpacity="0.7" />
          <line x1="520" y1="210" x2="600" y2="210" stroke="#f6b94b" strokeOpacity="0.7" />
          <text x="200" y="265" fill="#f6b94b" fontSize="11" letterSpacing="2">
            FENSTER
          </text>
        </g>

        {/* Tuer / Door */}
        <g className="hotspot" onClick={handle("door")}>
          <rect x="370" y="200" width="60" height="100" fill="#0e1c33" stroke="#22d3ee" strokeWidth="2" />
          <circle cx="420" cy="252" r="2" fill="#22d3ee" />
          <text x="370" y="320" fill="#22d3ee" fontSize="11" letterSpacing="2">
            TUER
          </text>
        </g>
      </svg>
    </div>
  );
}
