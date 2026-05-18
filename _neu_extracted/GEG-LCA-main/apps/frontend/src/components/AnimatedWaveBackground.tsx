import { useEffect, useState } from "react";

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

export function AnimatedWaveBackground() {
  const ok = useImageOk("/assets/wave-bg.png");
  if (ok) {
    return (
      <div
        className="wave-bg"
        aria-hidden
        style={{
          backgroundImage: `url(/assets/wave-bg.png)`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          opacity: 0.55,
          mixBlendMode: "screen",
        }}
      />
    );
  }
  return (
    <div className="wave-bg" aria-hidden>
      <svg viewBox="0 0 1440 800" preserveAspectRatio="none">
        <defs>
          <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0" />
            <stop offset="50%" stopColor="#22d3ee" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f6b94b" stopOpacity="0" />
            <stop offset="50%" stopColor="#f6b94b" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#f6b94b" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d="M0 480 Q 360 380 720 460 T 1440 440 L 1440 800 L 0 800 Z" fill="url(#g1)">
          <animate attributeName="d" dur="14s" repeatCount="indefinite"
            values="M0 480 Q 360 380 720 460 T 1440 440 L 1440 800 L 0 800 Z;
                    M0 460 Q 360 520 720 420 T 1440 480 L 1440 800 L 0 800 Z;
                    M0 480 Q 360 380 720 460 T 1440 440 L 1440 800 L 0 800 Z" />
        </path>
        <path d="M0 560 Q 360 480 720 540 T 1440 520 L 1440 800 L 0 800 Z" fill="url(#g2)">
          <animate attributeName="d" dur="18s" repeatCount="indefinite"
            values="M0 560 Q 360 480 720 540 T 1440 520 L 1440 800 L 0 800 Z;
                    M0 540 Q 360 600 720 500 T 1440 560 L 1440 800 L 0 800 Z;
                    M0 560 Q 360 480 720 540 T 1440 520 L 1440 800 L 0 800 Z" />
        </path>
      </svg>
    </div>
  );
}
