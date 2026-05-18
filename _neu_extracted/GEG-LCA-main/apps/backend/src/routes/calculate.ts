import { Router } from "express";
import {
  calculateEnvelope,
  calculateHeatingDemand,
  calculateUValue,
  calculateWindowSolarGainKWhA,
  calculateEffectiveApertureAreaM2,
  referenceAreaFromGeometryM2,
  validateEnvelopeRequest,
  windowAreaM2,
} from "@geg/shared";
import type {
  BuildingGeometry,
  EnvelopeRequest,
  HeatingDemandInput,
  Orientation,
  WindowItem,
} from "@geg/shared";
import { findConstructionById } from "../data/constructions.js";

export const calculateRouter = Router();

calculateRouter.post("/calculate/u-value", (req, res) => {
  const { constructionId } = req.body ?? {};
  if (typeof constructionId !== "string" || constructionId.trim() === "") {
    return res.status(400).json({ error: "constructionId fehlt." });
  }
  const c = findConstructionById(constructionId);
  if (!c) {
    return res.status(404).json({ error: `Bauteil ${constructionId} nicht gefunden.` });
  }
  try {
    res.json(calculateUValue(c));
  } catch (err) {
    res.status(422).json({
      error: err instanceof Error ? err.message : "U-Wert-Berechnung fehlgeschlagen.",
    });
  }
});

calculateRouter.post("/calculate/envelope", (req, res) => {
  const body = req.body as EnvelopeRequest | undefined;
  if (!body || typeof body !== "object") {
    return res.status(400).json({ error: "Request body fehlt." });
  }
  const errs = validateEnvelopeRequest(body);
  if (errs.length > 0) return res.status(400).json({ errors: errs });

  const construction = body.externalWallConstructionId
    ? findConstructionById(body.externalWallConstructionId)
    : null;
  const hasOverride =
    body.wallExtras?.uValueOverrideWm2K !== undefined &&
    body.wallExtras.uValueOverrideWm2K > 0;
  if (!construction && !hasOverride) {
    return res.status(404).json({
      error: `Aussenwand-Bauteil ${body.externalWallConstructionId ?? "(leer)"} nicht gefunden.`,
    });
  }
  res.json(calculateEnvelope(body, construction ?? null, findConstructionById));
});

calculateRouter.post("/calculate/solar-gains", (req, res) => {
  const { windows } = (req.body ?? {}) as { windows?: WindowItem[] };
  if (!Array.isArray(windows)) {
    return res.status(400).json({ error: "windows[] fehlt." });
  }
  const byOrient: Record<Orientation, number> = {
    north: 0,
    south: 0,
    east: 0,
    west: 0,
  };
  const items = windows.map((w) => {
    const area = windowAreaM2(w);
    const aEff = calculateEffectiveApertureAreaM2(w);
    const gain = calculateWindowSolarGainKWhA(w);
    byOrient[w.orientation] += gain;
    return {
      id: w.id,
      orientation: w.orientation,
      areaM2: area,
      effectiveApertureAreaM2: aEff,
      solarGainKWhA: gain,
    };
  });
  const total = Object.values(byOrient).reduce((s, v) => s + v, 0);
  res.json({ items, byOrientation: byOrient, totalKWhA: total });
});

calculateRouter.post("/calculate/heating-demand", (req, res) => {
  const body = req.body as Partial<HeatingDemandInput> & {
    envelopeRequest: EnvelopeRequest;
  } | undefined;
  if (!body || !body.envelopeRequest) {
    return res.status(400).json({ error: "envelopeRequest erforderlich." });
  }
  const errs = validateEnvelopeRequest(body.envelopeRequest);
  if (errs.length > 0) return res.status(400).json({ errors: errs });

  // Wall override has priority; if it's set we don't require a construction id.
  const constructionId = body.envelopeRequest.externalWallConstructionId;
  const construction = constructionId ? findConstructionById(constructionId) : null;
  const hasOverride =
    body.envelopeRequest.wallExtras?.uValueOverrideWm2K !== undefined &&
    body.envelopeRequest.wallExtras.uValueOverrideWm2K > 0;
  if (!construction && !hasOverride) {
    return res.status(404).json({
      error: `Aussenwand-Bauteil ${constructionId ?? "(leer)"} nicht gefunden.`,
    });
  }
  const env = calculateEnvelope(
    body.envelopeRequest,
    construction ?? null,
    findConstructionById,
  );

  const geo: BuildingGeometry = body.envelopeRequest.buildingGeometry;
  const refArea =
    body.referenceAreaM2 && body.referenceAreaM2 > 0
      ? body.referenceAreaM2
      : referenceAreaFromGeometryM2(geo);

  if (!body.ventilation) {
    return res.status(400).json({ error: "ventilation erforderlich." });
  }
  const input: HeatingDemandInput = {
    envelope: env,
    ventilation: body.ventilation,
    heating: body.heating,
    hotWater: body.hotWater,
    distribution: body.distribution,
    pv: body.pv,
    buildingGeometry: geo,
    referenceAreaM2: refArea,
  };
  res.json({ envelope: env, heating: calculateHeatingDemand(input) });
});
