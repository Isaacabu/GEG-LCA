import type { ReactNode } from "react";

export type MetricStatus = "complete" | "ignored" | "incomplete" | "error" | "neutral";

export function MetricCard({
  label,
  value,
  unit,
  sub,
  pill,
  status = "neutral",
  children,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  sub?: ReactNode;
  pill?: { text: string; variant?: "success" | "warning" | "error" };
  status?: MetricStatus;
  children?: ReactNode;
}) {
  const statusClass =
    status === "ignored"
      ? "ignored"
      : status === "incomplete"
        ? "warning"
        : status === "error"
          ? "error"
          : "";
  const valueDim = value === "—" || value === null || value === undefined;
  return (
    <div className={`metric ${statusClass}`}>
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${valueDim ? "dim" : ""}`}>
        {valueDim ? "—" : value}
        {!valueDim && unit && <span className="metric-unit">{unit}</span>}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
      {pill && (
        <div className={`metric-pill ${pill.variant ?? ""}`}>{pill.text}</div>
      )}
      {children}
    </div>
  );
}
