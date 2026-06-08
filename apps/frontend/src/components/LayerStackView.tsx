import type { UValueResult } from "@geg/shared";

export function LayerStackView({ uResult }: { uResult: UValueResult | null }) {
  if (!uResult) return null;

  if (uResult.method === "fixedUValue") {
    return (
      <div className="layer-stack">
        <div className="layer layer-head">
          <span />
          <span>Bauteil</span>
          <span className="layer-val">—</span>
          <span className="layer-val">—</span>
          <span className="layer-val">U [W/(m²K)]</span>
        </div>
        <div className="layer">
          <span className="layer-idx">F</span>
          <span className="layer-name">U-Wert aus fertigem Bauteil übernommen</span>
          <span className="layer-val">—</span>
          <span className="layer-val">—</span>
          <span className="layer-val">{uResult.uValueWm2K.toFixed(3)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="layer-stack">
      <div className="layer layer-head">
        <span />
        <span>Schicht (innen &rarr; aussen)</span>
        <span className="layer-val">d [m]</span>
        <span className="layer-val">&lambda; [W/(mK)]</span>
        <span className="layer-val">R [m²K/W]</span>
      </div>
      <div className="layer">
        <span className="layer-idx">Rsi</span>
        <span className="layer-name">Waermeuebergang innen</span>
        <span className="layer-val">—</span>
        <span className="layer-val">—</span>
        <span className="layer-val">{uResult.rsi.toFixed(3)}</span>
      </div>
      {uResult.layers.map((l, i) => (
        <div className="layer" key={i}>
          <span className="layer-idx">{i + 1}</span>
          <span className="layer-name">{l.materialName}</span>
          <span className="layer-val">{l.thicknessM.toFixed(3)}</span>
          <span className="layer-val">{l.lambdaWmK.toFixed(3)}</span>
          <span className="layer-val">{l.rLayer.toFixed(3)}</span>
        </div>
      ))}
      <div className="layer">
        <span className="layer-idx">Rse</span>
        <span className="layer-name">Waermeuebergang aussen</span>
        <span className="layer-val">—</span>
        <span className="layer-val">—</span>
        <span className="layer-val">{uResult.rse.toFixed(3)}</span>
      </div>
      <div className="layer layer-head">
        <span />
        <span>R_total / U-Wert</span>
        <span className="layer-val">—</span>
        <span className="layer-val">
          R = {uResult.rTotal.toFixed(3)}
        </span>
        <span className="layer-val">
          U = {uResult.uValueWm2K.toFixed(3)}
        </span>
      </div>
    </div>
  );
}
