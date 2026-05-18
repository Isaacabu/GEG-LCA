import { useEffect, useRef, useState } from "react";
import { api } from "../api/client.js";

export type OBDMaterialItem = {
  uuid: string;
  name: string;
  category: string;
  densityKgM3: number | null;
  defaultThicknessM: number | null;
  lambdaWmK: number | null;
  url: string;
};

export function OBDMaterialPicker({
  label,
  value,
  onChange,
}: {
  label?: string;
  value: OBDMaterialItem | null;
  onChange: (m: OBDMaterialItem) => void;
}) {
  const [query, setQuery] = useState(value?.name ?? "");
  const [results, setResults] = useState<OBDMaterialItem[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounced search
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (!open) return;
    timerRef.current = setTimeout(() => {
      setLoading(true);
      api
        .searchOBD(query, 30)
        .then((r) => setResults(r.items))
        .catch(() => setResults([]))
        .finally(() => setLoading(false));
    }, 280);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [query, open]);

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function select(m: OBDMaterialItem) {
    setQuery(m.name);
    setOpen(false);
    onChange(m);
  }

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      {label && <span className="field-label">{label}</span>}
      <input
        className="input"
        placeholder="Ökobaudat-Material suchen …"
        value={query}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        style={{ width: "100%" }}
      />
      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            zIndex: 200,
            background: "var(--surface-2, #1e2130)",
            border: "1px solid var(--border, rgba(255,255,255,0.12))",
            borderRadius: 8,
            maxHeight: 320,
            overflowY: "auto",
            boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
          }}
        >
          {loading && (
            <div style={{ padding: "10px 14px", color: "var(--muted)", fontSize: 13 }}>
              Suche …
            </div>
          )}
          {!loading && results.length === 0 && (
            <div style={{ padding: "10px 14px", color: "var(--muted)", fontSize: 13 }}>
              Keine Ergebnisse
            </div>
          )}
          {results.map((m) => (
            <button
              key={m.uuid}
              type="button"
              onClick={() => select(m)}
              style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                padding: "9px 14px",
                background: "none",
                border: "none",
                borderBottom: "1px solid var(--border, rgba(255,255,255,0.07))",
                cursor: "pointer",
                color: "var(--text)",
              }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLElement).style.background = "var(--surface-3, rgba(255,255,255,0.06))")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLElement).style.background = "none")
              }
            >
              <div style={{ fontSize: 13, fontWeight: 500 }}>{m.name}</div>
              <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2, display: "flex", gap: 12 }}>
                <span>{m.category.replace(/'/g, "").split("/").slice(0, 2).join(" › ")}</span>
                {m.lambdaWmK !== null && (
                  <span style={{ color: "var(--accent, #60a5fa)", fontWeight: 600 }}>
                    λ = {m.lambdaWmK.toFixed(3)} W/(mK)
                  </span>
                )}
                {m.densityKgM3 && (
                  <span>ρ = {m.densityKgM3} kg/m³</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
