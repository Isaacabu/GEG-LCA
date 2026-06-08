import { useCallback, useMemo, useState } from "react";
import type {
  BoundaryType,
  BuildingGeometry,
  DistributionInput,
  DoorItem,
  FloorItem,
  HeatingInput,
  HotWaterInput,
  Orientation,
  PVInput,
  RoofInput,
  VentilationInput,
  WallExtras,
  WallOrientation,
  WallOrientationInput,
  WindowItem,
} from "@geg/shared";
import type { CustomLayer } from "../components/CustomLayerBuilder.js";
import {
  defaultDistribution,
  defaultHeating,
  defaultHotWater,
  defaultPV,
  defaultVentilation,
  deriveWallAreasFromGeometry,
  totalDoorAreaByWall,
  totalWindowAreaByWall,
} from "@geg/shared";

const WALLS: WallOrientation[] = ["north", "south", "east", "west"];

type WallOverrides = Record<WallOrientation, { boundaryType: BoundaryType }>;

const DEFAULT_OVERRIDES: WallOverrides = {
  north: { boundaryType: "outside" },
  south: { boundaryType: "outside" },
  east: { boundaryType: "outside" },
  west: { boundaryType: "outside" },
};

const uid = () => Math.random().toString(36).slice(2, 10);

const defaultWindow = (
  o: Orientation = "south",
  index = 1,
): WindowItem => ({
  id: uid(),
  name: `Fenster ${index}`,
  orientation: o,
  count: 1,
  widthM: 1.2,
  heightM: 1.4,
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
});

const defaultDoor = (o: Orientation = "south", index = 1): DoorItem => ({
  id: uid(),
  name: `Tuer ${index}`,
  orientation: o,
  count: 1,
  widthM: 1.0,
  heightM: 2.0,
  doorType: "entrance",
  material: "woodInsulated",
  thicknessM: 0.06,
  uValueWm2K: 1.8,
  glassFractionPct: 0,
  sealCondition: "normal",
  thresholdInsulated: true,
  openingFrequency: "normal",
  boundaryType: "outside",
});

const defaultFloor = (
  storyIndex: number,
  isTop = false,
): FloorItem => ({
  id: uid(),
  name: isTop
    ? "oberste Geschossdecke"
    : storyIndex === 0
      ? "Bodenplatte"
      : `Zwischendecke OG${storyIndex}`,
  role: isTop
    ? "topFloorCeiling"
    : storyIndex === 0
      ? "groundSlab"
      : "interFloor",
  storyIndex,
  enabled: true,
  areaM2: 0,
  autoFromGeometry: true,
  boundaryType: isTop
    ? "unheatedRoom"
    : storyIndex === 0
      ? "ground"
      : "heatedRoom",
  constructionId: null,
  insulation: "none",
  insulationThicknessMM: 0,
  floorHeating: false,
});

const defaultRoof = (): RoofInput => ({
  roofType: "saddle",
  calcMode: "againstOutside",
  areaM2: 0,
  autoFromGeometry: true,
  enabled: true,
  insulated: true,
  insulationPosition: "betweenRafters",
  insulationThicknessMM: 200,
  constructionId: null,
  material: "claytile",
  ventilation: "ventilated",
  pitchDeg: 30,
  dormers: [],
});

const defaultWallExtras = (): WallExtras => ({
  wallType: "unknown",
  insulationState: "unknown",
  facadeColor: "medium",
  thermalBridgeDeltaUWm2K: 0.05,
  uValueOverrideWm2K: 0.29,
});

export function useBuildingStore() {
  const [geometry, setGeometry] = useState<BuildingGeometry>({
    lengthM: 14.7,
    widthM: 7.57,
    floors: 1,
    storyHeightM: 3.12,
  });
  const [externalWallConstructionId, setExternalWallConstructionId] =
    useState<string>("");
  const [wallExtras, setWallExtras] = useState<WallExtras>(defaultWallExtras());
  const [overrides, setOverrides] =
    useState<WallOverrides>(DEFAULT_OVERRIDES);

  const [windows, setWindows] = useState<WindowItem[]>([
    {
      ...defaultWindow("east", 1),
      name: "Fenster Ost",
      count: 7,
      widthM: 1.5,
      heightM: 2.17,
      uValueWm2K: 1.4,
      gValue: 0.6,
    },
  ]);

  const [doors, setDoors] = useState<DoorItem[]>([
    { ...defaultDoor("south", 1), name: "Eingangstür", count: 2, widthM: 1.1, heightM: 2.0, uValueWm2K: 4.0 },
  ]);

  const [floors, setFloors] = useState<FloorItem[]>([
    {
      ...defaultFloor(0, false),
      name: "Kellerdecke",
      role: "basementCeiling",
      boundaryType: "unheatedRoom",
      uValueOverrideWm2K: 0.6,
    },
  ]);

  const [roof, setRoof] = useState<RoofInput>(defaultRoof());

  const [ventilation, setVentilation] =
    useState<VentilationInput>({
      ...defaultVentilation(),
      kind: "balancedWithHRV",
      airChangeRatePerH: 2.0,
      hasHeatRecovery: true,
      hrvEfficiency: 0.55,
    });
  const [heating, setHeating] = useState<HeatingInput>(defaultHeating());
  const [hotWater, setHotWater] = useState<HotWaterInput>(defaultHotWater());
  const [distribution, setDistribution] =
    useState<DistributionInput>(defaultDistribution());
  const [pv, setPv] = useState<PVInput>(defaultPV());

  // expert mode toggle
  const [expertMode, setExpertMode] = useState<boolean>(true);

  // OBD custom wall layer stack
  const [customWallLayers, setCustomWallLayers] = useState<CustomLayer[]>([]);

  const wallAreas = useMemo(
    () => deriveWallAreasFromGeometry(geometry),
    [geometry],
  );
  const winAreaByWall = useMemo(() => totalWindowAreaByWall(windows), [windows]);
  const doorAreaByWall = useMemo(() => totalDoorAreaByWall(doors), [doors]);

  const wallOrientations = useMemo<WallOrientationInput[]>(() => {
    return WALLS.map((o) => ({
      orientation: o,
      grossAreaM2: wallAreas[o],
      windowAreaM2: winAreaByWall[o],
      doorAreaM2: doorAreaByWall[o],
      boundaryType: overrides[o].boundaryType,
    }));
  }, [wallAreas, winAreaByWall, doorAreaByWall, overrides]);

  const setBoundary = useCallback((o: WallOrientation, b: BoundaryType) => {
    setOverrides((p) => ({ ...p, [o]: { ...p[o], boundaryType: b } }));
  }, []);

  // Items helpers ------------------------------------------------------------
  const addWindow = useCallback(
    (o: Orientation = "south") =>
      setWindows((p) => [...p, defaultWindow(o, p.length + 1)]),
    [],
  );
  const duplicateWindow = useCallback(
    (id: string) =>
      setWindows((p) => {
        const i = p.findIndex((w) => w.id === id);
        if (i < 0) return p;
        const copy: WindowItem = { ...p[i], id: uid(), name: p[i].name + " (Kopie)" };
        return [...p.slice(0, i + 1), copy, ...p.slice(i + 1)];
      }),
    [],
  );
  const updateWindow = useCallback((id: string, patch: Partial<WindowItem>) => {
    setWindows((p) => p.map((w) => (w.id === id ? { ...w, ...patch } : w)));
  }, []);
  const removeWindow = useCallback((id: string) => {
    setWindows((p) => p.filter((w) => w.id !== id));
  }, []);

  const addDoor = useCallback(
    (o: Orientation = "south") =>
      setDoors((p) => [...p, defaultDoor(o, p.length + 1)]),
    [],
  );
  const duplicateDoor = useCallback(
    (id: string) =>
      setDoors((p) => {
        const i = p.findIndex((d) => d.id === id);
        if (i < 0) return p;
        const copy: DoorItem = { ...p[i], id: uid(), name: p[i].name + " (Kopie)" };
        return [...p.slice(0, i + 1), copy, ...p.slice(i + 1)];
      }),
    [],
  );
  const updateDoor = useCallback((id: string, patch: Partial<DoorItem>) => {
    setDoors((p) => p.map((d) => (d.id === id ? { ...d, ...patch } : d)));
  }, []);
  const removeDoor = useCallback((id: string) => {
    setDoors((p) => p.filter((d) => d.id !== id));
  }, []);

  const addFloor = useCallback(
    () => setFloors((p) => [...p, defaultFloor(p.length, false)]),
    [],
  );
  const duplicateFloor = useCallback(
    (id: string) =>
      setFloors((p) => {
        const i = p.findIndex((f) => f.id === id);
        if (i < 0) return p;
        const copy: FloorItem = { ...p[i], id: uid(), name: p[i].name + " (Kopie)" };
        return [...p.slice(0, i + 1), copy, ...p.slice(i + 1)];
      }),
    [],
  );
  const updateFloor = useCallback((id: string, patch: Partial<FloorItem>) => {
    setFloors((p) => p.map((f) => (f.id === id ? { ...f, ...patch } : f)));
  }, []);
  const removeFloor = useCallback((id: string) => {
    setFloors((p) => p.filter((f) => f.id !== id));
  }, []);

  // Derived quantities -------------------------------------------------------
  const grossArea = useMemo(
    () => geometry.lengthM * geometry.widthM,
    [geometry],
  );
  const totalHeight = useMemo(
    () => geometry.floors * geometry.storyHeightM,
    [geometry],
  );
  const volume = useMemo(
    () => grossArea * totalHeight,
    [grossArea, totalHeight],
  );
  const referenceArea = useMemo(
    () => grossArea * geometry.floors,
    [grossArea, geometry.floors],
  );

  return {
    // geometry
    geometry, setGeometry,
    grossArea, totalHeight, volume, referenceArea,
    // walls
    wallOrientations, overrides, setBoundary,
    externalWallConstructionId, setExternalWallConstructionId,
    wallExtras, setWallExtras,
    // windows
    windows, addWindow, updateWindow, removeWindow, duplicateWindow,
    // doors
    doors, addDoor, updateDoor, removeDoor, duplicateDoor,
    // floors
    floors, addFloor, updateFloor, removeFloor, duplicateFloor,
    // roof
    roof, setRoof,
    // HVAC
    ventilation, setVentilation,
    heating, setHeating,
    hotWater, setHotWater,
    distribution, setDistribution,
    pv, setPv,
    // mode
    expertMode, setExpertMode,
    // OBD custom layers
    customWallLayers, setCustomWallLayers,
  };
}

export type BuildingStore = ReturnType<typeof useBuildingStore>;
