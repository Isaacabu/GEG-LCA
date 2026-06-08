import { useEffect, useMemo, useRef, useState } from "react";

function useImageOk(src: string): boolean | null {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    const im = new Image();
    im.onload = () => setOk(true);
    im.onerror = () => setOk(false);
    im.src = src;
  }, [src]);
  return ok;
}

type Spot = { x: number; y: number; size: number; rotate: number; delay: number };
function spots(): Spot[] {
  return [
    { x: 8, y: 14, size: 72, rotate: -6, delay: 0 },
    { x: 86, y: 18, size: 88, rotate: 4, delay: 120 },
    { x: 12, y: 72, size: 96, rotate: 8, delay: 240 },
    { x: 78, y: 64, size: 64, rotate: -10, delay: 60 },
    { x: 46, y: 8, size: 56, rotate: 0, delay: 180 },
    { x: 52, y: 88, size: 72, rotate: -4, delay: 300 },
  ];
}

const CELLS = [
  [0, 0], [1, 0], [2, 0], [3, 0],
  [0, 1], [1, 1], [2, 1], [3, 1],
];

export function FloatingHudIcons() {
  const ok = useImageOk("/assets/hud-icons.png");
  const ref = useRef<HTMLDivElement>(null);
  const [p, setP] = useState({ x: 0.5, y: 0.5 });
  const list = useMemo(() => spots(), []);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      setP({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    };
    window.addEventListener("mousemove", onMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  if (ok === null) return null;

  return (
    <div className="hud-bg" ref={ref} aria-hidden>
      {list.map((s, i) => {
        const dx = (p.x - 0.5) * 14;
        const dy = (p.y - 0.5) * 14;
        const t = `translate(${dx}px, ${dy}px) rotate(${s.rotate}deg)`;
        if (ok) {
          const [cx, cy] = CELLS[i % CELLS.length];
          return (
            <div
              key={i}
              className="hud-icon"
              style={{
                left: `${s.x}%`, top: `${s.y}%`,
                width: s.size, height: s.size, transform: t,
                backgroundImage: "url(/assets/hud-icons.png)",
                backgroundSize: `${s.size * 4}px ${s.size * 3}px`,
                backgroundPosition: `${-cx * s.size}px ${-cy * s.size}px`,
                transitionDelay: `${s.delay}ms`,
              }}
            />
          );
        }
        return (
          <svg
            key={i}
            className="hud-icon"
            style={{
              left: `${s.x}%`, top: `${s.y}%`,
              width: s.size, height: s.size, transform: t,
              transitionDelay: `${s.delay}ms`,
            }}
            viewBox="0 0 100 100" fill="none"
          >
            <circle cx="50" cy="50" r="36" stroke="#22d3ee" strokeWidth="1.4" />
            <path d="M30 60 L50 30 L70 60 Z" stroke="#22d3ee" strokeWidth="1.4" />
            <path d="M30 60 H70" stroke="#f6b94b" strokeWidth="1.4" />
          </svg>
        );
      })}
    </div>
  );
}
