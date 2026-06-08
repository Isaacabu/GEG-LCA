import type {
  ComponentRating,
  EnergyCarrier,
  EnergyClass,
  HeatingDemandInput,
  HeatingDemandResult,
  HeatingInput,
  HotWaterInput,
  DistributionInput,
  PVInput,
  PipeInsulation,
  VentilationInput,
  WeakSpot,
  EnvelopeResult,
} from "../types/index.js";
import {
  AIR_CP_RHO_WH_M3K,
  HEATING_PERIOD_GT_KKHA,
  calculateVentilationConductanceWK,
  energyTrafficLight,
  gainUtilisationFactor,
  heatedVolumeM3,
  internalGainsKWhA,
} from "./buildingPhysics.js";

// Vereinfachte Primaerenergiefaktoren und CO2-Emissionsfaktoren je Energietraeger.
// Projektwerte. CO2 in kg/kWh.
export const PRIMARY_ENERGY_FACTORS: Record<EnergyCarrier, number> = {
  naturalGas: 1.1,
  heatingOil: 1.1,
  electricity: 1.8,
  districtHeat: 0.7,
  pellets: 0.2,
  wood: 0.2,
  lpg: 1.1,
  biomass: 0.2,
  solarThermal: 0.0,
  ambient: 0.0,
  hydrogenReady: 1.1,
  custom: 1.0,
};

export const CO2_FACTORS_KG_KWH: Record<EnergyCarrier, number> = {
  naturalGas: 0.201,
  heatingOil: 0.266,
  electricity: 0.366,
  districtHeat: 0.13,
  pellets: 0.036,
  wood: 0.027,
  lpg: 0.236,
  biomass: 0.045,
  solarThermal: 0,
  ambient: 0,
  hydrogenReady: 0.05,
  custom: 0.2,
};

// Spec demand (gross) -> energy class.
export function energyClassFromSpecific(spec: number): EnergyClass {
  if (spec <= 30) return "A+";
  if (spec <= 50) return "A";
  if (spec <= 75) return "B";
  if (spec <= 100) return "C";
  if (spec <= 130) return "D";
  if (spec <= 160) return "E";
  if (spec <= 200) return "F";
  if (spec <= 250) return "G";
  return "H";
}

// Pipe-insulation impact factor on distribution losses.
const PIPE_INSUL_FACTOR: Record<PipeInsulation, number> = {
  none: 1.0,
  weak: 0.7,
  normal: 0.4,
  good: 0.2,
  veryGood: 0.1,
  unknown: 0.6,
};

function ratingForU(u: number | null, thresholds: number[]): ComponentRating["rating"] {
  if (u === null) return "red";
  if (u <= thresholds[0]) return "green";
  if (u <= thresholds[1]) return "yellow";
  if (u <= thresholds[2]) return "orange";
  return "red";
}

function buildComponentRatings(
  env: EnvelopeResult,
  vent: VentilationInput,
  heating: HeatingInput | undefined,
): { ratings: ComponentRating[]; weakSpots: WeakSpot[] } {
  const ratings: ComponentRating[] = [];
  const weakSpots: WeakSpot[] = [];
  const totalH = Math.max(env.hTTotalWK, 1e-9);

  // Aussenwaende
  ratings.push({
    id: "walls",
    label: "Aussenwaende",
    metric: "U-Wert",
    metricValue: env.externalWallUValueWm2K,
    rating: ratingForU(env.externalWallUValueWm2K, [0.24, 0.4, 0.7]),
    hContributionWK: env.wallsTotalWK,
    share: env.wallsTotalWK / totalH,
  });

  // Fenster (avg U gewichtet)
  const winArea = env.windowResults.reduce((s, w) => s + w.areaM2, 0);
  const winWeightedU =
    winArea > 0
      ? env.windowResults.reduce((s, w) => s + w.uValueWm2K * w.areaM2, 0) /
        winArea
      : null;
  ratings.push({
    id: "windows",
    label: "Fenster",
    metric: "U_w (Flaechen-gewichtet)",
    metricValue: winWeightedU,
    rating: ratingForU(winWeightedU, [1.0, 1.6, 2.5]),
    hContributionWK: env.windowsTotalWK,
    share: env.windowsTotalWK / totalH,
    note:
      env.solarGainsTotalKWhA > 0
        ? `Solare Gewinne ${env.solarGainsTotalKWhA.toFixed(0)} kWh/a`
        : undefined,
  });

  // Tueren
  const doorArea = env.doorResults.reduce((s, d) => s + d.areaM2, 0);
  const doorWeightedU =
    doorArea > 0
      ? env.doorResults.reduce((s, d) => s + d.uValueWm2K * d.areaM2, 0) /
        doorArea
      : null;
  ratings.push({
    id: "doors",
    label: "Tueren",
    metric: "U-Wert",
    metricValue: doorWeightedU,
    rating: ratingForU(doorWeightedU, [1.4, 2.0, 3.0]),
    hContributionWK: env.doorsTotalWK,
    share: env.doorsTotalWK / totalH,
  });

  // Boeden gesamt
  const floorArea = env.floors.reduce((s, f) => s + f.areaM2, 0);
  const floorWeightedU =
    floorArea > 0
      ? env.floors
          .filter((f) => f.uValueWm2K !== null)
          .reduce((s, f) => s + (f.uValueWm2K ?? 0) * f.areaM2, 0) / floorArea
      : null;
  ratings.push({
    id: "floors",
    label: "Boeden",
    metric: "U-Wert (avg)",
    metricValue: floorWeightedU,
    rating: ratingForU(floorWeightedU, [0.3, 0.5, 0.9]),
    hContributionWK: env.floorsTotalWK,
    share: env.floorsTotalWK / totalH,
  });

  // Dach
  if (env.roof) {
    ratings.push({
      id: "roof",
      label: "Dach",
      metric: "U-Wert",
      metricValue: env.roof.uValueWm2K,
      rating: ratingForU(env.roof.uValueWm2K, [0.2, 0.3, 0.5]),
      hContributionWK: env.roof.hTransmissionWK ?? 0,
      share: (env.roof.hTransmissionWK ?? 0) / totalH,
      note: env.roof.insulated ? undefined : "Dach nicht isoliert.",
    });
  }

  // Lueftung
  ratings.push({
    id: "vent",
    label: "Lueftung",
    metric: "n + WRG",
    metricValue: vent.airChangeRatePerH,
    rating: vent.hasHeatRecovery
      ? vent.hrvEfficiency >= 0.8
        ? "green"
        : vent.hrvEfficiency >= 0.6
          ? "yellow"
          : "orange"
      : vent.airChangeRatePerH > 0.7
        ? "orange"
        : "yellow",
    note: vent.hasHeatRecovery
      ? `WRG ${(vent.hrvEfficiency * 100).toFixed(0)} %`
      : "ohne WRG",
  });

  // Anlagentechnik
  if (heating) {
    const eff = heating.isHeatPump
      ? (heating.copJaz ?? heating.efficiency ?? 1)
      : heating.efficiency;
    ratings.push({
      id: "heating",
      label: "Anlagentechnik",
      metric: heating.isHeatPump ? "JAZ" : "eta",
      metricValue: eff,
      rating: heating.isHeatPump
        ? eff >= 4
          ? "green"
          : eff >= 3
            ? "yellow"
            : eff >= 2
              ? "orange"
              : "red"
        : eff >= 0.95
          ? "green"
          : eff >= 0.85
            ? "yellow"
            : eff >= 0.7
              ? "orange"
              : "red",
    });
  }

  // Schwachstellen: groesster Beitrag mit schlechtem Rating
  const sorted = [...ratings]
    .filter((r) => r.hContributionWK !== undefined)
    .sort((a, b) => (b.hContributionWK ?? 0) - (a.hContributionWK ?? 0));
  for (const r of sorted.slice(0, 3)) {
    if (r.rating === "orange" || r.rating === "red") {
      weakSpots.push({
        id: `weak-${r.id}`,
        label: r.label,
        reason: `${r.metric} = ${r.metricValue?.toFixed(3) ?? "—"} (${(r.share! * 100).toFixed(0)} % von H_T)`,
        recommendation:
          r.id === "walls"
            ? "Daemmung verbessern (WDVS / Kerndaemmung / Innendaemmung)."
            : r.id === "windows"
              ? "Verglasung auf 2- oder 3-fach Waermeschutz tauschen."
              : r.id === "doors"
                ? "Tuer dichten oder gedaemmte Aussentuer einbauen."
                : r.id === "floors"
                  ? "Bodenplatte / Kellerdecke daemmen."
                  : r.id === "roof"
                    ? "Dach- oder oberste Geschossdecke daemmen."
                    : "Anlagentechnik modernisieren oder Lueftung optimieren.",
        rating: r.rating,
      });
    }
  }

  return { ratings, weakSpots };
}

export function calculateHeatingDemand(
  input: HeatingDemandInput,
): HeatingDemandResult {
  const notes: string[] = [
    "Vereinfachter Projektansatz: G_t = 84 kKh/a, eta_gn aus Gewinn/Verlust-Verhaeltnis.",
  ];

  const hTWK = input.envelope.hTTotalWK;
  const v = heatedVolumeM3(input.buildingGeometry);
  const hVWK = calculateVentilationConductanceWK(
    input.ventilation.airChangeRatePerH,
    v,
  );
  const hrvFactor = input.ventilation.hasHeatRecovery
    ? Math.max(0, 1 - Math.min(1, input.ventilation.hrvEfficiency))
    : 1;
  const hVEffectiveWK = hVWK * hrvFactor;
  if (input.ventilation.hasHeatRecovery) {
    notes.push(
      `Lueftungsverlust um WRG eta=${(input.ventilation.hrvEfficiency * 100).toFixed(0)} % reduziert.`,
    );
  }

  const transmissionLossKWhA = hTWK * HEATING_PERIOD_GT_KKHA;
  const ventilationLossKWhA = hVEffectiveWK * HEATING_PERIOD_GT_KKHA;
  const lossesKWhA = transmissionLossKWhA + ventilationLossKWhA;

  const solarGainsKWhA = input.envelope.solarGainsTotalKWhA;
  const refArea = Math.max(0, input.referenceAreaM2);
  const internalGainsKWhA_ = internalGainsKWhA(refArea);
  const totalGainsKWhA = solarGainsKWhA + internalGainsKWhA_;

  const utilisationFactor = gainUtilisationFactor(lossesKWhA, totalGainsKWhA);
  const usedGainsKWhA = utilisationFactor * totalGainsKWhA;

  const heatingDemandNetKWhA = Math.max(0, lossesKWhA - usedGainsKWhA);

  // Anlagenverluste
  const heating = input.heating;
  const dist = input.distribution;
  const dhw = input.hotWater;
  const pv = input.pv;

  let efficiency = 0.9;
  let isHP = false;
  let cop = 0;
  let carrier: EnergyCarrier = "naturalGas";
  if (heating) {
    isHP = heating.isHeatPump;
    cop = heating.copJaz ?? 0;
    efficiency = Math.min(1, Math.max(0.01, heating.efficiency));
    carrier = heating.carrier;
  }

  const generationLossKWhA = heatingDemandNetKWhA * (1 / efficiency - 1);

  const distributionLossKWhA = dist
    ? heatingDemandNetKWhA * 0.05 * PIPE_INSUL_FACTOR[dist.insulation] *
      (dist.routing === "outside"
        ? 2
        : dist.routing === "mostlyUnheated"
          ? 1.4
          : dist.routing === "partlyUnheated"
            ? 1.1
            : dist.routing === "basement"
              ? 1.2
              : 1.0)
    : heatingDemandNetKWhA * 0.05;

  const storageLossKWhA = dist
    ? (dist.storageCount * dist.storageSizeL * dist.storageLossWhPerDayPerL *
        365) /
      1000
    : 0;

  // Hot water demand (vereinfacht): 4187 J/(kgK) * Liter * deltaT * Tage
  let hotWaterDemandKWhA = 0;
  if (dhw && dhw.persons > 0 && dhw.litresPerPersonPerDay > 0) {
    const dT = Math.max(0, dhw.setpointC - 10);
    const energyJ =
      dhw.persons * dhw.litresPerPersonPerDay * 4187 * dT * 365;
    hotWaterDemandKWhA = energyJ / 3.6e6;
    hotWaterDemandKWhA += dhw.storageLossKWhPerDay * 365;
    if (dhw.solarFractionPct > 0) {
      hotWaterDemandKWhA *= 1 - Math.min(1, dhw.solarFractionPct / 100);
    }
  }

  const auxiliaryEnergyKWhA =
    (dist?.pumpPowerW ?? 0) * (dist?.pumpHoursPerYear ?? 0) / 1000 +
    (input.ventilation.fanPowerW * input.ventilation.runHoursPerDay * 365) /
      1000;

  // Brutto / Endenergie
  let endEnergyKWhA =
    heatingDemandNetKWhA / efficiency +
    distributionLossKWhA +
    storageLossKWhA +
    hotWaterDemandKWhA +
    auxiliaryEnergyKWhA;

  // PV / Solar offset
  let solarOffsetKWhA = 0;
  if (pv) {
    const heatCoverage = pv.coverageHeatPct
      ? Math.min(1, pv.coverageHeatPct / 100)
      : 0;
    solarOffsetKWhA = pv.pvYieldKWhPerYear * (pv.selfConsumptionPct / 100) +
      (pv.solarThermalYieldKWhPerYear ?? 0) * heatCoverage;
    endEnergyKWhA = Math.max(0, endEnergyKWhA - solarOffsetKWhA);
  }

  // Primaerenergie + CO2
  const fPE = PRIMARY_ENERGY_FACTORS[carrier] ?? 1.0;
  const fCO2 = CO2_FACTORS_KG_KWH[carrier] ?? 0.2;
  const primaryEnergyKWhA = endEnergyKWhA * fPE;
  const co2EmissionsKgA = endEnergyKWhA * fCO2;

  const heatingDemandGrossKWhA = endEnergyKWhA;
  const specificDemandNetKWhM2A =
    refArea > 0 ? heatingDemandNetKWhA / refArea : 0;
  const specificDemandGrossKWhM2A =
    refArea > 0 ? heatingDemandGrossKWhA / refArea : 0;
  const specificPrimaryEnergyKWhM2A =
    refArea > 0 ? primaryEnergyKWhA / refArea : 0;

  if (!(refArea > 0)) {
    notes.push("Referenzflaeche = 0: spezifische Werte nicht aussagekraeftig.");
  }

  const { ratings: componentRatings, weakSpots } = buildComponentRatings(
    input.envelope,
    input.ventilation,
    input.heating,
  );

  return {
    hTWK,
    hVWK,
    hVEffectiveWK,
    transmissionLossKWhA,
    ventilationLossKWhA,
    solarGainsKWhA,
    internalGainsKWhA: internalGainsKWhA_,
    utilisationFactor,
    usedGainsKWhA,
    heatingDemandNetKWhA,
    generationLossKWhA,
    storageLossKWhA,
    distributionLossKWhA,
    auxiliaryEnergyKWhA,
    hotWaterDemandKWhA,
    solarOffsetKWhA,
    heatingDemandGrossKWhA,
    endEnergyKWhA,
    primaryEnergyKWhA,
    co2EmissionsKgA,
    specificDemandNetKWhM2A,
    specificDemandGrossKWhM2A,
    specificPrimaryEnergyKWhM2A,
    trafficLight: energyTrafficLight(specificDemandGrossKWhM2A),
    energyClass: energyClassFromSpecific(specificDemandGrossKWhM2A),
    componentRatings,
    weakSpots,
    notes,
  };
}

// Defaults helpers (for backend + frontend reusability)
export function defaultVentilation(): VentilationInput {
  return {
    kind: "windowVentilation",
    airChangeRatePerH: 0.5,
    tightnessClass: "normal",
    hasHeatRecovery: false,
    hrvEfficiency: 0.8,
    fanPowerW: 0,
    runHoursPerDay: 0,
    control: "manual",
  };
}

export function defaultHeating(): HeatingInput {
  return {
    system: "gasCondensing",
    carrier: "naturalGas",
    efficiency: 0.95,
    isHeatPump: false,
    supplyTemp: "t56_70",
    hydraulicBalanced: false,
    pumpPowerW: 30,
    emission: "radiatorsModern",
    control: "weather",
    maintenance: "ok",
  };
}

export function defaultHotWater(): HotWaterInput {
  return {
    system: "viaCentralHeating",
    persons: 2,
    litresPerPersonPerDay: 35,
    storage: "tank",
    storageInsulationQuality: "normal",
    storageLossKWhPerDay: 1.0,
    circulation: "none",
    setpointC: 55,
    solarFractionPct: 0,
  };
}

export function defaultDistribution(): DistributionInput {
  return {
    pipeLengthM: 60,
    insulation: "normal",
    routing: "heated",
    pumpPowerW: 30,
    pumpHoursPerYear: 4000,
    storageCount: 1,
    storageSizeL: 150,
    storageLossWhPerDayPerL: 6,
  };
}

export function defaultPV(): PVInput {
  return {
    option: "none",
    pvPeakKWp: 0,
    pvYieldKWhPerYear: 0,
    selfConsumptionPct: 30,
    coverageDHWPct: 0,
    coverageHeatPct: 0,
  };
}
