import { Router } from "express";
import { loadOBDMaterials } from "../data/obdParser.js";

export const obdRouter = Router();

// Pre-load on import so it's ready before first request
loadOBDMaterials();

/**
 * GET /api/obd/materials?q=<search>&limit=<n>
 * Returns OBD materials filtered by name/category, with estimated lambda.
 */
obdRouter.get("/obd/materials", (req, res) => {
  const q = String(req.query.q ?? "").toLowerCase().trim();
  const limit = Math.min(100, Math.max(1, Number(req.query.limit ?? 30)));

  const all = loadOBDMaterials();

  // Only return materials that have thermal relevance (lambdaWmK != null)
  const filtered = q
    ? all.filter(
        (m) =>
          m.lambdaWmK !== null &&
          (m.name.toLowerCase().includes(q) ||
            m.category.toLowerCase().includes(q)),
      )
    : all.filter((m) => m.lambdaWmK !== null);

  res.json({
    items: filtered.slice(0, limit),
    total: filtered.length,
  });
});
