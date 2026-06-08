import { useState, type ReactNode } from "react";

export type AccordionItemSpec = {
  id: string;
  eyebrow?: string;
  title: string;
  meta?: ReactNode;
  body: ReactNode;
  defaultOpen?: boolean;
};

export function Accordion({ items }: { items: AccordionItemSpec[] }) {
  const [openId, setOpenId] = useState<string>(
    () => items.find((i) => i.defaultOpen)?.id ?? items[0]?.id ?? "",
  );
  return (
    <div className="accordion">
      {items.map((it) => {
        const open = it.id === openId;
        return (
          <div key={it.id} className={`acc-item ${open ? "open" : ""}`}>
            <button
              type="button"
              className="acc-trigger"
              onClick={() => setOpenId(open ? "" : it.id)}
            >
              <div>
                {it.eyebrow && <span className="acc-eyebrow">{it.eyebrow}</span>}
                <span className="acc-title">{it.title}</span>
              </div>
              <div className="acc-meta">
                {it.meta}
                <span className="acc-chev" />
              </div>
            </button>
            {open && <div className="acc-body">{it.body}</div>}
          </div>
        );
      })}
    </div>
  );
}
