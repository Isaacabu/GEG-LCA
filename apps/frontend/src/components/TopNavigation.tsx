import type { ReactNode } from "react";
import { BrandLogo } from "./BrandLogo.js";

export type Page = "dashboard" | "buildingData" | "envelope" | "results";

const PAGES: { id: Page; label: string }[] = [
  { id: "dashboard", label: "01 Dashboard" },
  { id: "buildingData", label: "02 Gebäudedaten" },
  { id: "envelope", label: "03 Gebäudehülle" },
  { id: "results", label: "04 Ergebnisse" },
];

export function TopNavigation({
  current,
  onChange,
  right,
}: {
  current: Page;
  onChange: (p: Page) => void;
  right?: ReactNode;
}) {
  return (
    <header className="top-nav">
      <div className="top-nav-inner">
        <div className="brand">
          <BrandLogo />
          <div>
            <div className="brand-name">GEGenius</div>
          </div>
        </div>
        <nav className="steps" aria-label="Navigation">
          {PAGES.map((p) => (
            <button
              key={p.id}
              className={`step-btn ${current === p.id ? "active" : ""}`}
              onClick={() => onChange(p.id)}
              type="button"
            >
              {p.label}
            </button>
          ))}
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {right}
        </div>
      </div>
    </header>
  );
}
