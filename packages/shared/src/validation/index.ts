import type {
  BuildingGeometry,
  DoorItem,
  EnvelopeRequest,
  FloorItem,
  RoofInput,
  WallOrientationInput,
  WindowItem,
} from "../types/index.js";

export type ValidationError = { path: string; message: string };

export function validateGeometry(g: BuildingGeometry): ValidationError[] {
  const errs: ValidationError[] = [];
  if (!(g.lengthM > 0)) errs.push({ path: "lengthM", message: "Laenge muss > 0 sein." });
  if (!(g.widthM > 0)) errs.push({ path: "widthM", message: "Breite muss > 0 sein." });
  if (!(g.floors > 0) || !Number.isInteger(g.floors))
    errs.push({ path: "floors", message: "Etagen muss ganzzahlig und > 0 sein." });
  if (!(g.storyHeightM > 0))
    errs.push({ path: "storyHeightM", message: "Wandhoehe pro Etage muss > 0 sein." });
  return errs;
}

export function validateWallOrientation(
  w: WallOrientationInput,
  index: number,
): ValidationError[] {
  const errs: ValidationError[] = [];
  const prefix = `wallOrientations[${index}]`;
  if (!(w.grossAreaM2 >= 0))
    errs.push({ path: `${prefix}.grossAreaM2`, message: "Bruttoflaeche muss >= 0 sein." });
  if (!(w.windowAreaM2 >= 0))
    errs.push({ path: `${prefix}.windowAreaM2`, message: "Fensterflaeche muss >= 0 sein." });
  if (!(w.doorAreaM2 >= 0))
    errs.push({ path: `${prefix}.doorAreaM2`, message: "Tuerflaeche muss >= 0 sein." });
  return errs;
}

export function validateWindow(w: WindowItem, i: number): ValidationError[] {
  const errs: ValidationError[] = [];
  const p = `windows[${i}]`;
  if (!(w.count >= 0)) errs.push({ path: `${p}.count`, message: "Anzahl muss >= 0." });
  if (!(w.widthM > 0)) errs.push({ path: `${p}.widthM`, message: "Breite > 0." });
  if (!(w.heightM > 0)) errs.push({ path: `${p}.heightM`, message: "Hoehe > 0." });
  if (!(w.uValueWm2K > 0))
    errs.push({ path: `${p}.uValueWm2K`, message: "U-Wert Fenster > 0." });
  for (const k of [
    "gValue",
    "frameFactor",
    "shadingFactor",
    "dirtFactor",
    "nonPerpFactor",
  ] as const) {
    const v = w[k];
    if (!(v >= 0 && v <= 1))
      errs.push({ path: `${p}.${k}`, message: `${k} muss in [0, 1] liegen.` });
  }
  return errs;
}

export function validateDoor(d: DoorItem, i: number): ValidationError[] {
  const errs: ValidationError[] = [];
  const p = `doors[${i}]`;
  if (!(d.count >= 0)) errs.push({ path: `${p}.count`, message: "Anzahl muss >= 0." });
  if (!(d.widthM > 0)) errs.push({ path: `${p}.widthM`, message: "Breite > 0." });
  if (!(d.heightM > 0)) errs.push({ path: `${p}.heightM`, message: "Hoehe > 0." });
  if (!(d.uValueWm2K > 0))
    errs.push({ path: `${p}.uValueWm2K`, message: "U-Wert Tuer > 0." });
  if (!(d.glassFractionPct >= 0 && d.glassFractionPct <= 100))
    errs.push({ path: `${p}.glassFractionPct`, message: "Glasanteil in 0..100 %." });
  return errs;
}

export function validateFloor(f: FloorItem, i: number): ValidationError[] {
  if (!f.enabled) return [];
  const errs: ValidationError[] = [];
  const p = `floors[${i}]`;
  if (!f.autoFromGeometry && !(f.areaM2 > 0))
    errs.push({ path: `${p}.areaM2`, message: "Bodenflaeche > 0 oder Auto aktivieren." });
  if (!f.boundaryType)
    errs.push({ path: `${p}.boundaryType`, message: "Grenzbedingung fehlt." });
  return errs;
}

export function validateRoof(r: RoofInput | undefined): ValidationError[] {
  if (!r) return [];
  if (!r.enabled) return [];
  const errs: ValidationError[] = [];
  if (!r.roofType) errs.push({ path: "roof.roofType", message: "Dachtyp fehlt." });
  if (!r.autoFromGeometry && !(r.areaM2 > 0))
    errs.push({ path: "roof.areaM2", message: "Dachflaeche > 0 oder Auto aktivieren." });
  return errs;
}

export function validateEnvelopeRequest(req: EnvelopeRequest): ValidationError[] {
  const errs: ValidationError[] = [...validateGeometry(req.buildingGeometry)];
  req.wallOrientations.forEach((w, i) =>
    errs.push(...validateWallOrientation(w, i)),
  );
  // Aussenwand: Override hat Vorrang, sonst Construction Pflicht.
  const hasOverride =
    req.wallExtras?.uValueOverrideWm2K !== undefined &&
    req.wallExtras.uValueOverrideWm2K > 0;
  if (
    !hasOverride &&
    (!req.externalWallConstructionId || req.externalWallConstructionId.trim() === "")
  ) {
    errs.push({
      path: "externalWallConstructionId",
      message: "Es wurde kein Aussenwandaufbau gewaehlt (oder U-Override).",
    });
  }
  (req.windows ?? []).forEach((w, i) => errs.push(...validateWindow(w, i)));
  (req.doors ?? []).forEach((d, i) => errs.push(...validateDoor(d, i)));
  (req.floors ?? []).forEach((f, i) => errs.push(...validateFloor(f, i)));
  errs.push(...validateRoof(req.roof));
  return errs;
}
