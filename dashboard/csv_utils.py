import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

NAME_KEYS = ["name", "material", "produkt", "bezeichnung", "produktname", "produkt name"]
PRODUCER_KEYS = ["producer", "hersteller", "lieferant", "company", "firma"]
CATEGORY_KEYS = ["category", "kategorie", "gruppe", "typ", "productgroup", "produktgruppe"]
U_VALUE_KEYS = ["u_wert", "u-wert", "uwert", "u value", "transmissionswärmeverlust", "wärmedurchgangskoeffizient", "transmissionskoeffizient"]
CO2_KEYS = ["co2", "co₂", "co2e", "co2-e", "co2e/m3", "co2e/m²", "kg co2", "kg co2e"]
NOTES_KEYS = ["notes", "bemerkungen", "beschreibung", "comment", "remark"]


def list_data_files() -> List[str]:
    if not DATA_DIR.exists():
        return []
    return sorted([path.name for path in DATA_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".csv"])


def detect_delimiter(sample: str) -> str:
    delimiters = [",", ";", "\t", "|"]
    best = ","
    best_count = sample.count(best)
    for delim in delimiters:
        count = sample.count(delim)
        if count > best_count:
            best = delim
            best_count = count
    return best


def normalize_header(name: str) -> str:
    return name.strip().lower().replace("\ufeff", "").replace(" ", "_").replace("-", "_")


def find_column(header_map: Dict[str, str], candidates: Iterable[str]) -> Optional[str]:
    for raw_name, normalized in header_map.items():
        for candidate in candidates:
            if candidate in normalized:
                return raw_name
    return None


def parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def read_csv_rows(filename: str) -> List[Dict[str, str]]:
    csv_path = DATA_DIR / filename
    if not csv_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {csv_path}")

    raw = csv_path.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise UnicodeDecodeError("csv", b"", 0, 1, f"Keine unterstützte Kodierung für {csv_path.name}")

    sample = text[:4096]
    delimiter = detect_delimiter(sample)
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return [
        {key.strip(): (value or "").strip() for key, value in row.items()}
        for row in reader
    ]


def read_csv_bytes(raw: bytes) -> List[Dict[str, str]]:
    """Wie read_csv_rows, aber aus einem hochgeladenen Byte-Puffer (kein Dateipfad).

    Erkennt Kodierung (utf-8-sig → cp1252 → latin-1) und Trennzeichen automatisch.
    """
    text = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Keine unterstützte Zeichenkodierung (utf-8/cp1252/latin-1).")

    delimiter = detect_delimiter(text[:4096])
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    rows: List[Dict[str, str]] = []
    for row in reader:
        rows.append({
            (key or "").strip(): (value or "").strip()
            for key, value in row.items()
            if key is not None
        })
    return rows


def _cell_str(value: object) -> str:
    """Excel-Zellwert → String. Ganzzahlige Floats (z. B. Jahr 2024.0) ohne .0."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _read_xlsx(raw: bytes) -> List[Dict[str, str]]:
    try:
        import openpyxl
    except ImportError:
        raise ValueError("Excel-Import (.xlsx) benötigt das Paket 'openpyxl' – bitte installieren "
                         "oder die Datei als CSV exportieren.")
    from io import BytesIO
    wb = openpyxl.load_workbook(BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active
    if ws is None:
        return []
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header = next(rows_iter)
    except StopIteration:
        return []
    headers = [_cell_str(h).strip() for h in header]

    out: List[Dict[str, str]] = []
    for values in rows_iter:
        if values is None:
            continue
        if all(v is None or _cell_str(v).strip() == "" for v in values):
            continue  # Leerzeile überspringen
        row: Dict[str, str] = {}
        for idx, head in enumerate(headers):
            if not head:
                continue
            cell = values[idx] if idx < len(values) else None
            row[head] = _cell_str(cell).strip()
        out.append(row)
    return out


def _read_xls(raw: bytes) -> List[Dict[str, str]]:
    try:
        import xlrd
    except ImportError:
        raise ValueError("Alte .xls-Dateien benötigen das Paket 'xlrd' – bitte die Datei als "
                         ".xlsx oder .csv exportieren.")
    book = xlrd.open_workbook(file_contents=raw)
    sheet = book.sheet_by_index(0)
    if sheet.nrows == 0:
        return []
    headers = [_cell_str(sheet.cell_value(0, c)).strip() for c in range(sheet.ncols)]
    out: List[Dict[str, str]] = []
    for r in range(1, sheet.nrows):
        values = [sheet.cell_value(r, c) for c in range(sheet.ncols)]
        if all(_cell_str(v).strip() == "" for v in values):
            continue
        row: Dict[str, str] = {}
        for c, head in enumerate(headers):
            if not head:
                continue
            row[head] = _cell_str(values[c]).strip()
        out.append(row)
    return out


def read_excel_bytes(raw: bytes, filename: str = "") -> List[Dict[str, str]]:
    """Excel-Upload (.xlsx/.xlsm/.xls) → Zeilen als Dicts (1. Zeile = Kopfzeile)."""
    name = (filename or "").lower()
    if name.endswith(".xls") and not name.endswith(".xlsx"):
        return _read_xls(raw)
    return _read_xlsx(raw)


def extract_material_data(row: Dict[str, str]) -> Optional[Dict[str, Optional[object]]]:
    header_map = {key: normalize_header(key) for key in row.keys()}

    name_key = find_column(header_map, NAME_KEYS)
    if not name_key:
        return None

    u_key = find_column(header_map, U_VALUE_KEYS)
    co2_key = find_column(header_map, CO2_KEYS)
    producer_key = find_column(header_map, PRODUCER_KEYS)
    category_key = find_column(header_map, CATEGORY_KEYS)
    notes_key = find_column(header_map, NOTES_KEYS)

    return {
        "name": row.get(name_key, "").strip(),
        "producer": row.get(producer_key, "").strip() if producer_key else "",
        "category": row.get(category_key, "").strip() if category_key else "",
        "u_value": parse_float(row.get(u_key)) if u_key else None,
        "embodied_co2": parse_float(row.get(co2_key)) if co2_key else None,
        "notes": row.get(notes_key, "").strip() if notes_key else "",
    }


def _is_obd_export(rows: List[Dict[str, str]]) -> bool:
    """Erkennt das offizielle ÖKOBAUDAT-Exportformat (UUID + Modul-Spalten)."""
    if not rows:
        return False
    keys = set(rows[0].keys())
    return "UUID" in keys and "Modul" in keys and "Name (de)" in keys


def _obd_gwp(row: Dict[str, str]) -> Optional[float]:
    """GWP des Datensatzes: EN 15804+A1-Spalte 'GWP', sonst 'GWPtotal (A2)'."""
    for key in ("GWP", "GWPtotal (A2)"):
        value = parse_float(row.get(key))
        if value is not None:
            return value
    return None


def import_obd_export(rows: List[Dict[str, str]], model_class):
    """Import des offiziellen ÖKOBAUDAT-Exports.

    Je Datensatz (UUID) wird die Zeile des Moduls A1–A3 (Herstellung) übernommen –
    das ist der Kennwert für 'graue Emissionen'. Andere Module (C/D, B6 …) werden
    bewusst nicht vermischt.
    """
    a1a3 = {}
    for row in rows:
        if (row.get("Modul") or "").strip() == "A1-A3":
            uuid = (row.get("UUID") or "").strip()
            if uuid and uuid not in a1a3:
                a1a3[uuid] = row

    objects = []
    for uuid, row in a1a3.items():
        gwp = _obd_gwp(row)
        qty = parse_float(row.get("Bezugsgroesse")) or 1.0
        unit = (row.get("Bezugseinheit") or "").strip()
        density = parse_float(row.get("Rohdichte (kg/m3)"))
        # GWP je kg, sofern aus Einheit + Rohdichte umrechenbar (Vergleichswert)
        per_kg = None
        if gwp is not None and qty > 0:
            if unit == "kg":
                per_kg = gwp / qty
            elif unit == "m3" and density and density > 0:
                per_kg = gwp / (qty * density)
        objects.append(model_class(
            name=(row.get("Name (de)") or "").strip()[:300],
            producer=(row.get("Declaration owner") or "").strip()[:300],
            category=(row.get("Kategorie (original)") or "").strip()[:300],
            uuid=uuid,
            dataset_type=(row.get("Typ") or "").strip()[:50],
            ref_quantity=qty,
            ref_unit=unit[:20],
            density=density,
            gwp_a1a3=gwp,
            embodied_co2=per_kg,
            notes=f"ÖKOBAUDAT {row.get('Referenzjahr', '')}; Konformität {row.get('Konformitaet', '')}".strip(),
        ))

    # Kompletter Neuaufbau: alter Stand wird ersetzt (idempotenter Import).
    model_class.objects.all().delete()
    model_class.objects.bulk_create(objects, batch_size=500)
    return {
        "file": "OBD-Export",
        "rows": len(rows),
        "imported": len(objects),
        "updated": 0,
        "skipped": len(rows) - len(objects),
    }


def import_material_rows(rows: List[Dict[str, str]], model_class, source_name: str = "upload"):
    """Import einer bereits eingelesenen Zeilenliste (aus CSV *oder* Excel).

    Erkennt den offiziellen ÖKOBAUDAT-Export (UUID/Modul) und nutzt sonst den
    generischen Spalten-Matcher. Gemeinsame Basis für Datei-, Upload- und Excel-Import.
    """
    # Offizieller ÖKOBAUDAT-Export → eigener Importpfad (Modul A1–A3, GWP)
    if _is_obd_export(rows):
        result = import_obd_export(rows, model_class)
        result["file"] = source_name
        return result

    imported = 0
    updated = 0
    skipped = 0

    for row in rows:
        parsed = extract_material_data(row)
        if not parsed or not parsed["name"]:
            skipped += 1
            continue

        defaults = {
            "producer": parsed["producer"],
            "category": parsed["category"],
            "u_value": parsed["u_value"],
            "embodied_co2": parsed["embodied_co2"],
            "notes": parsed["notes"],
        }

        obj, created = model_class.objects.update_or_create(
            name=parsed["name"],
            defaults=defaults,
        )
        if created:
            imported += 1
        else:
            updated += 1

    return {
        "file": source_name,
        "rows": len(rows),
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
    }


def import_materials_from_csv(filename: str, model_class):
    """Import aus einer CSV-Datei in dashboard/data/ (Dateipfad-basiert)."""
    rows = read_csv_rows(filename)
    return import_material_rows(rows, model_class, source_name=filename)
