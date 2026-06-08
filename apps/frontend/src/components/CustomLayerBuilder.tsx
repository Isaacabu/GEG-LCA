import { useMemo, useState } from "react";
import { OBDMaterialPicker, type OBDMaterialItem } from "./OBDMaterialPicker.js";

export type CustomLayer = {
  id: string;
  material: OBDMaterialItem | null;
  thicknessM: number;
};

/** Surface thermal resistances for exterior walls (DIN EN ISO 6946) */
const RSI = 0.13; // interior [m²K/W]
const RSE = 0.04; // exterior [m²K/W]

function calcU(layers: CustomLayer[]): number | null {
  const complete = layers.filter((l) => l.material?.lambdaWmK && l.thicknessM > 0);
  if (complete.length === 0) return null;
  const rTotal =
    RSI +
    complete.reduce((sum, l) => sum + l.thicknessM / l.material!.lambdaWmK!, 0) +
    RSE;
  return 1 / rTotal;
}

let _nextId = 1;
function newId() {
  return `layer-${_nextId++}`;
}

export function CustomLayerBuilder({
  layers,
  onChange,
}: {
  layers: CustomLayer[];
  onChange: (layers: CustomLayer[]) => void;
}) {
  const uValue = useMemo(() => calcU(layers), [layers]);

  function addLayer() {
    onChange([...layers, { id: newId(), material: null, thicknessM: 0.1 }]);
  }

  function removeLayer(id: string) {
    onChange(layers.filter((l) => l.id !== id));
  }

  function updateLayer(id: string, patch: Partial<CustomLayer>) {
    onChange(layers.map((l) => (l.id === id ? { ...l, ...patch } : l)));
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {/* Header row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 120px 90px 90px 32px",
          gap: 8,
          fontSize: 11,
          color: "var(--muted)",
          fontWeight: 600,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          padding: "0 4px",
        }}
      >
        <span>Material (Ökobaudat)</span>
        <span>d [m]</span>
        <span>λ [W/(mK)]</span>
        <span>R [m²K/W]</span>
        <span />
      </div>

      {/* Layers */}
      {layers.map((layer, idx) => {
        const r =
          layer.material?.lambdaWmK && layer.thicknessM > 0
            ? layer.thicknessM / layer.material.lambdaWmK
            : null;
        return (
          <div
            key={layer.id}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 120px 90px 90px 32px",
              gap: 8,
              alignItems: "center",
            }}
          >
            <OBDMaterialPicker
              value={layer.material}
              onChange={(m) => updateLayer(layer.id, { material: m })}
            />
            <input
              className="input"
              type="number"
              min={0.001}
              max={2}
              step={0.01}
              value={layer.thicknessM}
              onChange={(e) =>
                updateLayer(layer.id, { thicknessM: Number(e.target.value) || 0 })
              }
            />
            <div
              style={{
                padding: "0 8px",
                fontSize: 13,
                color:
                  layer.material?.lambdaWmK != null
                    ? "var(--accent, #60a5fa)"
                    : "var(--muted)",
              }}
            >
              {layer.material?.lambdaWmK != null
                ? layer.material.lambdaWmK.toFixed(3)
                : "—"}
            </div>
            <div
              style={{
                padding: "0 8px",
                fontSize: 13,
                color: r != null ? "var(--text)" : "var(--muted)",
              }}
            >
              {r != null ? r.toFixed(3) : "—"}
            </div>
            <button
              type="button"
              className="btn-icon"
              title="Schicht entfernen"
              onClick={() => removeLayer(layer.id)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "var(--muted)",
                fontSize: 16,
                padding: 4,
              }}
            >
              ×
            </button>
          </div>
        );
      })}

      {/* Add layer + U-value result */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 4 }}>
        <button type="button" className="btn-secondary" onClick={addLayer}>
          + Schicht hinzufügen
        </button>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 13, color: "var(--muted)" }}>Rsi = {RSI} · Rse = {RSE}</div>
        <div
          style={{
            fontWeight: 700,
            fontSize: 16,
            color: uValue != null ? "var(--accent, #60a5fa)" : "var(--muted)",
          }}
        >
          U ={" "}
          {uValue != null ? (
            <>
              <span style={{ color: "var(--text)" }}>{uValue.toFixed(3)}</span>
              <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 4 }}>
                W/(m²K)
              </span>
            </>
          ) : (
            "—"
          )}
        </div>
      </div>
    </div>
  );
}
