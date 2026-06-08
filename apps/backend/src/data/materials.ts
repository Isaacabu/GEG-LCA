import type { Material } from "@geg/shared";

// Materialdatenbank. Lambda-Werte aus DIN 4108-4 / Herstellerdatenblaettern
// in typischen Groessenordnungen. Vereinfacht fuer Projektzwecke.
export const MATERIALS: Material[] = [
  {
    id: "mat-brick-solid",
    name: "Ziegel Vollziegel",
    category: "masonry",
    lambdaWmK: 0.81,
    densityKgM3: 1800,
    source: "DIN 4108-4",
  },
  {
    id: "mat-brick-perforated",
    name: "Hochlochziegel",
    category: "masonry",
    lambdaWmK: 0.45,
    densityKgM3: 1200,
    source: "DIN 4108-4",
  },
  {
    id: "mat-lightconcrete-block",
    name: "Leichtbeton-Block",
    category: "masonry",
    lambdaWmK: 0.36,
    densityKgM3: 1000,
    source: "DIN 4108-4",
  },
  {
    id: "mat-lightconcrete-stone",
    name: "Leichtbeton-Stein",
    category: "masonry",
    lambdaWmK: 0.45,
    densityKgM3: 1200,
    source: "DIN 4108-4",
  },
  {
    id: "mat-concrete-reinforced",
    name: "Stahlbeton",
    category: "concrete",
    lambdaWmK: 2.3,
    densityKgM3: 2400,
    source: "DIN 4108-4",
  },
  {
    id: "mat-insulation-mineralwool",
    name: "Mineralwolle WLG 035",
    category: "insulation",
    lambdaWmK: 0.035,
    densityKgM3: 50,
    source: "DIN 4108-4",
  },
  {
    id: "mat-insulation-eps",
    name: "EPS WLG 032",
    category: "insulation",
    lambdaWmK: 0.032,
    densityKgM3: 20,
    source: "DIN 4108-4",
  },
  {
    id: "mat-plaster-gypsum",
    name: "Gipsputz innen",
    category: "plaster",
    lambdaWmK: 0.35,
    densityKgM3: 1000,
    source: "DIN 4108-4",
  },
  {
    id: "mat-plaster-resin",
    name: "Kunstharzputz aussen",
    category: "plaster",
    lambdaWmK: 0.7,
    densityKgM3: 1100,
    source: "DIN 4108-4",
  },
  {
    id: "mat-wood-softwood",
    name: "Nadelholz",
    category: "wood",
    lambdaWmK: 0.13,
    densityKgM3: 500,
    source: "DIN 4108-4",
  },
];

export function findMaterialById(id: string): Material | undefined {
  return MATERIALS.find((m) => m.id === id);
}
