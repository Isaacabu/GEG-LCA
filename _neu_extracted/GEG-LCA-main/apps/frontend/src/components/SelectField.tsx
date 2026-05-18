export type Option<T extends string = string> = { value: T; label: string };

export function SelectField<T extends string = string>({
  label,
  value,
  options,
  onChange,
  placeholder,
}: {
  label: string;
  value: T | "";
  options: Option<T>[];
  onChange: (v: T) => void;
  placeholder?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <select
        className="select"
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
      >
        {placeholder !== undefined && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
