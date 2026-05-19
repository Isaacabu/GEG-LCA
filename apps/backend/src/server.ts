import express from "express";
import cors from "cors";
import { healthRouter } from "./routes/health.js";
import { materialsRouter } from "./routes/materials.js";
import { constructionsRouter } from "./routes/constructions.js";
import { calculateRouter } from "./routes/calculate.js";
import { obdRouter } from "./routes/obd.js";

const PORT = Number(process.env.PORT ?? 4001);

const app = express();
app.use(cors());
app.use(express.json({ limit: "1mb" }));

app.use("/api", healthRouter);
app.use("/api", materialsRouter);
app.use("/api", constructionsRouter);
app.use("/api", calculateRouter);
app.use("/api", obdRouter);

app.use((_req, res) => {
  res.status(404).json({ error: "Endpunkt nicht gefunden." });
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[geg-backend] http://localhost:${PORT}/api/health`);
});
