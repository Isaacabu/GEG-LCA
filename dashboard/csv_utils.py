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


def import_materials_from_csv(filename: str, model_class):
    rows = read_csv_rows(filename)
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
        "file": filename,
        "rows": len(rows),
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
    }
