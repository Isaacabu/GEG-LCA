import { useEffect, useState } from "react";
import type {
  EnvelopeRequest,
  EnvelopeResult,
  HeatingDemandResult,
} from "@geg/shared";
import { api } from "../api/client.js";
import type { BuildingStore } from "./useBuildingStore.js";

export function buildEnvelopeRequest(store: BuildingStore): EnvelopeRequest {
  return {
    buildingGeometry: store.geometry,
    wallOrientations: store.wallOrientations,
    externalWallConstructionId: store.externalWallConstructionId,
    wallExtras: store.wallExtras,
    floors: store.floors,
    roof: store.roof,
    windows: store.windows,
    doors: store.doors,
  };
}

export function useEnvelopeCalc(store: BuildingStore) {
  const [envelope, setEnvelope] = useState<EnvelopeResult | null>(null);
  const [heating, setHeating] = useState<HeatingDemandResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    const hasOverride =
      store.wallExtras?.uValueOverrideWm2K !== undefined &&
      store.wallExtras.uValueOverrideWm2K > 0;
    if (!store.externalWallConstructionId && !hasOverride) {
      setEnvelope(null);
      setHeating(null);
      return;
    }
    const handle = window.setTimeout(() => {
      api
        .calcHeatingDemand({
          envelopeRequest: buildEnvelopeRequest(store),
          ventilation: store.ventilation,
          heating: store.heating,
          hotWater: store.hotWater,
          distribution: store.distribution,
          pv: store.pv,
          referenceAreaM2: store.referenceArea,
        })
        .then((r) => {
          if (cancelled) return;
          setEnvelope(r.envelope);
          setHeating(r.heating);
        })
        .catch((e) => {
          if (cancelled) return;
          setEnvelope(null);
          setHeating(null);
          setError(e instanceof Error ? e.message : String(e));
        });
    }, 250);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [
    store.geometry,
    store.wallOrientations,
    store.externalWallConstructionId,
    store.wallExtras,
    store.windows,
    store.doors,
    store.floors,
    store.roof,
    store.ventilation,
    store.heating,
    store.hotWater,
    store.distribution,
    store.pv,
    store.referenceArea,
  ]);

  return { envelope, heating, error };
}
