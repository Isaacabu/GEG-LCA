import type { ReactNode } from "react";

export function GlassCard({
  title,
  eyebrow,
  right,
  children,
}: {
  title?: string;
  eyebrow?: string;
  right?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="glass section">
      {(title || eyebrow || right) && (
        <div className="section-header">
          <div>
            {eyebrow && (
              <div className="label-row">
                <span className="dot" />
                {eyebrow}
              </div>
            )}
            {title && <h2 style={{ marginTop: 8 }}>{title}</h2>}
          </div>
          <div>{right}</div>
        </div>
      )}
      {children}
    </section>
  );
}
