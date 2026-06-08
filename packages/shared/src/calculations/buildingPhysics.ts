import type {
  BoundaryType,
  Construction,
  ConstructionLayer,
  ElementType,
  Orientation,
  WallOrientation,
  UValueResult,
  WallOrientationInput,
  WallOrientationResult,
  WindowItem,
  BuildingGeometry,
} from "../types/index.js";

// Surface thermal resistances per DIN EN ISO 6946 (vereinfachte Projektwerte).
export const SURFACE_RESISTANCES: Record<
  ElementType,
  { rsi: number; rse: number }
> = {
  externalWall: { rsi: 0.13, rse: 0.04 },
  roof: { rsi: 0.1, rse: 0.04 },
  floor: { rsi: 0.17, rse: 0.04 },
  window: { rsi: 0.13, rse: 0.04 },
  door: { rsi: 0.13, rse: 0.04 },
};

// Vereinfachte Projekt-Korrekturfaktoren Fx.
export const BOUNDARY_CORRECTION_FACTORS: Record<BoundaryType, number> = {
  outside: 1.0,
  heatedRoom: 0.0,
  unheatedRoom: 0.5,
  corridor: 0.5,
  basement: 0.6,
  ground: 0.6,
  none: 0.0,
};

export function correctionFactorFor(boundary: BoundaryType): number {
  return BOUNDARY_CORRECTION_FACTORS[boundary];
}

// Vereinfachte Globalstrahlung pro Orientierung (kWh/m^2*a) ueber die
// Heizperiode. Projektwerte fuer Deutschland. Horizontal = Dachfenster.
export const SOLAR_RADIATION_VERTICAL_KWHM2A: Record<Orientation, number> = {
  north: 100,
  northeast: 140,
  east: 175,
  southeast: 280,
  south: 350,
  southwest: 280,
  west: 175,
  northwest: 140,
  horizontal: 460,
};

// Fenster / Tueren werden bei der Wandflaechen-Abzugslogik auf eine der vier
// Hauptwaende gemappt. Zwischenrichtungen werden naeher gerichtet zugeordnet,
// horizontal (Dachfenster) erzeugt keinen Wandabzug.
export function mapToWall(o: Orientation): WallOrientation | null {
  switch (o) {
    case "north":
    case "northeast":
      return "north";
    case "east":
    case "southeast":
      return "east";
    case "south":
    case "southwest":
      return "south";
    case "west":
    case "northwest":
      return "west";
    case "horizontal":
      return null;
  }
}

export const ORIENTATION_LABELS: Record<Orientation, string> = {
  north: "Nord",
  northeast: "Nord-Ost",
  east: "Ost",
  southeast: "Sued-Ost",
  south: "Sued",
  southwest: "Sued-West",
  west: "West",
  northwest: "Nord-West",
  horizontal: "horizontal / Dachfenster",
};

export const WALL_ORIENTATION_LABELS: Record<WallOrientation, string> = {
  north: "Nord",
  east: "Ost",
  south: "Sued",
  west: "West",
};

// Vereinfachte Schwellen fuer die Energieampel (Projektwerte).
export const ENERGY_TRAFFIC_LIGHT_THRESHOLDS_KWHM2A = {
  green: 50,
  yellow: 100,
  orange: 150,
};

// Heizperiode in Deutschland (vereinfacht).
export const HEATING_PERIOD_GT_KKHA = 84; // kKh/a (Gradtagszahl, Projektwert)

// Volumetric heat capacity of air at 20 °C.
export const AIR_CP_RHO_WH_M3K = 0.34;

export function calculateLayerResistance(layer: ConstructionLayer): {
  rLayer: number;
  warnings: string[];
} {
  const warnings: string[] = [];
  if (!(layer.thicknessM > 0)) {
    warnings.push(
      `Schicht "${layer.materialName}": Dicke ${layer.thicknessM} m ist ungueltig.`,
    );
  }
  if (!(layer.lambdaWmK > 0)) {
    warnings.push(
      `Schicht "${layer.materialName}": Lambda ${layer.lambdaWmK} W/(m*K) ist ungueltig.`,
    );
  }
  if (warnings.length > 0) {
    return { rLayer: NaN, warnings };
  }
  return { rLayer: layer.thicknessM / layer.lambdaWmK, warnings };
}

export function calculateUValue(construction: Construction): UValueResult {
  const surface = SURFACE_RESISTANCES[construction.elementType];

  if (construction.calculationMode === "fixedUValue") {
    if (
      construction.fixedUValueWm2K === undefined ||
      !(construction.fixedUValueWm2K > 0)
    ) {
      throw new Error(
        `Bauteil "${construction.name}" hat keinen gueltigen festen U-Wert.`,
      );
    }
    return {
      uValueWm2K: construction.fixedUValueWm2K,
      method: "fixedUValue",
      layers: [],
      rTotal: 1 / construction.fixedUValueWm2K,
      rsi: surface.rsi,
      rse: surface.rse,
      warnings: [],
    };
  }

  if (!construction.layers || construction.layers.length === 0) {
    throw new Error(
      `Bauteil "${construction.name}" hat keine Schichten und keinen festen U-Wert.`,
    );
  }

  const warnings: string[] = [];
  const layerDetails: UValueResult["layers"] = [];
  let rLayersSum = 0;

  for (const layer of construction.layers) {
    const { rLayer, warnings: layerWarnings } =
      calculateLayerResistance(layer);
    warnings.push(...layerWarnings);
    if (!Number.isFinite(rLayer)) {
      throw new Error(
        `Bauteil "${construction.name}" enthaelt ungueltige Schicht "${layer.materialName}".`,
      );
    }
    rLayersSum += rLayer;
    layerDetails.push({
      materialName: layer.materialName,
      thicknessM: layer.thicknessM,
      lambdaWmK: layer.lambdaWmK,
      rLayer,
    });
  }

  const rTotal = surface.rsi + rLayersSum + surface.rse;
  if (!(rTotal > 0)) {
    throw new Error(
      `Bauteil "${construction.name}": R_total <= 0, U-Wert nicht definiert.`,
    );
  }

  return {
    uValueWm2K: 1 / rTotal,
    method: "layers",
    layers: layerDetails,
    rTotal,
    rsi: surface.rsi,
    rse: surface.rse,
    warnings,
  };
}

export function calculateNetArea(input: {
  grossAreaM2: number;
  windowAreaM2: number;
  doorAreaM2: number;
}): { netAreaM2: number; warnings: string[] } {
  const warnings: string[] = [];
  const sumOpenings = input.windowAreaM2 + input.doorAreaM2;
  if (sumOpenings > input.grossAreaM2) {
    warnings.push(
      `Fenster- und Tuerflaeche (${sumOpenings.toFixed(2)} m^2) groesser als Bruttoflaeche (${input.grossAreaM2.toFixed(2)} m^2).`,
    );
    return { netAreaM2: 0, warnings };
  }
  return { netAreaM2: input.grossAreaM2 - sumOpenings, warnings };
}

export function calculateTransmissionLoss(
  areaM2: number,
  uValueWm2K: number | null,
  correctionFactor: number,
): number | null {
  if (uValueWm2K === null || !Number.isFinite(uValueWm2K)) return null;
  if (!Number.isFinite(areaM2) || areaM2 < 0) return null;
  if (!Number.isFinite(correctionFactor)) return null;
  return areaM2 * uValueWm2K * correctionFactor;
}

export function calculateWallResult(
  input: WallOrientationInput,
  externalWallUValueWm2K: number | null,
): WallOrientationResult {
  const messages: string[] = [];
  const { netAreaM2, warnings } = calculateNetArea(input);
  messages.push(...warnings);

  const correctionFactor = correctionFactorFor(input.boundaryType);

  if (input.boundaryType === "none") {
    return {
      orientation: input.orientation,
      grossAreaM2: input.grossAreaM2,
      windowAreaM2: input.windowAreaM2,
      doorAreaM2: input.doorAreaM2,
      netAreaM2,
      boundaryType: input.boundaryType,
      correctionFactor,
      uValueWm2K: null,
      hTransmissionWK: null,
      status: "ignored",
      messages: [...messages, "Orientierung als nicht relevant markiert."],
    };
  }

  if (input.boundaryType === "heatedRoom") {
    return {
      orientation: input.orientation,
      grossAreaM2: input.grossAreaM2,
      windowAreaM2: input.windowAreaM2,
      doorAreaM2: input.doorAreaM2,
      netAreaM2,
      boundaryType: input.boundaryType,
      correctionFactor: 0.0,
      uValueWm2K: externalWallUValueWm2K,
      hTransmissionWK: 0,
      status: "ignored",
      messages: [
        ...messages,
        "Innenwand gegen beheizten Raum: kein Transmissionsverlust angesetzt.",
      ],
    };
  }

  if (externalWallUValueWm2K === null) {
    return {
      orientation: input.orientation,
      grossAreaM2: input.grossAreaM2,
      windowAreaM2: input.windowAreaM2,
      doorAreaM2: input.doorAreaM2,
      netAreaM2,
      boundaryType: input.boundaryType,
      correctionFactor,
      uValueWm2K: null,
      hTransmissionWK: null,
      status: "incomplete",
      messages: [
        ...messages,
        "Aussenwandaufbau fehlt: U-Wert nicht berechenbar.",
      ],
    };
  }

  const h = calculateTransmissionLoss(
    netAreaM2,
    externalWallUValueWm2K,
    correctionFactor,
  );

  return {
    orientation: input.orientation,
    grossAreaM2: input.grossAreaM2,
    windowAreaM2: input.windowAreaM2,
    doorAreaM2: input.doorAreaM2,
    netAreaM2,
    boundaryType: input.boundaryType,
    correctionFactor,
    uValueWm2K: externalWallUValueWm2K,
    hTransmissionWK: h,
    status: h === null ? "error" : "complete",
    messages,
  };
}

// Building geometry helpers ---------------------------------------------------

export function totalHeightM(g: BuildingGeometry): number {
  return g.floors * g.storyHeightM;
}

export function deriveWallAreasFromGeometry(
  g: BuildingGeometry,
): Record<WallOrientation, number> {
  const h = totalHeightM(g);
  return {
    north: g.lengthM * h,
    south: g.lengthM * h,
    east: g.widthM * h,
    west: g.widthM * h,
  };
}

export function floorPlateAreaM2(g: BuildingGeometry): number {
  return g.lengthM * g.widthM;
}

export function heatedVolumeM3(g: BuildingGeometry): number {
  return floorPlateAreaM2(g) * totalHeightM(g);
}

// Reference area (vereinfacht). Wenn der Nutzer keinen Wert setzt, nehmen wir
// die Summe der Geschossflaechen.
export function referenceAreaFromGeometryM2(g: BuildingGeometry): number {
  return floorPlateAreaM2(g) * g.floors;
}

// Windows --------------------------------------------------------------------

export function windowAreaM2(w: WindowItem): number {
  return Math.max(0, w.count) * Math.max(0, w.widthM) * Math.max(0, w.heightM);
}

// A_eff = A * g * F_F * F_S * F_dirt * F_w
export function calculateEffectiveApertureAreaM2(w: WindowItem): number {
  const a = windowAreaM2(w);
  const factor =
    clamp01(w.gValue) *
    clamp01(w.frameFactor) *
    clamp01(w.shadingFactor) *
    clamp01(w.dirtFactor) *
    clamp01(w.nonPerpFactor);
  return a * factor;
}

function clamp01(x: number): number {
  if (!Number.isFinite(x)) return 0;
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}

export function calculateWindowSolarGainKWhA(w: WindowItem): number {
  return (
    calculateEffectiveApertureAreaM2(w) *
    SOLAR_RADIATION_VERTICAL_KWHM2A[w.orientation]
  );
}

// Aggregiert Fenster-Flaeche pro Wand (4 Hauptrichtungen). Zwischenrichtungen
// werden ueber mapToWall gemappt, Dachfenster ignoriert.
export function totalWindowAreaByWall(
  windows: WindowItem[],
): Record<WallOrientation, number> {
  const result: Record<WallOrientation, number> = {
    north: 0,
    south: 0,
    east: 0,
    west: 0,
  };
  for (const w of windows) {
    const wall = mapToWall(w.orientation);
    if (wall) result[wall] += windowAreaM2(w);
  }
  return result;
}

export function totalDoorAreaByWall<
  T extends { orientation: Orientation; count: number; widthM: number; heightM: number },
>(doors: T[]): Record<WallOrientation, number> {
  const result: Record<WallOrientation, number> = {
    north: 0,
    south: 0,
    east: 0,
    west: 0,
  };
  for (const d of doors) {
    const wall = mapToWall(d.orientation);
    if (!wall) continue;
    result[wall] +=
      Math.max(0, d.count) * Math.max(0, d.widthM) * Math.max(0, d.heightM);
  }
  return result;
}

// Traffic light --------------------------------------------------------------

export function energyTrafficLight(
  specificKWhM2A: number,
): "green" | "yellow" | "orange" | "red" {
  const t = ENERGY_TRAFFIC_LIGHT_THRESHOLDS_KWHM2A;
  if (specificKWhM2A < t.green) return "green";
  if (specificKWhM2A < t.yellow) return "yellow";
  if (specificKWhM2A < t.orange) return "orange";
  return "red";
}

// Ventilation H_V = n * V * c_p * rho
export function calculateVentilationConductanceWK(
  airChangeRatePerH: number,
  heatedVolumeM3: number,
): number {
  return airChangeRatePerH * heatedVolumeM3 * AIR_CP_RHO_WH_M3K;
}

// Heating demand (vereinfacht):
//   Q_T = H_T * G_t       in kWh/a   (H_T in W/K, G_t in kKh/a)
//   Q_V = H_V * G_t
//   Q_g = Q_S + Q_I       in kWh/a
//   Q_H,net = max(0, Q_T + Q_V - eta_gn * Q_g)
export function calculateHeatingLossKWhA(hWK: number): number {
  return hWK * HEATING_PERIOD_GT_KKHA;
}

// Utilisation factor for gains, simplified bracket approach.
export function gainUtilisationFactor(
  lossesKWhA: number,
  gainsKWhA: number,
): number {
  if (gainsKWhA <= 0) return 1;
  const gamma = gainsKWhA / Math.max(lossesKWhA, 1e-9);
  // DIN V 4108-6 / 18599 utilisation factor for inertia ~ medium:
  //   eta = (1 - gamma^a) / (1 - gamma^(a+1)) with a ~ 1 + tau/15h
  // For a project-level approximation we set a = 2.
  const a = 2;
  if (Math.abs(gamma - 1) < 1e-6) return a / (a + 1);
  return (1 - Math.pow(gamma, a)) / (1 - Math.pow(gamma, a + 1));
}

export function internalGainsKWhA(referenceAreaM2: number): number {
  // 22 kWh/(m^2 a) als vereinfachter Pauschalwert fuer Wohnnutzung.
  return 22 * Math.max(0, referenceAreaM2);
}
