import type { Page } from "../components/TopNavigation.js";
import { HeroBuildingVisual } from "../components/HeroBuildingVisual.js";

export function Dashboard({ onNavigate }: { onNavigate: (p: Page) => void }) {
  return (
    <>
      <section className="hero" style={{ marginBottom: 24 }}>
        <div className="hero-eyebrow">
          <span className="dot" />
          PROJEKT · VEREINFACHTE GEG-/DIN-V-18599-RECHNUNG
        </div>
        <h1>Saubere U-Werte. Echte Hₜ. Echte Solargewinne.</h1>
        <p>
          Vom Außenwandaufbau bis zum spezifischen Heizwärmebedarf — alle
          Werte entstehen aus Geometrie, Material und Faktoren. Keine stillen
          Defaults, keine erfundenen 0,28 W/(m²K).
        </p>
        <div className="hero-cta-row">
          <button className="btn btn-primary" onClick={() => onNavigate("buildingData")} type="button">
            Gebäude anlegen →
          </button>
          <button className="btn btn-ghost" onClick={() => onNavigate("envelope")} type="button">
            Direkt zur Hülle
          </button>
          <button className="btn btn-ghost" onClick={() => onNavigate("results")} type="button">
            Ergebnisse
          </button>
        </div>
      </section>

      <HeroBuildingVisual
        onHotspot={(id) => {
          if (id === "roof" || id === "wall" || id === "window" || id === "door" || id === "floor") {
            onNavigate("envelope");
          }
        }}
      />
    </>
  );
}
