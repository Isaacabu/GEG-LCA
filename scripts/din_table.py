#!/usr/bin/env python
"""Extract a table from a DIN PDF page by clustering words into rows/columns by
coordinates. Far more reliable than reading rendered images by eye.

Usage: python scripts/din_table.py <part> <pagenum>
"""
import sys
from pathlib import Path
import fitz

sys.stdout.reconfigure(encoding="utf-8")

# Watermark words overlaid diagonally on withdrawn-edition PDFs; drop them.
WATERMARK = {
    "withdrawn", "zurückgezogen", "uncontrolled", "are", "copies", "Printed",
    "DIN/TS", "Nachfolgedokument:", "(2025-10)", "(DE30105006)", "18599-10",
    "V", "DIN",
}

PDF_DIR = Path(r"C:\Users\ahmet\Desktop\schule\4. Sem\DigiProz\GEG-LCA-NEUESTE\DIN V 18599")
FILES = {
    "1": "DIN V 18599-1_2018-09-00_DE_2874317.pdf",
    "2": "DIN V 18599-2_2018-09-00_DE_2874435.pdf",
    "5": "DIN V 18599-5_2018-09-00_DE_2875514.pdf",
    "6": "DIN V 18599-6_2018-09-00_DE_2874949.pdf",
    "8": "DIN V 18599-8_2018-09-00_DE_2878217.pdf",
    "10": "DIN V 18599-10_2018-09-00_DE_2874436.pdf",
}


def main():
    part, pagenum = sys.argv[1], int(sys.argv[2])
    doc = fitz.open(PDF_DIR / FILES[part])
    page = doc[pagenum - 1]
    words = [w for w in page.get_text("words") if w[4] not in WATERMARK]
    # cluster into rows by y0 (tolerance 4 pt)
    rows = []
    for w in sorted(words, key=lambda w: (round(w[1] / 4), w[0])):
        y = w[1]
        placed = False
        for row in rows:
            if abs(row["y"] - y) < 4:
                row["words"].append((w[0], w[4]))
                placed = True
                break
        if not placed:
            rows.append({"y": y, "words": [(w[0], w[4])]})
    for row in sorted(rows, key=lambda r: r["y"]):
        cells = [t for _, t in sorted(row["words"], key=lambda p: p[0])]
        print(" | ".join(cells))
    doc.close()


if __name__ == "__main__":
    main()
