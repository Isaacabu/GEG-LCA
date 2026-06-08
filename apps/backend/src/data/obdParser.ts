import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export type OBDMaterial = {
  uuid: string;
  name: string;
  category: string;
  densityKgM3: number | null;
  defaultThicknessM: number | null;
  lambdaWmK: number | null; // Estimated from DIN 4108-4 / category
  url: string;
};

// ---------------------------------------------------------------------------
// Lambda estimation based on Ökobaudat category strings (DIN 4108-4 inspired)
// ---------------------------------------------------------------------------
function estimateLambda(category: string, density: number | null): number | null {
  const c = category.toLowerCase();

  // --- Insulation materials (Dämmstoffe) ---
  if (c.includes("expandiertes polystyrol") || c.includes("/ eps ")) {
    if (c.includes("grau")) return 0.031;
    return 0.035;
  }
  if (c.includes("extrudiertes polystyrol") || c.includes("/ xps ")) return 0.036;
  if (c.includes("pir-hartschaum")) return 0.023;
  if (c.includes("polyurethan-hartschaum") || c.includes("pu ") || c.includes("/ pu-")) return 0.026;
  if (c.includes("phenolharz")) return 0.021;
  if (c.includes("vakuumisolation")) return 0.008;
  if (
    c.includes("mineralwolle") ||
    c.includes("glaswolle") ||
    c.includes("steinwolle")
  )
    return 0.036;
  if (c.includes("schaumglas")) return 0.040;
  if (c.includes("holzfasern") || c.includes("holzfaserd")) return 0.042;
  if (c.includes("zellulose")) return 0.040;
  if (c.includes("baumwolle")) return 0.040;
  if (c.includes("hanffaser") || c.includes("hanf")) return 0.042;
  if (c.includes("expandierter kork") || c.includes("/ kork")) return 0.042;
  if (c.includes("stroh")) return 0.080;
  if (c.includes("holzwolle")) return 0.090;
  if (c.includes("melaminharz")) return 0.042;
  if (c.includes("kautschuk") && c.includes("schaum")) return 0.036;
  if (c.includes("polyethylen") && c.includes("schaum")) return 0.040;
  if (c.includes("blähperlit") || c.includes("bl hperlit")) return 0.065;
  if (c.includes("calciumsilikat") && c.includes("d mm")) return 0.065;
  if (c.includes("schaumbeton") && c.includes("d mm")) return 0.150;
  if (c.includes("schafswolle") || c.includes("schafwolle")) return 0.040;
  if (c.includes("flachsfaser")) return 0.042;
  if (c.includes("wärmedämmverbundsystem") || c.includes("wdvs komplett") || c.includes("w rmed mmverbundsystem")) return 0.035;

  // --- Masonry (density-based, DIN 4108-4 Table 1) ---
  if (c.includes("hochlochziegel") || (c.includes("ziegel") && c.includes("mauerwerk"))) {
    if (density) return Math.max(0.08, 0.19 * (density / 1000) + 0.04);
    return 0.36;
  }
  if (c.includes("vollziegel")) {
    if (density) return Math.max(0.4, 0.81 * (density / 1800));
    return 0.81;
  }
  if (c.includes("kalksandstein")) {
    if (density) return Math.max(0.5, 0.99 * (density / 1800));
    return 0.99;
  }
  if (c.includes("porenbeton")) {
    if (density) return Math.max(0.07, 0.073 + 0.0002 * density);
    return 0.14;
  }
  if (c.includes("leichtbeton")) {
    if (density) return Math.max(0.27, 0.28 + 0.0009 * density);
    return 0.56;
  }
  if (c.includes("stahlbeton")) return 2.30;
  if (c.includes("beton") && !c.includes("d mm")) {
    if (density && density < 1500) return Math.max(0.27, 0.28 + 0.0009 * density);
    return 1.65;
  }
  if (c.includes("mauerwerk")) return 0.45;

  // --- Wood products ---
  if (
    c.includes("brettschichtholz") ||
    c.includes("konstruktionsvollholz") ||
    c.includes("vollholz") ||
    c.includes("bau-schnittholz") ||
    c.includes("balkenschichtholz")
  )
    return 0.13;
  if (c.includes("osb")) return 0.13;
  if (c.includes("sperrholz")) return 0.17;
  if (c.includes("holzfaserplatte") || c.includes("mdf") || c.includes("hdf")) return 0.10;
  if (c.includes("spanplatte")) return 0.13;
  if (c.includes("holzzementplatte")) return 0.26;
  if (c.includes("holzwerkstoffe") || c.includes("/ holz")) return 0.13;
  if (c.includes("vollholz") || c.includes("holz") && c.includes("rahmen")) return 0.13;

  // --- Plaster / Mortar ---
  if (c.includes("gipsputz") || (c.includes("gips") && c.includes("putz"))) return 0.35;
  if (c.includes("kalkzementputz") || (c.includes("kalkzement") && c.includes("putz"))) return 0.87;
  if (c.includes("kunstharzputz")) return 0.70;
  if (c.includes("außenputz") || c.includes("aussenputz")) return 0.87;
  if (c.includes("putz")) return 0.60;

  // --- Screed / concrete floor ---
  if (c.includes("estrich")) return 1.40;

  // --- Metals ---
  if (c.includes("stahl")) return 50.0;
  if (c.includes("aluminium")) return 160.0;

  // --- Glass ---
  if (c.includes("glas") && !c.includes("glaswolle")) return 0.96;

  // No thermal significance (coatings, hardware, sealants, systems, etc.)
  return null;
}

// ---------------------------------------------------------------------------
// CSV parser
// ---------------------------------------------------------------------------
let _cache: OBDMaterial[] | null = null;

export function loadOBDMaterials(): OBDMaterial[] {
  if (_cache) return _cache;

  const csvPath = path.join(
    path.dirname(fileURLToPath(import.meta.url)),
    "OBD_2024.csv",
  );

  if (!fs.existsSync(csvPath)) {
    console.warn("[obd] OBD_2024.csv nicht gefunden – Datenbank leer.");
    _cache = [];
    return _cache;
  }

  const raw = fs.readFileSync(csvPath, "utf-8");
  const lines = raw.split("\n");
  if (lines.length < 2) {
    _cache = [];
    return _cache;
  }

  // Parse header (semicolon-delimited)
  const header = lines[0].split(";");
  const idx = (name: string) => header.findIndex((h) => h.trim() === name);

  const iUUID = idx("UUID");
  const iName = idx("Name (de)");
  const iCat = idx("Kategorie (original)");
  const iDensity = idx("Rohdichte (kg/m3)");
  const iThickness = idx("Schichtdicke (m)");
  const iURL = idx("URL");

  const seen = new Set<string>();
  const result: OBDMaterial[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const cols = line.split(";");
    const uuid = cols[iUUID]?.trim();
    if (!uuid || seen.has(uuid)) continue;
    seen.add(uuid);

    const name = cols[iName]?.trim() ?? "";
    const category = cols[iCat]?.trim() ?? "";
    const densityRaw = cols[iDensity]?.trim().replace(",", ".");
    const thicknessRaw = cols[iThickness]?.trim().replace(",", ".");
    const url = cols[iURL]?.trim() ?? "";

    const density = densityRaw && !isNaN(Number(densityRaw)) ? Number(densityRaw) : null;
    const thickness = thicknessRaw && !isNaN(Number(thicknessRaw)) ? Number(thicknessRaw) : null;

    result.push({
      uuid,
      name,
      category,
      densityKgM3: density,
      defaultThicknessM: thickness,
      lambdaWmK: estimateLambda(category, density),
      url,
    });
  }

  _cache = result;
  console.log(`[obd] ${result.length} Materialien aus OBD_2024.csv geladen.`);
  return _cache;
}
