import { useState } from "react";
import { TopNavigation, type Page } from "./components/TopNavigation.js";
import { AnimatedWaveBackground } from "./components/AnimatedWaveBackground.js";
import { FloatingHudIcons } from "./components/FloatingHudIcons.js";
import { Dashboard } from "./pages/Dashboard.js";
import { BuildingData } from "./pages/BuildingData.js";
import { Envelope } from "./pages/Envelope.js";
import { Results } from "./pages/Results.js";
import { useBuildingStore } from "./hooks/useBuildingStore.js";

export function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const store = useBuildingStore();
  return (
    <div className="app-shell">
      <AnimatedWaveBackground />
      <FloatingHudIcons />
      <TopNavigation
        current={page}
        onChange={setPage}
      />
      <main className="app-main">
        {page === "dashboard" && <Dashboard onNavigate={setPage} />}
        {page === "buildingData" && <BuildingData store={store} />}
        {page === "envelope" && <Envelope store={store} />}
        {page === "results" && <Results store={store} />}
      </main>
    </div>
  );
}
