import { Router } from "express";
import { MATERIALS } from "../data/materials.js";

export const materialsRouter = Router();

materialsRouter.get("/materials", (_req, res) => {
  res.json({ items: MATERIALS });
});
