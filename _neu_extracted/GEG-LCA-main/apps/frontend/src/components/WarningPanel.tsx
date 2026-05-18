export function WarningPanel({
  title,
  items,
}: {
  title?: string;
  items: string[];
}) {
  if (!items || items.length === 0) return null;
  return (
    <div className="warning-panel">
      <strong>{title ?? "Hinweise"}</strong>
      <ul>
        {items.map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ul>
    </div>
  );
}
