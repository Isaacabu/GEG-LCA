import type { Construction, ConstructionLayer } from "@geg/shared";
import { findMaterialById } from "./materials.js";

type LayerSpec = { materialId: string; thicknessM: number };

function buildLayers(specs: LayerSpec[]): ConstructionLayer[] {
  return specs.map((s, i) => {
    const m = findMaterialById(s.materialId);
    if (!m) {
      throw new Error(`Material ${s.materialId} nicht gefunden.`);
    }
    return {
      id: `${s.materialId}-${i}`,
      materialId: m.id,
      materialName: m.name,
      thicknessM: s.thicknessM,
      lambdaWmK: m.lambdaWmK,
      order: i,
    };
  });
}

// Bauteilkatalog. Schichten sind von innen nach außen aufgeführt.
// U-Werte werden NICHT vorab eingetragen, sondern aus den Schichten
// berechnet (Single Source of Truth: Schicht-Daten + Lambda).
export const CONSTRUCTIONS: Construction[] = [
  {
    id: "wall-brick-365",
    name: "Aussenwand Hochlochziegel 36,5 cm",
    elementType: "externalWall",
    calculationMode: "layers",
    layers: buildLayers([
      { materialId: "mat-plaster-gypsum", thicknessM: 0.015 },
      { materialId: "mat-brick-perforated", thicknessM: 0.365 },
      { materialId: "mat-plaster-resin", thicknessM: 0.015 },
    ]),
    source: "Vereinfachter Standard-Wandaufbau",
  },
  {
    id: "wall-lightconcrete-block-300",
    name: "Aussenwand Leichtbeton-Block 30 cm",
    elementType: "externalWall",
    calculationMode: "layers",
    layers: buildLayers([
      { materialId: "mat-plaster-gypsum", thicknessM: 0.015 },
      { materialId: "mat-lightconcrete-block", thicknessM: 0.3 },
      { materialId: "mat-plaster-resin", thicknessM: 0.015 },
    ]),
    source: "Vereinfachter Standard-Wandaufbau",
  },
  {
    id: "wall-lightconcrete-stone-300",
    name: "Aussenwand Leichtbeton-Stein 30 cm",
    elementType: "externalWall",
    calculationMode: "layers",
    layers: buildLayers([
      { materialId: "mat-plaster-gypsum", thicknessM: 0.015 },
      { materialId: "mat-lightconcrete-stone", thicknessM: 0.3 },
      { materialId: "mat-plaster-resin", thicknessM: 0.015 },
    ]),
    source: "Vereinfachter Standard-Wandaufbau",
  },
  {
    id: "wall-brick-240-insul-160",
    name: "Aussenwand Ziegel 24 cm + WDVS 16 cm",
    elementType: "externalWall",
    calculationMode: "layers",
    layers: buildLayers([
      { materialId: "mat-plaster-gypsum", thicknessM: 0.015 },
      { materialId: "mat-brick-perforated", thicknessM: 0.24 },
      { materialId: "mat-insulation-eps", thicknessM: 0.16 },
      { materialId: "mat-plaster-resin", thicknessM: 0.01 },
    ]),
    source: "WDVS-Standardaufbau, Projektwert",
  },
  {
    id: "roof-flat-insulated",
    name: "Flachdach mit Mineralwolle 24 cm",
    elementType: "roof",
    calculationMode: "layers",
    layers: buildLayers([
      { materialId: "mat-plaster-gypsum", thicknessM: 0.015 },
      { materialId: "mat-concrete-reinforced", thicknessM: 0.2 },
      { materialId: "mat-insulation-mineralwool", thicknessM: 0.24 },
    ]),
    source: "Vereinfachter Standard-Dachaufbau",
  },
  {
    id: "floor-basement-insulated",
    name: "Bodenplatte gegen Keller, gedaemmt 12 cm",
    elementType: "floor",
    calculationMode: "layers",
    layers: buildLayers([
      { materialId: "mat-concrete-reinforced", thicknessM: 0.2 },
      { materialId: "mat-insulation-eps", thicknessM: 0.12 },
    ]),
    source: "Vereinfachter Standard-Bodenaufbau",
  },
  {
    id: "window-2pane",
    name: "Fenster 2-Scheiben Waermeschutzverglasung",
    elementType: "window",
    calculationMode: "fixedUValue",
    fixedUValueWm2K: 1.3,
    source: "Herstellerangabe (vereinfacht)",
  },
  {
    id: "door-insulated",
    name: "Haustuer gedaemmt",
    elementType: "door",
    calculationMode: "fixedUValue",
    fixedUValueWm2K: 1.8,
    source: "Herstellerangabe (vereinfacht)",
  },
];

export function findConstructionById(id: string): Construction | undefined {
  return CONSTRUCTIONS.find((c) => c.id === id);
}

export function constructionsByElementType(
  elementType: Construction["elementType"],
): Construction[] {
  return CONSTRUCTIONS.filter((c) => c.elementType === elementType);
}
