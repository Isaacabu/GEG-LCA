import type {
  Construction,
  DistributionInput,
  EnvelopeRequest,
  EnvelopeResult,
  HeatingDemandResult,
  HeatingInput,
  HotWaterInput,
  Material,
  Orientation,
  PVInput,
  UValueResult,
  VentilationInput,
  WindowItem,
} from "@geg/shared";

const API_BASE = "/api";

async function jsonFetch<T>(input: string, init?: RequestInit): Promise<T> {
  const res = await fetch(input, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const msg =
      body?.error ??
      (Array.isArray(body?.errors)
        ? body.errors.map((e: any) => `${e.path}: ${e.message}`).join(" | ")
        : null) ??
      `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body as T;
}

export const api = {
  async health() {
    return jsonFetch<{ ok: boolean }>(`${API_BASE}/health`);
  },
  async listMaterials() {
    return jsonFetch<{ items: Material[] }>(`${API_BASE}/materials`);
  },
  async listConstructions() {
    return jsonFetch<{ items: Construction[] }>(`${API_BASE}/constructions`);
  },
  async listByElement(alias: "walls" | "roofs" | "floors" | "windows" | "doors") {
    return jsonFetch<{ items: Construction[] }>(
      `${API_BASE}/constructions/${alias}`,
    );
  },
  async calcUValue(constructionId: string) {
    return jsonFetch<UValueResult>(`${API_BASE}/calculate/u-value`, {
      method: "POST",
      body: JSON.stringify({ constructionId }),
    });
  },
  async calcEnvelope(req: EnvelopeRequest) {
    return jsonFetch<EnvelopeResult>(`${API_BASE}/calculate/envelope`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
  async calcSolarGains(windows: WindowItem[]) {
    return jsonFetch<{
      items: Array<{
        id: string;
        orientation: Orientation;
        areaM2: number;
        effectiveApertureAreaM2: number;
        solarGainKWhA: number;
      }>;
      byOrientation: Record<Orientation, number>;
      totalKWhA: number;
    }>(`${API_BASE}/calculate/solar-gains`, {
      method: "POST",
      body: JSON.stringify({ windows }),
    });
  },
  async calcHeatingDemand(payload: {
    envelopeRequest: EnvelopeRequest;
    ventilation: VentilationInput;
    heating?: HeatingInput;
    hotWater?: HotWaterInput;
    distribution?: DistributionInput;
    pv?: PVInput;
    referenceAreaM2?: number;
  }) {
    return jsonFetch<{ envelope: EnvelopeResult; heating: HeatingDemandResult }>(
      `${API_BASE}/calculate/heating-demand`,
      { method: "POST", body: JSON.stringify(payload) },
    );
  },
  async searchOBD(q: string, limit = 30) {
    const params = new URLSearchParams({ q, limit: String(limit) });
    return jsonFetch<{
      items: Array<{
        uuid: string;
        name: string;
        category: string;
        densityKgM3: number | null;
        defaultThicknessM: number | null;
        lambdaWmK: number | null;
        url: string;
      }>;
      total: number;
    }>(`${API_BASE}/obd/materials?${params}`);
  },
};
