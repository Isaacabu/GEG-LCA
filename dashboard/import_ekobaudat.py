from dashboard.csv_utils import list_data_files, read_csv_rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Lade eine Ökobaudat-CSV aus dashboard/data und zeige die ersten Zeilen."
    )
    parser.add_argument(
        "filename",
        nargs="?",
        default=None,
        help="Name der CSV-Datei in dashboard/data",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste verfügbare CSV-Dateien im Ordner dashboard/data",
    )
    args = parser.parse_args()

    if args.list:
        files = list_data_files()
        if not files:
            print("Keine CSV-Dateien in dashboard/data gefunden.")
            raise SystemExit(0)
        print("Verfügbare CSV-Dateien:")
        for filename in files:
            print(f"- {filename}")
        raise SystemExit(0)

    filename = args.filename
    if not filename:
        files = list_data_files()
        if len(files) == 1:
            filename = files[0]
            print(f"Einzige Datei gefunden: {filename}")
        else:
            print("Bitte einen Dateinamen angeben oder --list verwenden.")
            raise SystemExit(1)

    try:
        rows = read_csv_rows(filename)
    except FileNotFoundError as exc:
        print(exc)
        raise SystemExit(1)

    print(f"Gefundene Zeilen: {len(rows)}")
    if not rows:
        print("Die CSV-Datei enthält keine Daten.")
        raise SystemExit(0)

    print("Spalten:", rows[0].keys())
    print("--- Erste 10 Zeilen ---")
    for i, row in enumerate(rows[:10], start=1):
        print(i, {k: row.get(k, '') for k in list(rows[0].keys())[:10]})
