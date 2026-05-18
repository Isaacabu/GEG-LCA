import type {
  Construction,
  DoorItem,
  DoorResult,
  EnvelopeRequest,
  EnvelopeResult,
  FloorItem,
  FloorResult,
  Orientation,
  RoofInput,
  RoofResult,
  WindowItem,
  WindowResult,
} from "../types/index.js";
import {
  calculateEffectiveApertureAreaM2,
  calculateUValue,
  calculateWallResult,
  calculateWindowSolarGainKWhA,
  correctionFactorFor,
  floorPlateAreaM2,
  windowAreaM2,
} from "./buildingPhysics.js";

export function calculateWindowResult(w: WindowItem): WindowResult {
  const area = windowAreaM2(w);
  const aEff = calculateEffectiveApertureAreaM2(w);
  const h = area * w.uValueWm2K;
  const solarGain = calculateWindowSolarGainKWhA(w);
  const messages: string[] = [];
  if (!(w.uValueWm2K > 0)) messages.push("U-Wert Fenster fehlt.");
  if (w.gValue < 0 || w.gValue > 1) messages.push("g-Wert ausserhalb 0..1.");
  return {
    id: w.id,
    name: w.name,
    orientation: w.orientation,
    areaM2: area,
    uValueWm2K: w.uValueWm2K,
    hTransmissionWK: h,
    effectiveApertureAreaM2: aEff,
    solarGainKWhA: solarGain,
    messages,
  };
}

export function calculateDoorResult(d: DoorItem): DoorResult {
  const area =
    Math.max(0, d.count) * Math.max(0, d.widthM) * Math.max(0, d.heightM);
  const fx = correctionFactorFor(d.boundaryType);
  const messages: string[] = [];
  if (!(d.uValueWm2K > 0)) messages.push("U-Wert Tuer fehlt.");
  if (d.sealCondition === "noSeal" || d.sealCondition === "veryLeaky") {
    messages.push("Tuer schlecht abgedichtet - zusaetzliche Luftleckage moeglich.");
  }
  if (d.boundaryType === "none") {
    return {
      id: d.id,
      name: d.name,
      orientation: d.orientation,
      boundaryType: d.boundaryType,
      areaM2: area,
      uValueWm2K: d.uValueWm2K,
      correctionFactor: fx,
      hTransmissionWK: null,
      status: "ignored",
      messages: [...messages, "Tuer als ignoriert markiert."],
    };
  }
  if (d.boundaryType === "heatedRoom") {
    return {
      id: d.id,
      name: d.name,
      orientation: d.orientation,
      boundaryType: d.boundaryType,
      areaM2: area,
      uValueWm2K: d.uValueWm2K,
      correctionFactor: 0,
      hTransmissionWK: 0,
      status: "ignored",
      messages: [...messages, "Tuer gegen beheizten Raum: kein H-Wert."],
    };
  }
  if (!(d.uValueWm2K > 0)) {
    return {
      id: d.id,
      name: d.name,
      orientation: d.orientation,
      boundaryType: d.boundaryType,
      areaM2: area,
      uValueWm2K: d.uValueWm2K,
      correctionFactor: fx,
      hTransmissionWK: null,
      status: "incomplete",
      messages,
    };
  }
  return {
    id: d.id,
    name: d.name,
    orientation: d.orientation,
    boundaryType: d.boundaryType,
    areaM2: area,
    uValueWm2K: d.uValueWm2K,
    correctionFactor: fx,
    hTransmissionWK: area * d.uValueWm2K * fx,
    status: "complete",
    messages,
  };
}

export function calculateFloorResult(
  input: FloorItem,
  resolveConstruction: (id: string) => Construction | undefined,
  autoAreaM2: number,
): FloorResult {
  const area = input.autoFromGeometry ? autoAreaM2 : input.areaM2;
  const messages: string[] = [];

  if (!input.enabled) {
    return {
      id: input.id,
      name: input.name,
      role: input.role,
      enabled: false,
      areaM2: area,
      boundaryType: input.boundaryType,
      uValueWm2K: null,
      correctionFactor: correctionFactorFor(input.boundaryType),
      hTransmissionWK: null,
      status: "ignored",
      messages: ["Bauteil deaktiviert (z. B. Dachgeschoss ungenutzt)."],
    };
  }

  // Manual override has priority.
  if (input.uValueOverrideWm2K !== undefined && input.uValueOverrideWm2K > 0) {
    const fx = correctionFactorFor(input.boundaryType);
    return {
      id: input.id,
      name: input.name,
      role: input.role,
      enabled: true,
      areaM2: area,
      boundaryType: input.boundaryType,
      uValueWm2K: input.uValueOverrideWm2K,
      correctionFactor: fx,
      hTransmissionWK: area * input.uValueOverrideWm2K * fx,
      status: "complete",
      messages: [...messages, "U-Wert manuell uebersteuert."],
    };
  }

  if (!input.constructionId) {
    return {
      id: input.id,
      name: input.name,
      role: input.role,
      enabled: true,
      areaM2: area,
      boundaryType: input.boundaryType,
      uValueWm2K: null,
      correctionFactor: correctionFactorFor(input.boundaryType),
      hTransmissionWK: null,
      status: "incomplete",
      messages: [...messages, "Bodenaufbau fehlt: U-Wert nicht berechenbar."],
    };
  }
  const c = resolveConstruction(input.constructionId);
  if (!c) {
    return {
      id: input.id,
      name: input.name,
      role: input.role,
      enabled: true,
      areaM2: area,
      boundaryType: input.boundaryType,
      uValueWm2K: null,
      correctionFactor: correctionFactorFor(input.boundaryType),
      hTransmissionWK: null,
      status: "error",
      messages: [`Bodenkonstruktion ${input.constructionId} nicht gefunden.`],
    };
  }
  try {
    const u = calculateUValue(c);
    const fx = correctionFactorFor(input.boundaryType);
    return {
      id: input.id,
      name: input.name,
      role: input.role,
      enabled: true,
      areaM2: area,
      boundaryType: input.boundaryType,
      uValueWm2K: u.uValueWm2K,
      correctionFactor: fx,
      hTransmissionWK: area * u.uValueWm2K * fx,
      status: "complete",
      messages: [...messages, ...u.warnings],
    };
  } catch (err) {
    return {
      id: input.id,
      name: input.name,
      role: input.role,
      enabled: true,
      areaM2: area,
      boundaryType: input.boundaryType,
      uValueWm2K: null,
      correctionFactor: correctionFactorFor(input.boundaryType),
      hTransmissionWK: null,
      status: "error",
      messages: [err instanceof Error ? err.message : String(err)],
    };
  }
}

export function calculateRoofResult(
  input: RoofInput | undefined,
  resolveConstruction: (id: string) => Construction | undefined,
  autoAreaM2: number,
): RoofResult | null {
  if (!input) return null;
  const area = input.autoFromGeometry ? autoAreaM2 : input.areaM2;
  const messages: string[] = [];

  if (!input.enabled) {
    return {
      roofType: input.roofType,
      calcMode: input.calcMode,
      enabled: false,
      areaM2: area,
      insulated: input.insulated,
      uValueWm2K: null,
      hTransmissionWK: null,
      status: "ignored",
      messages: ["Dach deaktiviert (z. B. ungenutzt). Verwende oberste Geschossdecke."],
    };
  }

  if (!input.insulated) {
    messages.push("Dach nicht isoliert - hoher Waermeverlust wahrscheinlich.");
  }

  // Override wins.
  if (input.uValueOverrideWm2K !== undefined && input.uValueOverrideWm2K > 0) {
    return {
      roofType: input.roofType,
      calcMode: input.calcMode,
      enabled: true,
      areaM2: area,
      insulated: input.insulated,
      uValueWm2K: input.uValueOverrideWm2K,
      hTransmissionWK: area * input.uValueOverrideWm2K * 1.0,
      status: "complete",
      messages: [...messages, "U-Wert manuell uebersteuert."],
    };
  }

  if (!input.constructionId) {
    return {
      roofType: input.roofType,
      calcMode: input.calcMode,
      enabled: true,
      areaM2: area,
      insulated: input.insulated,
      uValueWm2K: null,
      hTransmissionWK: null,
      status: "incomplete",
      messages: [...messages, "Dachaufbau fehlt: U-Wert nicht berechenbar."],
    };
  }
  const c = resolveConstruction(input.constructionId);
  if (!c) {
    return {
      roofType: input.roofType,
      calcMode: input.calcMode,
      enabled: true,
      areaM2: area,
      insulated: input.insulated,
      uValueWm2K: null,
      hTransmissionWK: null,
      status: "error",
      messages: [...messages, `Dachkonstruktion ${input.constructionId} nicht gefunden.`],
    };
  }
  try {
    const u = calculateUValue(c);
    return {
      roofType: input.roofType,
      calcMode: input.calcMode,
      enabled: true,
      areaM2: area,
      insulated: input.insulated,
      uValueWm2K: u.uValueWm2K,
      hTransmissionWK: area * u.uValueWm2K * 1.0,
      status: "complete",
      messages: [...messages, ...u.warnings],
    };
  } catch (err) {
    return {
      roofType: input.roofType,
      calcMode: input.calcMode,
      enabled: true,
      areaM2: area,
      insulated: input.insulated,
      uValueWm2K: null,
      hTransmissionWK: null,
      status: "error",
      messages: [...messages, err instanceof Error ? err.message : String(err)],
    };
  }
}

export function calculateEnvelope(
  req: EnvelopeRequest,
  externalWallConstruction: Construction | null,
  resolveConstruction: (id: string) => Construction | undefined,
): EnvelopeResult {
  const warnings: string[] = [];

  let externalWallU: number | null = null;
  let method: "layers" | "fixedUValue" | "override" | null = null;

  // Manual override on the wall has the highest priority.
  if (req.wallExtras?.uValueOverrideWm2K && req.wallExtras.uValueOverrideWm2K > 0) {
    externalWallU = req.wallExtras.uValueOverrideWm2K;
    method = "override";
  } else if (!externalWallConstruction) {
    warnings.push("Kein Aussenwandaufbau gewaehlt: U-Wert nicht berechenbar.");
  } else if (externalWallConstruction.elementType !== "externalWall") {
    warnings.push(
      `Gewaehltes Bauteil "${externalWallConstruction.name}" ist keine Aussenwand.`,
    );
  } else {
    try {
      const u = calculateUValue(externalWallConstruction);
      externalWallU = u.uValueWm2K;
      method = u.method;
      warnings.push(...u.warnings);
    } catch (err) {
      warnings.push(
        err instanceof Error ? err.message : "U-Wert-Berechnung fehlgeschlagen.",
      );
    }
  }

  // Pauschaler Waermebrueckenzuschlag wirkt sich nur aus, wenn ein U-Wert da ist.
  const thermalBridge = req.wallExtras?.thermalBridgeDeltaUWm2K ?? 0;
  const effectiveWallU =
    externalWallU !== null && thermalBridge > 0
      ? externalWallU + thermalBridge
      : externalWallU;
  if (thermalBridge > 0) {
    warnings.push(
      `Waermebrueckenzuschlag DeltaU_WB = ${thermalBridge.toFixed(3)} W/(m^2*K) auf Wand-U addiert.`,
    );
  }

  const wallResults = req.wallOrientations.map((w) =>
    calculateWallResult(w, effectiveWallU),
  );
  const wallsTotalWK = wallResults.reduce(
    (s, w) => s + (w.hTransmissionWK ?? 0),
    0,
  );

  const windowResults = (req.windows ?? []).map(calculateWindowResult);
  const windowsTotalWK = windowResults.reduce(
    (s, w) => s + (w.hTransmissionWK ?? 0),
    0,
  );

  const doorResults = (req.doors ?? []).map(calculateDoorResult);
  const doorsTotalWK = doorResults.reduce(
    (s, d) => s + (d.hTransmissionWK ?? 0),
    0,
  );

  const planArea = floorPlateAreaM2(req.buildingGeometry);
  const floors: FloorResult[] = (req.floors ?? []).map((f) =>
    calculateFloorResult(f, resolveConstruction, planArea),
  );
  const floorsTotalWK = floors.reduce(
    (s, f) => s + (f.hTransmissionWK ?? 0),
    0,
  );
  const roof = calculateRoofResult(req.roof, resolveConstruction, planArea);

  const solarGainsByOrientation: Partial<Record<Orientation, number>> = {};
  for (const w of windowResults) {
    solarGainsByOrientation[w.orientation] =
      (solarGainsByOrientation[w.orientation] ?? 0) + w.solarGainKWhA;
  }
  const solarGainsTotalKWhA = Object.values(solarGainsByOrientation).reduce(
    (s, v) => s + (v ?? 0),
    0,
  );

  const hTTotalWK =
    wallsTotalWK +
    windowsTotalWK +
    doorsTotalWK +
    floorsTotalWK +
    (roof?.hTransmissionWK ?? 0);

  return {
    externalWallUValueWm2K: effectiveWallU,
    externalWallUValueMethod: method,
    wallResultsByOrientation: wallResults,
    wallsTotalWK,
    windowResults,
    windowsTotalWK,
    doorResults,
    doorsTotalWK,
    floors,
    floorsTotalWK,
    roof,
    solarGainsByOrientation,
    solarGainsTotalKWhA,
    hTTotalWK,
    warnings,
  };
}
