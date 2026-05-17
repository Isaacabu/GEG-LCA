// Domain types for the GEG envelope + energy demand calculator.
// Strict: every value either exists with units or is null. No silent defaults.

export type MaterialCategory =
  | "masonry"
  | "insulation"
  | "plaster"
  | "concrete"
  | "wood"
  | "glass"
  | "door"
  | "other";

export type Material = {
  id: string;
  name: string;
  category: MaterialCategory;
  lambdaWmK: number;
  densityKgM3?: number;
  heatCapacityJkgK?: number;
  source?: string;
};

export type ConstructionLayer = {
  id: string;
  materialId: string;
  materialName: string;
  thicknessM: number;
  lambdaWmK: number;
  order: number;
};

export type ElementType = "externalWall" | "roof" | "floor" | "window" | "door";

export type Construction = {
  id: string;
  name: string;
  elementType: ElementType;
  calculationMode: "layers" | "fixedUValue";
  layers?: ConstructionLayer[];
  fixedUValueWm2K?: number;
  source?: string;
};

// Vier Haupthimmelsrichtungen fuer Wandflaechen-Geometrie.
export type WallOrientation = "north" | "south" | "east" | "west";

// Erweiterte Himmelsrichtungen fuer Fenster / Tueren / Solar
// (inkl. Zwischenrichtungen und horizontal fuer Dachfenster).
export type Orientation =
  | WallOrientation
  | "northeast"
  | "southeast"
  | "southwest"
  | "northwest"
  | "horizontal";

export type BoundaryType =
  | "outside"
  | "heatedRoom"
  | "unheatedRoom"
  | "corridor"
  | "basement"
  | "ground"
  | "none";

export type WallOrientationInput = {
  orientation: WallOrientation;
  grossAreaM2: number;
  windowAreaM2: number;
  doorAreaM2: number;
  boundaryType: BoundaryType;
};

export type WallOrientationResult = {
  orientation: WallOrientation;
  grossAreaM2: number;
  windowAreaM2: number;
  doorAreaM2: number;
  netAreaM2: number;
  boundaryType: BoundaryType;
  correctionFactor: number;
  uValueWm2K: number | null;
  hTransmissionWK: number | null;
  status: "complete" | "ignored" | "incomplete" | "error";
  messages: string[];
};

// ---------- Building geometry ----------

export type BuildingGeometry = {
  lengthM: number;
  widthM: number;
  floors: number;
  storyHeightM: number;
};

// ---------- Windows ----------

export type WindowType =
  | "casement"
  | "boxWindow"
  | "compositeWindow"
  | "doubleWindow"
  | "tiltTurn"
  | "fixed"
  | "sliding"
  | "rooflight"
  | "floorToCeiling"
  | "balconyDoor"
  | "shopfront"
  | "custom";

export type WindowGlazing =
  | "single"
  | "double-old"
  | "double-thermal"
  | "triple-thermal"
  | "solarControl"
  | "safety"
  | "unknown"
  | "custom";

export type WindowFrame =
  | "wood"
  | "pvc"
  | "alu"
  | "aluTherm"
  | "woodAlu"
  | "steel"
  | "unknown";

export type WindowInstall =
  | "oldUnrenovated"
  | "normal"
  | "lowThermalBridge"
  | "leakyJoints"
  | "newSeal"
  | "unknown";

export type WindowShadingKind =
  | "none"
  | "interiorBlind"
  | "exteriorShutter"
  | "venetian"
  | "awning"
  | "roofOverhang"
  | "balconyOverhang"
  | "neighbourBuilding"
  | "trees"
  | "partial"
  | "manual";

export type WindowItem = {
  id: string;
  name: string;
  orientation: Orientation;
  count: number;
  widthM: number;
  heightM: number;
  type: WindowType;
  glazing: WindowGlazing;
  frame: WindowFrame;
  install: WindowInstall;
  uValueWm2K: number; // U_w (overall)
  uGlassWm2K?: number; // U_g
  uFrameWm2K?: number; // U_f
  frameShareFraction: number; // 0..1 (Rahmenanteil)
  airTightnessClass?: 1 | 2 | 3 | 4;
  gValue: number; // 0..1
  frameFactor: number; // F_F (0..1)  -> "Abminderung Rahmen", typischerweise 0.7
  shadingKind: WindowShadingKind;
  shadingFactor: number; // F_S (0..1)
  dirtFactor: number; // F_dirt (0..1)
  nonPerpFactor: number; // F_w (0..1)
  tiltDeg?: number; // for rooflights
};

export type WindowResult = {
  id: string;
  name: string;
  orientation: Orientation;
  areaM2: number;
  uValueWm2K: number;
  hTransmissionWK: number;
  effectiveApertureAreaM2: number;
  solarGainKWhA: number; // annual solar gain during heating period
  messages: string[];
};

// ---------- Doors ----------

export type DoorType =
  | "entrance"
  | "apartmentEntrance"
  | "sideEntrance"
  | "basement"
  | "garage"
  | "balcony"
  | "terrace"
  | "fire"
  | "glass"
  | "sectional"
  | "rollup"
  | "sliding"
  | "industrial"
  | "custom";

export type DoorMaterial =
  | "woodSolid"
  | "woodInsulated"
  | "pvc"
  | "aluUninsulated"
  | "aluInsulated"
  | "steelUninsulated"
  | "steelInsulated"
  | "glass"
  | "composite"
  | "unknown";

export type DoorSealCondition =
  | "veryTight"
  | "normal"
  | "slightlyLeaky"
  | "veryLeaky"
  | "noSeal"
  | "unknown";

export type DoorOpeningFrequency =
  | "rare"
  | "normal"
  | "frequent"
  | "veryFrequent"
  | "publicTraffic"
  | "manual";

export type DoorItem = {
  id: string;
  name: string;
  orientation: Orientation;
  count: number;
  widthM: number;
  heightM: number;
  doorType: DoorType;
  material: DoorMaterial;
  thicknessM?: number;
  uValueWm2K: number;
  glassFractionPct: number; // 0..100
  sealCondition: DoorSealCondition;
  thresholdInsulated: boolean;
  openingFrequency: DoorOpeningFrequency;
  openingsPerDay?: number; // when manual
  boundaryType: BoundaryType;
};

export type DoorResult = {
  id: string;
  name: string;
  orientation: Orientation;
  boundaryType: BoundaryType;
  areaM2: number;
  uValueWm2K: number;
  correctionFactor: number;
  hTransmissionWK: number | null;
  status: "complete" | "ignored" | "incomplete";
  messages: string[];
};

// ---------- Floor (Boden / Bodenplatte / Zwischendecke) ----------

export type FloorBoundaryRole =
  | "groundSlab"
  | "basementCeiling"
  | "floorToOutside"
  | "floorToGarage"
  | "crawlSpace"
  | "interFloor"
  | "floorOverArchway"
  | "topFloorCeiling"
  | "custom";

export type FloorInsulation =
  | "none"
  | "aboveSlab"
  | "belowSlab"
  | "perimeter"
  | "basementCeiling"
  | "partial"
  | "unknown";

export type FloorItem = {
  id: string;
  name: string;
  role: FloorBoundaryRole;
  storyIndex: number; // 0 = EG, 1 = OG, ...
  enabled: boolean;
  areaM2: number;
  autoFromGeometry: boolean;
  perimeterAgainstGroundM?: number;
  slabThicknessM?: number;
  boundaryType: BoundaryType;
  constructionId: string | null;
  uValueOverrideWm2K?: number;
  insulation: FloorInsulation;
  insulationThicknessMM?: number;
  floorHeating: boolean;
};

export type FloorResult = {
  id: string;
  name: string;
  role: FloorBoundaryRole;
  enabled: boolean;
  areaM2: number;
  boundaryType: BoundaryType;
  uValueWm2K: number | null;
  correctionFactor: number;
  hTransmissionWK: number | null;
  status: "complete" | "incomplete" | "error" | "ignored";
  messages: string[];
};

// ---------- Roof ----------

export type RoofType =
  | "saddle"
  | "monopitch"
  | "flat"
  | "hipped"
  | "mansard"
  | "tent"
  | "shed"
  | "green"
  | "sheetMetal"
  | "industrial"
  | "custom";

export type RoofCalcMode =
  | "againstOutside"
  | "topFloorCeilingAgainstUnheated"
  | "heatedAtticRoof"
  | "partiallyHeatedAttic"
  | "flatDirectOverHeated";

export type RoofInsulationPosition =
  | "none"
  | "betweenRafters"
  | "aboveRafters"
  | "belowRafters"
  | "combined"
  | "topCeiling"
  | "flatRoof"
  | "partial"
  | "unknown";

export type RoofVentilation = "none" | "ventilated" | "strongVent" | "unknown";

export type RoofMaterial =
  | "claytile"
  | "concreteTile"
  | "metal"
  | "slate"
  | "bitumen"
  | "epdm"
  | "gravel"
  | "green"
  | "wood"
  | "sandwich"
  | "custom";

export type SummerProtection = "low" | "medium" | "good" | "veryGood";

export type RoofSurfaceCoating =
  | "light"
  | "dark"
  | "reflective"
  | "green"
  | "default";

export type RoofShading = "none" | "partial" | "strong";

export type RoofDormer = {
  id: string;
  name: string;
  widthM: number;
  heightM: number;
  uValueWm2K: number;
};

export type RoofInput = {
  roofType: RoofType;
  calcMode: RoofCalcMode;
  areaM2: number;
  autoFromGeometry: boolean;
  enabled: boolean; // false = ungenutztes Dach (z. B. nur oberste Decke)
  insulated: boolean;
  insulationPosition: RoofInsulationPosition;
  insulationThicknessMM: number;
  constructionId: string | null;
  uValueOverrideWm2K?: number;
  material: RoofMaterial;
  ventilation: RoofVentilation;
  pitchDeg?: number;
  overhangM?: number;
  summerProtection?: SummerProtection;
  rooflightAreaM2?: number;
  dormers: RoofDormer[];
  // Steildach extras (optional)
  surfaceA?: { areaM2: number; orientation: Orientation; tiltDeg: number };
  surfaceB?: { areaM2: number; orientation: Orientation; tiltDeg: number };
  // Flachdach extras
  coating?: RoofSurfaceCoating;
  shading?: RoofShading;
};

export type RoofResult = {
  roofType: RoofType;
  calcMode: RoofCalcMode;
  enabled: boolean;
  areaM2: number;
  insulated: boolean;
  uValueWm2K: number | null;
  hTransmissionWK: number | null;
  status: "complete" | "incomplete" | "error" | "ignored";
  messages: string[];
};

// ---------- Wandbauteil-Erweiterung ----------

export type WallType =
  | "solidMass"
  | "brick"
  | "concrete"
  | "aerated"
  | "calciumSilicate"
  | "timberFrame"
  | "halfTimber"
  | "naturalStone"
  | "lightConstruction"
  | "unknown"
  | "custom";

export type WallInsulationState =
  | "none"
  | "interior"
  | "exterior"
  | "core"
  | "ventilatedFacade"
  | "partial"
  | "unknown";

export type WallFacadeColor =
  | "light"
  | "medium"
  | "dark"
  | "reflective"
  | "custom";

export type WallExtras = {
  wallType: WallType;
  insulationState: WallInsulationState;
  facadeColor: WallFacadeColor;
  thermalBridgeDeltaUWm2K: number; // pauschaler Zuschlag
  uValueOverrideWm2K?: number;
  notes?: string;
};

// ---------- Envelope + Energy ----------

export type EnvelopeRequest = {
  buildingGeometry: BuildingGeometry;
  wallOrientations: WallOrientationInput[];
  externalWallConstructionId: string;
  wallExtras?: WallExtras;
  floors?: FloorItem[];
  roof?: RoofInput;
  windows?: WindowItem[];
  doors?: DoorItem[];
};

export type EnvelopeResult = {
  externalWallUValueWm2K: number | null;
  externalWallUValueMethod: "layers" | "fixedUValue" | "override" | null;
  wallResultsByOrientation: WallOrientationResult[];
  wallsTotalWK: number;
  windowResults: WindowResult[];
  windowsTotalWK: number;
  doorResults: DoorResult[];
  doorsTotalWK: number;
  floors: FloorResult[];
  floorsTotalWK: number;
  roof: RoofResult | null;
  solarGainsByOrientation: Partial<Record<Orientation, number>>;
  solarGainsTotalKWhA: number;
  hTTotalWK: number;
  warnings: string[];
};

// ---------- Lueftung ----------

export type VentilationKind =
  | "windowVentilation"
  | "freeVent"
  | "shaftVent"
  | "exhaustOnly"
  | "centralBalanced"
  | "decentralBalanced"
  | "balancedWithHRV"
  | "balancedNoHRV"
  | "commercial"
  | "custom";

export type AirTightnessClass =
  | "veryTight"
  | "normal"
  | "slightlyLeaky"
  | "veryLeaky"
  | "withBlowerDoor"
  | "unknown";

export type VentilationControl =
  | "manual"
  | "timer"
  | "humidity"
  | "co2"
  | "demand"
  | "smartHome";

export type VentilationInput = {
  kind: VentilationKind;
  airChangeRatePerH: number; // n
  n50PerH?: number; // blower-door 50 Pa
  tightnessClass: AirTightnessClass;
  hasHeatRecovery: boolean;
  hrvEfficiency: number; // 0..1
  fanPowerW: number;
  sfpWhPerM3?: number; // Specific Fan Power
  runHoursPerDay: number;
  control: VentilationControl;
  minVolumeFlowM3H?: number;
};

// ---------- Heizung ----------

export type HeatingSystem =
  | "gasCondensing"
  | "gasLowTemp"
  | "gasOld"
  | "oilCondensing"
  | "oilOld"
  | "hpAir"
  | "hpGround"
  | "hpWater"
  | "districtHeating"
  | "pellet"
  | "logGasifier"
  | "logBoiler"
  | "chip"
  | "directElectric"
  | "nightStorage"
  | "hybrid"
  | "solarSupport"
  | "chp"
  | "custom";

export type EnergyCarrier =
  | "naturalGas"
  | "heatingOil"
  | "electricity"
  | "districtHeat"
  | "pellets"
  | "wood"
  | "lpg"
  | "biomass"
  | "solarThermal"
  | "ambient"
  | "hydrogenReady"
  | "custom";

export type HeatEmission =
  | "radiatorsOld"
  | "radiatorsModern"
  | "underfloor"
  | "wall"
  | "ceiling"
  | "airHeating"
  | "fanCoil"
  | "mixed";

export type SupplyTempBand =
  | "t35"
  | "t36_45"
  | "t46_55"
  | "t56_70"
  | "t70plus"
  | "unknown";

export type HeatingControl =
  | "noModern"
  | "roomThermostats"
  | "weather"
  | "nightSetback"
  | "perRoom"
  | "smartHome"
  | "ai";

export type HeatingInput = {
  system: HeatingSystem;
  carrier: EnergyCarrier;
  yearBuilt?: number;
  nominalPowerKW?: number;
  efficiency: number; // generation efficiency 0..1 (or for HPs: COP/JAZ)
  isHeatPump: boolean;
  copJaz?: number; // when heat pump
  supplyTemp: SupplyTempBand;
  returnTempC?: number;
  heatCurve?: number;
  hydraulicBalanced: boolean;
  pumpPowerW: number;
  emission: HeatEmission;
  control: HeatingControl;
  maintenance: "good" | "ok" | "poor" | "unknown";
};

// ---------- Warmwasser ----------

export type HotWaterSystem =
  | "viaCentralHeating"
  | "electricInstant"
  | "gasInstant"
  | "hpBoiler"
  | "solarThermal"
  | "freshWaterStation"
  | "combiStorage"
  | "custom";

export type HotWaterStorage =
  | "none"
  | "small"
  | "tank"
  | "buffer"
  | "combi"
  | "poorlyInsulated"
  | "wellInsulated"
  | "unknown";

export type HotWaterCirculation =
  | "none"
  | "permanent"
  | "timer"
  | "demand"
  | "unknown";

export type HotWaterInput = {
  system: HotWaterSystem;
  persons: number;
  litresPerPersonPerDay: number;
  storage: HotWaterStorage;
  storageInsulationQuality: "poor" | "normal" | "good" | "veryGood" | "unknown";
  storageLossKWhPerDay: number;
  circulation: HotWaterCirculation;
  setpointC: number;
  solarFractionPct: number; // 0..100
};

// ---------- Verteilung / Speicher ----------

export type PipeInsulation =
  | "none"
  | "weak"
  | "normal"
  | "good"
  | "veryGood"
  | "unknown";

export type PipeRouting =
  | "heated"
  | "partlyUnheated"
  | "mostlyUnheated"
  | "basement"
  | "outside"
  | "unknown";

export type DistributionInput = {
  pipeLengthM: number;
  insulation: PipeInsulation;
  routing: PipeRouting;
  pumpPowerW: number;
  pumpHoursPerYear: number;
  storageCount: number;
  storageSizeL: number;
  storageLossWhPerDayPerL: number;
};

// ---------- PV / Solarthermie ----------

export type PVOption =
  | "none"
  | "pvOnly"
  | "solarThermalDHW"
  | "solarThermalHeating"
  | "pvWithHP"
  | "batteryStorage"
  | "custom";

export type PVInput = {
  option: PVOption;
  pvPeakKWp: number;
  pvYieldKWhPerYear: number;
  selfConsumptionPct: number;
  batteryKWh?: number;
  solarThermalAreaM2?: number;
  solarThermalYieldKWhPerYear?: number;
  coverageDHWPct: number;
  coverageHeatPct: number;
};

export type HeatingDemandInput = {
  envelope: EnvelopeResult;
  ventilation: VentilationInput;
  heating?: HeatingInput;
  hotWater?: HotWaterInput;
  distribution?: DistributionInput;
  pv?: PVInput;
  buildingGeometry: BuildingGeometry;
  referenceAreaM2: number;
};

export type EnergyClass =
  | "A+" | "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H";

export type ComponentTrafficLight = "green" | "yellow" | "orange" | "red";

export type ComponentRating = {
  id: string;
  label: string;
  metric: string;
  metricValue: number | null;
  rating: ComponentTrafficLight;
  hContributionWK?: number;
  share?: number; // 0..1 of H_T
  note?: string;
};

export type WeakSpot = {
  id: string;
  label: string;
  reason: string;
  recommendation: string;
  rating: ComponentTrafficLight;
  potentialKWhA?: number;
};

export type HeatingDemandResult = {
  hTWK: number;
  hVWK: number;
  hVEffectiveWK: number; // after HRV
  transmissionLossKWhA: number;
  ventilationLossKWhA: number;
  solarGainsKWhA: number;
  internalGainsKWhA: number;
  utilisationFactor: number;
  usedGainsKWhA: number;
  heatingDemandNetKWhA: number;
  // Anlagenseite
  generationLossKWhA: number; // Erzeugung
  storageLossKWhA: number; // Speicher
  distributionLossKWhA: number; // Verteilung
  auxiliaryEnergyKWhA: number; // Hilfsenergie (Pumpen, Ventilatoren)
  hotWaterDemandKWhA: number;
  solarOffsetKWhA: number; // PV / Solarthermie Anrechnung
  heatingDemandGrossKWhA: number; // Q_end
  endEnergyKWhA: number; // synonym fuer brutto
  primaryEnergyKWhA: number;
  co2EmissionsKgA: number;
  specificDemandNetKWhM2A: number;
  specificDemandGrossKWhM2A: number;
  specificPrimaryEnergyKWhM2A: number;
  trafficLight: ComponentTrafficLight;
  energyClass: EnergyClass;
  componentRatings: ComponentRating[];
  weakSpots: WeakSpot[];
  notes: string[];
};

export type UValueResult = {
  uValueWm2K: number;
  method: "layers" | "fixedUValue";
  layers: Array<{
    materialName: string;
    thicknessM: number;
    lambdaWmK: number;
    rLayer: number;
  }>;
  rTotal: number;
  rsi: number;
  rse: number;
  warnings: string[];
};
