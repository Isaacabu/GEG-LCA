export function NumberField({
  label,
  value,
  onChange,
  unit,
  step = 0.1,
  min = 0,
  warning,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  unit?: string;
  step?: number;
  min?: number;
  warning?: boolean;
}) {
  return (
    <label className="field">
      <span className="field-label">
        {label}
        {unit && <span style={{ color: "var(--dim)", marginLeft: 6 }}>[{unit}]</span>}
      </span>
      <input
        className={`input ${warning ? "warning" : ""}`}
        type="number"
        value={Number.isFinite(value) ? value : 0}
        min={min}
        step={step}
        onChange={(e) => {
          const n = Number(e.target.value);
          onChange(Number.isFinite(n) ? n : 0);
        }}
      />
    </label>
  );
}
