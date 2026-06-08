import type {
  AirTightnessClass,
  DistributionInput,
  EnergyCarrier,
  HeatEmission,
  HeatingControl,
  HeatingInput,
  HeatingSystem,
  HotWaterCirculation,
  HotWaterInput,
  HotWaterStorage,
  HotWaterSystem,
  PVInput,
  PVOption,
  PipeInsulation,
  PipeRouting,
  SupplyTempBand,
  VentilationControl,
  VentilationInput,
  VentilationKind,
} from "@geg/shared";

const VENT_KINDS: { value: VentilationKind; label: string }[] = [
  { value: "windowVentilation", label: "Fensterlüftung" },
  { value: "freeVent", label: "freie Lüftung" },
  { value: "shaftVent", label: "Schachtlüftung" },
  { value: "exhaustOnly", label: "Abluftanlage" },
  { value: "centralBalanced", label: "zentrale Zu-/Abluftanlage" },
  { value: "decentralBalanced", label: "dezentrale Lüftungsanlage" },
  { value: "balancedWithHRV", label: "Lüftungsanlage mit WRG" },
  { value: "balancedNoHRV", label: "Lüftungsanlage ohne WRG" },
  { value: "commercial", label: "gewerbliche Lüftung" },
  { value: "custom", label: "benutzerdefiniert" },
];

const TIGHTNESS: { value: AirTightnessClass; label: string }[] = [
  { value: "veryTight", label: "sehr dicht" },
  { value: "normal", label: "normal dicht" },
  { value: "slightlyLeaky", label: "Altbau leicht undicht" },
  { value: "veryLeaky", label: "Altbau stark undicht" },
  { value: "withBlowerDoor", label: "Blower-Door vorhanden" },
  { value: "unknown", label: "unbekannt" },
];

const VENT_CTRL: { value: VentilationControl; label: string }[] = [
  { value: "manual", label: "manuell" },
  { value: "timer", label: "zeitgesteuert" },
  { value: "humidity", label: "feuchtegefuehrt" },
  { value: "co2", label: "CO2-gesteuert" },
  { value: "demand", label: "bedarfsgefuehrt" },
  { value: "smartHome", label: "Smart Home" },
];

const HEAT_SYS: { value: HeatingSystem; label: string; isHP: boolean }[] = [
  { value: "gasCondensing", label: "Gas-Brennwert", isHP: false },
  { value: "gasLowTemp", label: "Gas-Niedertemperatur", isHP: false },
  { value: "gasOld", label: "Gas-Altgeraet", isHP: false },
  { value: "oilCondensing", label: "Oel-Brennwert", isHP: false },
  { value: "oilOld", label: "Oel-Altgeraet", isHP: false },
  { value: "hpAir", label: "Luft-Wasser-WP", isHP: true },
  { value: "hpGround", label: "Sole-Wasser-WP", isHP: true },
  { value: "hpWater", label: "Wasser-Wasser-WP", isHP: true },
  { value: "districtHeating", label: "Fernwaerme", isHP: false },
  { value: "pellet", label: "Pelletheizung", isHP: false },
  { value: "logGasifier", label: "Holzvergaser", isHP: false },
  { value: "logBoiler", label: "Scheitholz", isHP: false },
  { value: "chip", label: "Hackschnitzel", isHP: false },
  { value: "directElectric", label: "Stromdirektheizung", isHP: false },
  { value: "nightStorage", label: "Nachtspeicher", isHP: false },
  { value: "hybrid", label: "Hybridheizung", isHP: false },
  { value: "solarSupport", label: "Solarthermie-Unterstuetzung", isHP: false },
  { value: "chp", label: "BHKW", isHP: false },
  { value: "custom", label: "benutzerdefiniert", isHP: false },
];

const CARRIERS: { value: EnergyCarrier; label: string }[] = [
  { value: "naturalGas", label: "Erdgas" },
  { value: "heatingOil", label: "Heizoel" },
  { value: "electricity", label: "Strom" },
  { value: "districtHeat", label: "Fernwaerme" },
  { value: "pellets", label: "Pellets" },
  { value: "wood", label: "Holz" },
  { value: "lpg", label: "Fluessiggas" },
  { value: "biomass", label: "Biomasse" },
  { value: "solarThermal", label: "Solarthermie" },
  { value: "ambient", label: "Umweltwaerme" },
  { value: "hydrogenReady", label: "Wasserstoff-ready" },
  { value: "custom", label: "benutzerdefiniert" },
];

const EMISSIONS: { value: HeatEmission; label: string }[] = [
  { value: "radiatorsOld", label: "Heizkoerper alt" },
  { value: "radiatorsModern", label: "Heizkoerper modern" },
  { value: "underfloor", label: "Fussbodenheizung" },
  { value: "wall", label: "Wandheizung" },
  { value: "ceiling", label: "Deckenheizung" },
  { value: "airHeating", label: "Luftheizung" },
  { value: "fanCoil", label: "Geblaesekonvektor" },
  { value: "mixed", label: "Mischsystem" },
];

const SUPPLY: { value: SupplyTempBand; label: string }[] = [
  { value: "t35", label: "<=35 °C" },
  { value: "t36_45", label: "36-45 °C" },
  { value: "t46_55", label: "46-55 °C" },
  { value: "t56_70", label: "56-70 °C" },
  { value: "t70plus", label: ">70 °C" },
  { value: "unknown", label: "unbekannt" },
];

const HEAT_CTRL: { value: HeatingControl; label: string }[] = [
  { value: "noModern", label: "keine moderne Regelung" },
  { value: "roomThermostats", label: "Raumthermostate" },
  { value: "weather", label: "witterungsgefuehrt" },
  { value: "nightSetback", label: "Nachtabsenkung" },
  { value: "perRoom", label: "Einzelraumregelung" },
  { value: "smartHome", label: "Smart Home" },
  { value: "ai", label: "KI-/Bedarfsregelung" },
];

const DHW_SYS: { value: HotWaterSystem; label: string }[] = [
  { value: "viaCentralHeating", label: "ueber Zentralheizung" },
  { value: "electricInstant", label: "elektr. Durchlauferhitzer" },
  { value: "gasInstant", label: "Gas-Durchlauferhitzer" },
  { value: "hpBoiler", label: "Waermepumpenboiler" },
  { value: "solarThermal", label: "Solarthermie" },
  { value: "freshWaterStation", label: "Frischwasserstation" },
  { value: "combiStorage", label: "Kombispeicher" },
  { value: "custom", label: "benutzerdefiniert" },
];

const DHW_STORAGE: { value: HotWaterStorage; label: string }[] = [
  { value: "none", label: "kein Speicher" },
  { value: "small", label: "Kleinspeicher" },
  { value: "tank", label: "Warmwasserspeicher" },
  { value: "buffer", label: "Pufferspeicher" },
  { value: "combi", label: "Kombispeicher" },
  { value: "poorlyInsulated", label: "schlecht gedaemmt" },
  { value: "wellInsulated", label: "gut gedaemmt" },
  { value: "unknown", label: "unbekannt" },
];

const CIRC: { value: HotWaterCirculation; label: string }[] = [
  { value: "none", label: "keine" },
  { value: "permanent", label: "permanent" },
  { value: "timer", label: "zeitgesteuert" },
  { value: "demand", label: "bedarfsgesteuert" },
  { value: "unknown", label: "unbekannt" },
];

const PIPE_INSUL: { value: PipeInsulation; label: string }[] = [
  { value: "none", label: "keine" },
  { value: "weak", label: "schwach" },
  { value: "normal", label: "normal" },
  { value: "good", label: "gut" },
  { value: "veryGood", label: "sehr gut" },
  { value: "unknown", label: "unbekannt" },
];

const ROUTING: { value: PipeRouting; label: string }[] = [
  { value: "heated", label: "in beheizter Zone" },
  { value: "partlyUnheated", label: "teils unbeheizt" },
  { value: "mostlyUnheated", label: "ueberwiegend unbeheizt" },
  { value: "basement", label: "Keller" },
  { value: "outside", label: "Aussenbereich" },
  { value: "unknown", label: "unbekannt" },
];

const PV_OPTS: { value: PVOption; label: string }[] = [
  { value: "none", label: "keine Anlage" },
  { value: "pvOnly", label: "PV vorhanden" },
  { value: "solarThermalDHW", label: "Solarthermie Warmwasser" },
  { value: "solarThermalHeating", label: "Solarthermie Heizung" },
  { value: "pvWithHP", label: "PV + Waermepumpe" },
  { value: "batteryStorage", label: "Batteriespeicher" },
  { value: "custom", label: "benutzerdefiniert" },
];

export function HvacSection({
  ventilation, setVentilation,
  heating, setHeating,
  hotWater, setHotWater,
  distribution, setDistribution,
  pv, setPv,
  expertMode,
}: {
  ventilation: VentilationInput;
  setVentilation: (v: VentilationInput) => void;
  heating: HeatingInput;
  setHeating: (h: HeatingInput) => void;
  hotWater: HotWaterInput;
  setHotWater: (h: HotWaterInput) => void;
  distribution: DistributionInput;
  setDistribution: (d: DistributionInput) => void;
  pv: PVInput;
  setPv: (p: PVInput) => void;
  expertMode: boolean;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      <div>
        <h3 style={{ marginBottom: 10 }}>1 · Lueftung</h3>
        <div className="grid grid-3" style={{ gap: 14 }}>
          <label className="field">
            <span className="field-label">Lueftungsart</span>
            <select className="select" value={ventilation.kind}
              onChange={(e) => {
                const k = e.target.value as VentilationKind;
                const hrv = k === "balancedWithHRV";
                setVentilation({ ...ventilation, kind: k, hasHeatRecovery: hrv });
              }}>
              {VENT_KINDS.map((v) => (<option key={v.value} value={v.value}>{v.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Luftwechselrate n [1/h]</span>
            <input className="input" type="number" min={0} step={0.05}
              value={ventilation.airChangeRatePerH}
              onChange={(e) => setVentilation({ ...ventilation, airChangeRatePerH: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Luftdichtheit</span>
            <select className="select" value={ventilation.tightnessClass}
              onChange={(e) => setVentilation({ ...ventilation, tightnessClass: e.target.value as AirTightnessClass })}>
              {TIGHTNESS.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">WRG?</span>
            <select className="select" value={ventilation.hasHeatRecovery ? "yes" : "no"}
              onChange={(e) => setVentilation({ ...ventilation, hasHeatRecovery: e.target.value === "yes" })}>
              <option value="no">nein</option>
              <option value="yes">ja</option>
            </select>
          </label>
          <label className="field">
            <span className="field-label">WRG-Wirkungsgrad [0..1]</span>
            <input className="input" type="number" min={0} max={1} step={0.05}
              value={ventilation.hrvEfficiency}
              onChange={(e) => setVentilation({ ...ventilation, hrvEfficiency: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Regelung</span>
            <select className="select" value={ventilation.control}
              onChange={(e) => setVentilation({ ...ventilation, control: e.target.value as VentilationControl })}>
              {VENT_CTRL.map((v) => (<option key={v.value} value={v.value}>{v.label}</option>))}
            </select>
          </label>
          {expertMode && (
            <>
              <label className="field">
                <span className="field-label">n50 [1/h]</span>
                <input className="input" type="number" min={0} step={0.1}
                  value={ventilation.n50PerH ?? 0}
                  onChange={(e) => setVentilation({ ...ventilation, n50PerH: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Ventilatorleistung [W]</span>
                <input className="input" type="number" min={0} step={1}
                  value={ventilation.fanPowerW}
                  onChange={(e) => setVentilation({ ...ventilation, fanPowerW: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">Betrieb [h/Tag]</span>
                <input className="input" type="number" min={0} max={24} step={1}
                  value={ventilation.runHoursPerDay}
                  onChange={(e) => setVentilation({ ...ventilation, runHoursPerDay: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">SFP [Wh/m³]</span>
                <input className="input" type="number" min={0} step={0.05}
                  value={ventilation.sfpWhPerM3 ?? 0}
                  onChange={(e) => setVentilation({ ...ventilation, sfpWhPerM3: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Min. Volumenstrom [m³/h]</span>
                <input className="input" type="number" min={0} step={5}
                  value={ventilation.minVolumeFlowM3H ?? 0}
                  onChange={(e) => setVentilation({ ...ventilation, minVolumeFlowM3H: Number(e.target.value) || undefined })} />
              </label>
            </>
          )}
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 10 }}>2 · Heizung</h3>
        <div className="grid grid-3" style={{ gap: 14 }}>
          <label className="field">
            <span className="field-label">Heizsystem</span>
            <select className="select" value={heating.system}
              onChange={(e) => {
                const s = e.target.value as HeatingSystem;
                const meta = HEAT_SYS.find((h) => h.value === s)!;
                setHeating({ ...heating, system: s, isHeatPump: meta.isHP });
              }}>
              {HEAT_SYS.map((h) => (<option key={h.value} value={h.value}>{h.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Energietraeger</span>
            <select className="select" value={heating.carrier}
              onChange={(e) => setHeating({ ...heating, carrier: e.target.value as EnergyCarrier })}>
              {CARRIERS.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">{heating.isHeatPump ? "JAZ / COP" : "Wirkungsgrad [0..1]"}</span>
            <input className="input" type="number" min={0} step={0.05}
              value={heating.isHeatPump ? (heating.copJaz ?? 3.5) : heating.efficiency}
              onChange={(e) => {
                const v = Number(e.target.value) || 0;
                if (heating.isHeatPump) setHeating({ ...heating, copJaz: v });
                else setHeating({ ...heating, efficiency: v });
              }} />
          </label>
          <label className="field">
            <span className="field-label">Vorlauftemperatur</span>
            <select className="select" value={heating.supplyTemp}
              onChange={(e) => setHeating({ ...heating, supplyTemp: e.target.value as SupplyTempBand })}>
              {SUPPLY.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Waermeuebergabe</span>
            <select className="select" value={heating.emission}
              onChange={(e) => setHeating({ ...heating, emission: e.target.value as HeatEmission })}>
              {EMISSIONS.map((e2) => (<option key={e2.value} value={e2.value}>{e2.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Regelung</span>
            <select className="select" value={heating.control}
              onChange={(e) => setHeating({ ...heating, control: e.target.value as HeatingControl })}>
              {HEAT_CTRL.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
            </select>
          </label>
          {expertMode && (
            <>
              <label className="field">
                <span className="field-label">Baujahr</span>
                <input className="input" type="number" min={0} step={1}
                  value={heating.yearBuilt ?? 0}
                  onChange={(e) => setHeating({ ...heating, yearBuilt: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Nennleistung [kW]</span>
                <input className="input" type="number" min={0} step={0.5}
                  value={heating.nominalPowerKW ?? 0}
                  onChange={(e) => setHeating({ ...heating, nominalPowerKW: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Pumpenstrom [W]</span>
                <input className="input" type="number" min={0} step={1}
                  value={heating.pumpPowerW}
                  onChange={(e) => setHeating({ ...heating, pumpPowerW: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">hydraul. Abgleich</span>
                <select className="select" value={heating.hydraulicBalanced ? "yes" : "no"}
                  onChange={(e) => setHeating({ ...heating, hydraulicBalanced: e.target.value === "yes" })}>
                  <option value="no">nein</option>
                  <option value="yes">ja</option>
                </select>
              </label>
            </>
          )}
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 10 }}>3 · Warmwasser</h3>
        <div className="grid grid-3" style={{ gap: 14 }}>
          <label className="field">
            <span className="field-label">System</span>
            <select className="select" value={hotWater.system}
              onChange={(e) => setHotWater({ ...hotWater, system: e.target.value as HotWaterSystem })}>
              {DHW_SYS.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Personen</span>
            <input className="input" type="number" min={0} step={1}
              value={hotWater.persons}
              onChange={(e) => setHotWater({ ...hotWater, persons: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">l/Person/Tag</span>
            <input className="input" type="number" min={0} step={1}
              value={hotWater.litresPerPersonPerDay}
              onChange={(e) => setHotWater({ ...hotWater, litresPerPersonPerDay: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Speicher</span>
            <select className="select" value={hotWater.storage}
              onChange={(e) => setHotWater({ ...hotWater, storage: e.target.value as HotWaterStorage })}>
              {DHW_STORAGE.map((s) => (<option key={s.value} value={s.value}>{s.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Speicherverlust [kWh/Tag]</span>
            <input className="input" type="number" min={0} step={0.1}
              value={hotWater.storageLossKWhPerDay}
              onChange={(e) => setHotWater({ ...hotWater, storageLossKWhPerDay: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Zirkulation</span>
            <select className="select" value={hotWater.circulation}
              onChange={(e) => setHotWater({ ...hotWater, circulation: e.target.value as HotWaterCirculation })}>
              {CIRC.map((c) => (<option key={c.value} value={c.value}>{c.label}</option>))}
            </select>
          </label>
          {expertMode && (
            <>
              <label className="field">
                <span className="field-label">Setpoint [°C]</span>
                <input className="input" type="number" min={20} max={90} step={1}
                  value={hotWater.setpointC}
                  onChange={(e) => setHotWater({ ...hotWater, setpointC: Number(e.target.value) || 55 })} />
              </label>
              <label className="field">
                <span className="field-label">Solaranteil [%]</span>
                <input className="input" type="number" min={0} max={100} step={1}
                  value={hotWater.solarFractionPct}
                  onChange={(e) => setHotWater({ ...hotWater, solarFractionPct: Number(e.target.value) || 0 })} />
              </label>
            </>
          )}
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 10 }}>4 · Verteilung / Speicher</h3>
        <div className="grid grid-3" style={{ gap: 14 }}>
          <label className="field">
            <span className="field-label">Rohrlaenge [m]</span>
            <input className="input" type="number" min={0} step={1}
              value={distribution.pipeLengthM}
              onChange={(e) => setDistribution({ ...distribution, pipeLengthM: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Rohrdaemmung</span>
            <select className="select" value={distribution.insulation}
              onChange={(e) => setDistribution({ ...distribution, insulation: e.target.value as PipeInsulation })}>
              {PIPE_INSUL.map((p) => (<option key={p.value} value={p.value}>{p.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Leitungsfuehrung</span>
            <select className="select" value={distribution.routing}
              onChange={(e) => setDistribution({ ...distribution, routing: e.target.value as PipeRouting })}>
              {ROUTING.map((p) => (<option key={p.value} value={p.value}>{p.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Pumpenleistung [W]</span>
            <input className="input" type="number" min={0} step={1}
              value={distribution.pumpPowerW}
              onChange={(e) => setDistribution({ ...distribution, pumpPowerW: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Pumpenlaufzeit [h/a]</span>
            <input className="input" type="number" min={0} step={100}
              value={distribution.pumpHoursPerYear}
              onChange={(e) => setDistribution({ ...distribution, pumpHoursPerYear: Number(e.target.value) || 0 })} />
          </label>
          {expertMode && (
            <>
              <label className="field">
                <span className="field-label">Speicheranzahl</span>
                <input className="input" type="number" min={0} step={1}
                  value={distribution.storageCount}
                  onChange={(e) => setDistribution({ ...distribution, storageCount: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">Speichergroesse [L]</span>
                <input className="input" type="number" min={0} step={10}
                  value={distribution.storageSizeL}
                  onChange={(e) => setDistribution({ ...distribution, storageSizeL: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">Verlust [Wh/Tag·L]</span>
                <input className="input" type="number" min={0} step={0.5}
                  value={distribution.storageLossWhPerDayPerL}
                  onChange={(e) => setDistribution({ ...distribution, storageLossWhPerDayPerL: Number(e.target.value) || 0 })} />
              </label>
            </>
          )}
        </div>
      </div>

      <div>
        <h3 style={{ marginBottom: 10 }}>5 · PV / Solarthermie</h3>
        <div className="grid grid-3" style={{ gap: 14 }}>
          <label className="field">
            <span className="field-label">Option</span>
            <select className="select" value={pv.option}
              onChange={(e) => setPv({ ...pv, option: e.target.value as PVOption })}>
              {PV_OPTS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">PV [kWp]</span>
            <input className="input" type="number" min={0} step={0.5}
              value={pv.pvPeakKWp}
              onChange={(e) => setPv({ ...pv, pvPeakKWp: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">PV-Ertrag [kWh/a]</span>
            <input className="input" type="number" min={0} step={100}
              value={pv.pvYieldKWhPerYear}
              onChange={(e) => setPv({ ...pv, pvYieldKWhPerYear: Number(e.target.value) || 0 })} />
          </label>
          <label className="field">
            <span className="field-label">Eigenverbrauch [%]</span>
            <input className="input" type="number" min={0} max={100} step={1}
              value={pv.selfConsumptionPct}
              onChange={(e) => setPv({ ...pv, selfConsumptionPct: Number(e.target.value) || 0 })} />
          </label>
          {expertMode && (
            <>
              <label className="field">
                <span className="field-label">Batterie [kWh]</span>
                <input className="input" type="number" min={0} step={0.5}
                  value={pv.batteryKWh ?? 0}
                  onChange={(e) => setPv({ ...pv, batteryKWh: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Solarthermie [m²]</span>
                <input className="input" type="number" min={0} step={0.5}
                  value={pv.solarThermalAreaM2 ?? 0}
                  onChange={(e) => setPv({ ...pv, solarThermalAreaM2: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Solarthermie [kWh/a]</span>
                <input className="input" type="number" min={0} step={100}
                  value={pv.solarThermalYieldKWhPerYear ?? 0}
                  onChange={(e) => setPv({ ...pv, solarThermalYieldKWhPerYear: Number(e.target.value) || undefined })} />
              </label>
              <label className="field">
                <span className="field-label">Deckung WW [%]</span>
                <input className="input" type="number" min={0} max={100} step={1}
                  value={pv.coverageDHWPct}
                  onChange={(e) => setPv({ ...pv, coverageDHWPct: Number(e.target.value) || 0 })} />
              </label>
              <label className="field">
                <span className="field-label">Deckung Heizung [%]</span>
                <input className="input" type="number" min={0} max={100} step={1}
                  value={pv.coverageHeatPct}
                  onChange={(e) => setPv({ ...pv, coverageHeatPct: Number(e.target.value) || 0 })} />
              </label>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
