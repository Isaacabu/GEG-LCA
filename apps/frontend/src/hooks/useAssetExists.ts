import { useEffect, useState } from "react";

// HEAD-Probe for a public asset. Returns true once we have evidence the file
// exists, false if it 404s. While we don't know, returns null.
export function useAssetExists(url: string): boolean | null {
  const [state, setState] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    fetch(url, { method: "HEAD" })
      .then((r) => alive && setState(r.ok))
      .catch(() => alive && setState(false));
    return () => {
      alive = false;
    };
  }, [url]);
  return state;
}
