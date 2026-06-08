import { describe, expect, it } from "vitest";
import {
  calculateEffectiveApertureAreaM2,
  calculateLayerResistance,
  calculateNetArea,
  calculateTransmissionLoss,
  calculateUValue,
  calculateVentilationConductanceWK,
  calculateWallResult,
  calculateWindowSolarGainKWhA,
  correctionFactorFor,
  deriveWallAreasFromGeometry,
  energyTrafficLight,
  gainUtilisationFactor,
  heatedVolumeM3,
  windowAreaM2,
  SOLAR_RADIATION_VERTICAL_KWHM2A,
} from "./buildingPhysics.js";
import { calculateHeatingDemand } from "./heating.js";
import { calculateEnvelope } from "./envelope.js";
import type {
  Construction,
  ConstructionLayer,
  WindowItem,
} from "../types/index.js";

const layer = (overrides: Partial<ConstructionLayer> = {}): ConstructionLayer => ({
  id: "l1",
  materialId: "m1",
  materialName: "Mat",
  thicknessM: 0.24,
  lambdaWmK: 0.12,
  order: 0,
  ...overrides,
});

const win = (overrides: Partial<WindowItem> = {}): WindowItem => ({
  id: "w1",
  name: "Fenster",
  orientation: "east",
  count: 1,
  widthM: 1,
  heightM: 1,
  type: "tiltTurn",
  glazing: "double-thermal",
  frame: "pvc",
  install: "normal",
  uValueWm2K: 1.3,
  frameShareFraction: 0.25,
  gValue: 0.6,
  frameFactor: 0.7,
  shadingKind: "none",
  shadingFactor: 0.9,
  dirtFactor: 0.9,
  nonPerpFactor: 0.9,
  ...overrides,
});

describe("calculateLayerResistance", () => {
  it("returns d/lambda for a valid layer", () => {
    const { rLayer, warnings } = calculateLayerResistance(layer());
    expect(warnings).toHaveLength(0);
    expect(rLayer).toBeCloseTo(0.24 / 0.12, 10);
  });

  it("warns when thickness is zero", () => {
    const { rLayer, warnings } = calculateLayerResistance(
      layer({ thicknessM: 0 }),
    );
    expect(Number.isNaN(rLayer)).toBe(true);
    expect(warnings.length).toBeGreaterThan(0);
  });

  it("warns when lambda is zero", () => {
    const { rLayer, warnings } = calculateLayerResistance(
      layer({ lambdaWmK: 0 }),
    );
    expect(Number.isNaN(rLayer)).toBe(true);
    expect(warnings.length).toBeGreaterThan(0);
  });
});

describe("calculateUValue (layers)", () => {
  it("single-layer external wall: R = Rsi + d/lambda + Rse", () => {
    const c: Construction = {
      id: "c1",
      name: "Test",
      elementType: "externalWall",
      calculationMode: "layers",
      layers: [layer({ thicknessM: 0.24, lambdaWmK: 0.12 })],
    };
    const result = calculateUValue(c);
    expect(result.rTotal).toBeCloseTo(2.17, 6);
    expect(result.uValueWm2K).toBeCloseTo(1 / 2.17, 6);
    expect(result.method).toBe("layers");
  });

  it("uses fixed U when calculationMode is fixedUValue", () => {
    const result = calculateUValue({
      id: "c2",
      name: "Window",
      elementType: "window",
      calculationMode: "fixedUValue",
      fixedUValueWm2K: 1.1,
    });
    expect(result.method).toBe("fixedUValue");
    expect(result.uValueWm2K).toBe(1.1);
  });

  it("throws when layers are missing", () => {
    expect(() =>
      calculateUValue({
        id: "c3",
        name: "Empty",
        elementType: "externalWall",
        calculationMode: "layers",
        layers: [],
      }),
    ).toThrow();
  });

  it("throws on invalid layer", () => {
    expect(() =>
      calculateUValue({
        id: "c4",
        name: "Broken",
        elementType: "externalWall",
        calculationMode: "layers",
        layers: [layer({ thicknessM: 0 })],
      }),
    ).toThrow();
  });
});

describe("calculateTransmissionLoss", () => {
  it("A * U * Fx", () => {
    expect(calculateTransmissionLoss(42, 0.28, 1)).toBeCloseTo(11.76, 6);
  });
  it("Fx=0 returns 0", () => {
    expect(calculateTransmissionLoss(42, 0.28, 0)).toBe(0);
  });
  it("missing U returns null", () => {
    expect(calculateTransmissionLoss(42, null, 1)).toBeNull();
  });
});

describe("calculateNetArea", () => {
  it("42 - 5 - 2 = 35", () => {
    const { netAreaM2, warnings } = calculateNetArea({
      grossAreaM2: 42,
      windowAreaM2: 5,
      doorAreaM2: 2,
    });
    expect(netAreaM2).toBe(35);
    expect(warnings).toHaveLength(0);
  });
  it("openings larger than wall -> warning and clamped to 0", () => {
    const { netAreaM2, warnings } = calculateNetArea({
      grossAreaM2: 10,
      windowAreaM2: 20,
      doorAreaM2: 0,
    });
    expect(netAreaM2).toBe(0);
    expect(warnings.length).toBeGreaterThan(0);
  });
});

describe("calculateWallResult", () => {
  it("complete for outside boundary with valid U", () => {
    const r = calculateWallResult(
      {
        orientation: "north",
        grossAreaM2: 42,
        windowAreaM2: 0,
        doorAreaM2: 0,
        boundaryType: "outside",
      },
      0.28,
    );
    expect(r.status).toBe("complete");
    expect(r.hTransmissionWK).toBeCloseTo(11.76, 6);
  });
  it("heatedRoom -> H=0, status ignored", () => {
    const r = calculateWallResult(
      {
        orientation: "north",
        grossAreaM2: 42,
        windowAreaM2: 0,
        doorAreaM2: 0,
        boundaryType: "heatedRoom",
      },
      0.28,
    );
    expect(r.status).toBe("ignored");
    expect(r.hTransmissionWK).toBe(0);
  });
  it("missing U -> incomplete and no H", () => {
    const r = calculateWallResult(
      {
        orientation: "north",
        grossAreaM2: 42,
        windowAreaM2: 0,
        doorAreaM2: 0,
        boundaryType: "outside",
      },
      null,
    );
    expect(r.status).toBe("incomplete");
    expect(r.hTransmissionWK).toBeNull();
  });
  it("unheatedRoom Fx=0.5", () => {
    expect(correctionFactorFor("unheatedRoom")).toBe(0.5);
    const r = calculateWallResult(
      {
        orientation: "east",
        grossAreaM2: 35,
        windowAreaM2: 0,
        doorAreaM2: 0,
        boundaryType: "unheatedRoom",
      },
      0.28,
    );
    expect(r.hTransmissionWK).toBeCloseTo(4.9, 6);
  });
});

describe("windowArea + A_eff", () => {
  it("Anzahl x Breite x Hoehe", () => {
    expect(windowAreaM2(win({ count: 7, widthM: 1.5, heightM: 2.17 }))).toBeCloseTo(
      22.785,
      6,
    );
  });
  it("A_eff aus dem User-Beispiel ist ~6.98 m^2 (nicht 1.00)", () => {
    const w = win({
      count: 7,
      widthM: 1.5,
      heightM: 2.17,
      gValue: 0.6,
      frameFactor: 0.7,
      shadingFactor: 0.9,
      dirtFactor: 0.9,
      nonPerpFactor: 0.9,
    });
    // 22.785 * 0.6 * 0.7 * 0.9 * 0.9 * 0.9 = 6.9763113
    expect(calculateEffectiveApertureAreaM2(w)).toBeCloseTo(6.9763, 3);
  });
  it("clamps faktoren auf 0..1", () => {
    const w = win({ gValue: 2, frameFactor: -1, shadingFactor: 0.5 });
    expect(calculateEffectiveApertureAreaM2(w)).toBe(0); // frame factor -> 0
  });
});

describe("calculateWindowSolarGain", () => {
  it("solarer Gewinn = A_eff x I_orient", () => {
    const w = win({
      orientation: "south",
      count: 1,
      widthM: 1,
      heightM: 1,
      gValue: 1,
      frameFactor: 1,
      shadingFactor: 1,
      dirtFactor: 1,
      nonPerpFactor: 1,
    });
    expect(calculateWindowSolarGainKWhA(w)).toBe(
      SOLAR_RADIATION_VERTICAL_KWHM2A.south,
    );
  });
});

describe("energyTrafficLight", () => {
  it("Schwellen", () => {
    expect(energyTrafficLight(30)).toBe("green");
    expect(energyTrafficLight(70)).toBe("yellow");
    expect(energyTrafficLight(120)).toBe("orange");
    expect(energyTrafficLight(160)).toBe("red");
  });
});

describe("calculateVentilationConductance", () => {
  it("H_V = n * V * c", () => {
    expect(calculateVentilationConductanceWK(0.5, 300)).toBeCloseTo(51, 6);
  });
});

describe("gainUtilisationFactor", () => {
  it("zwischen 0 und 1", () => {
    const e = gainUtilisationFactor(10000, 5000);
    expect(e).toBeGreaterThan(0);
    expect(e).toBeLessThan(1);
  });
  it("Gewinne 0 -> Faktor 1", () => {
    expect(gainUtilisationFactor(10000, 0)).toBe(1);
  });
});

describe("deriveWallAreasFromGeometry mit Etagen", () => {
  it("Hoehe = floors x storyHeight", () => {
    const g = { lengthM: 12, widthM: 10, floors: 2, storyHeightM: 3 };
    expect(heatedVolumeM3(g)).toBeCloseTo(12 * 10 * 6, 6);
    const a = deriveWallAreasFromGeometry(g);
    expect(a.north).toBeCloseTo(72, 6);
    expect(a.east).toBeCloseTo(60, 6);
  });
});

describe("calculateEnvelope integriert Fenster, Tueren, Dach, Boden", () => {
  const wall: Construction = {
    id: "wall",
    name: "W",
    elementType: "externalWall",
    calculationMode: "fixedUValue",
    fixedUValueWm2K: 0.28,
  };
  const roof: Construction = {
    id: "roof",
    name: "R",
    elementType: "roof",
    calculationMode: "fixedUValue",
    fixedUValueWm2K: 0.2,
  };
  const floor: Construction = {
    id: "floor",
    name: "F",
    elementType: "floor",
    calculationMode: "fixedUValue",
    fixedUValueWm2K: 0.35,
  };
  const resolver = (id: string) =>
    ({ wall, roof, floor }) [id as "wall" | "roof" | "floor"];

  it("summiert H_T aus allen Bauteilen und liefert Solarwerte", () => {
    const env = calculateEnvelope(
      {
        buildingGeometry: { lengthM: 12, widthM: 10, floors: 1, storyHeightM: 3 },
        wallOrientations: [
          { orientation: "north", grossAreaM2: 36, windowAreaM2: 0, doorAreaM2: 0, boundaryType: "outside" },
          { orientation: "south", grossAreaM2: 36, windowAreaM2: 6, doorAreaM2: 0, boundaryType: "outside" },
          { orientation: "east", grossAreaM2: 30, windowAreaM2: 0, doorAreaM2: 2.2, boundaryType: "outside" },
          { orientation: "west", grossAreaM2: 30, windowAreaM2: 0, doorAreaM2: 0, boundaryType: "outside" },
        ],
        externalWallConstructionId: "wall",
        floors: [
          {
            id: "fp1", name: "Bodenplatte", role: "groundSlab", storyIndex: 0,
            enabled: true, areaM2: 120, autoFromGeometry: true,
            boundaryType: "ground", constructionId: "floor",
            insulation: "belowSlab", floorHeating: false,
          },
        ],
        roof: {
          roofType: "flat", calcMode: "againstOutside",
          areaM2: 120, autoFromGeometry: true, enabled: true,
          insulated: true, insulationPosition: "flatRoof",
          insulationThicknessMM: 200, constructionId: "roof",
          material: "bitumen", ventilation: "none",
          dormers: [],
        },
        windows: [win({ id: "ws", orientation: "south", count: 3, widthM: 1, heightM: 2 })],
        doors: [
          {
            id: "d1",
            name: "Eingang",
            orientation: "east",
            count: 1,
            widthM: 1.1,
            heightM: 2.0,
            doorType: "entrance",
            material: "woodInsulated",
            uValueWm2K: 1.8,
            glassFractionPct: 0,
            sealCondition: "normal",
            thresholdInsulated: true,
            openingFrequency: "normal",
            boundaryType: "outside",
          },
        ],
      },
      wall,
      resolver,
    );
    expect(env.externalWallUValueWm2K).toBe(0.28);
    expect(env.windowResults[0].solarGainKWhA).toBeGreaterThan(0);
    expect(env.solarGainsByOrientation.south ?? 0).toBeGreaterThan(0);
    expect(env.solarGainsByOrientation.north ?? 0).toBe(0);
    expect(env.floors[0]?.uValueWm2K).toBe(0.35);
    expect(env.roof?.uValueWm2K).toBe(0.2);
    // sanity: hT setzt sich aus allen Teilen zusammen, > Waende allein
    expect(env.hTTotalWK).toBeGreaterThan(env.wallsTotalWK);
  });

  it("fehlender Bodenaufbau -> incomplete, kein Fake-U", () => {
    const env = calculateEnvelope(
      {
        buildingGeometry: { lengthM: 10, widthM: 10, floors: 1, storyHeightM: 3 },
        wallOrientations: [],
        externalWallConstructionId: "wall",
        floors: [
          {
            id: "fp", name: "Bodenplatte", role: "groundSlab", storyIndex: 0,
            enabled: true, areaM2: 100, autoFromGeometry: false,
            boundaryType: "ground", constructionId: null,
            insulation: "none", floorHeating: false,
          },
        ],
      },
      wall,
      resolver,
    );
    expect(env.floors[0].status).toBe("incomplete");
    expect(env.floors[0].uValueWm2K).toBeNull();
    expect(env.floors[0].hTransmissionWK).toBeNull();
  });
});

describe("calculateHeatingDemand", () => {
  it("liefert spezifischen Bedarf und Ampel", () => {
    const env = {
      hTTotalWK: 200,
      solarGainsTotalKWhA: 4000,
      externalWallUValueWm2K: 0.4,
      wallsTotalWK: 120,
      windowResults: [],
      windowsTotalWK: 40,
      doorResults: [],
      doorsTotalWK: 10,
      floors: [],
      floorsTotalWK: 15,
      roof: null,
      wallResultsByOrientation: [],
      solarGainsByOrientation: {},
      warnings: [],
      externalWallUValueMethod: "fixedUValue",
    } as any;
    const r = calculateHeatingDemand({
      envelope: env,
      ventilation: {
        kind: "windowVentilation",
        airChangeRatePerH: 0.5,
        tightnessClass: "normal",
        hasHeatRecovery: false,
        hrvEfficiency: 0.8,
        fanPowerW: 0,
        runHoursPerDay: 0,
        control: "manual",
      },
      buildingGeometry: { lengthM: 12, widthM: 10, floors: 1, storyHeightM: 3 },
      referenceAreaM2: 120,
    });
    expect(r.specificDemandGrossKWhM2A).toBeGreaterThan(0);
    expect(["green", "yellow", "orange", "red"]).toContain(r.trafficLight);
    expect(r.heatingDemandGrossKWhA).toBeGreaterThanOrEqual(r.heatingDemandNetKWhA);
  });
});
