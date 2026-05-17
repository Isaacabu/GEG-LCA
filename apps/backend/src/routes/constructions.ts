import { Router } from "express";
import {
  CONSTRUCTIONS,
  constructionsByElementType,
} from "../data/constructions.js";
import type { ElementType } from "@geg/shared";

export const constructionsRouter = Router();

constructionsRouter.get("/constructions", (_req, res) => {
  res.json({ items: CONSTRUCTIONS });
});

// Convenience routes by element type
const aliasMap: Record<string, ElementType> = {
  walls: "externalWall",
  "external-wall": "externalWall",
  roofs: "roof",
  floors: "floor",
  windows: "window",
  doors: "door",
};

constructionsRouter.get("/constructions/:alias", (req, res) => {
  const alias = req.params.alias;
  const mapped = aliasMap[alias];
  const valid: ElementType[] = ["externalWall", "roof", "floor", "window", "door"];
  const elementType =
    mapped ?? (valid.includes(alias as ElementType) ? (alias as ElementType) : null);
  if (!elementType) {
    return res.status(400).json({ error: `Unbekannter elementType: ${alias}` });
  }
  res.json({ items: constructionsByElementType(elementType) });
});
