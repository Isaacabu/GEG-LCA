#!/usr/bin/env python
"""Render DIN PDF pages to PNG so they can be read accurately (formulas/tables).

Usage:
    python scripts/din_page.py <part> <start> <end>
e.g. python scripts/din_page.py 2 30 33   -> renders Teil 2, PDF pages 30..33

Output: scripts/_din_render/teil<part>_p<n>.png
"""
import sys
from pathlib import Path
import fitz

PDF_DIR = Path(r"C:\Users\ahmet\Desktop\schule\4. Sem\DigiProz\GEG-LCA-NEUESTE\DIN V 18599")
OUT_DIR = Path(__file__).resolve().parent / "_din_render"
OUT_DIR.mkdir(exist_ok=True)

# Map part identifier -> filename
FILES = {
    "1": "DIN V 18599-1_2018-09-00_DE_2874317.pdf",
    "2": "DIN V 18599-2_2018-09-00_DE_2874435.pdf",
    "3": "DIN V 18599-3_2018-09-00_DE_2874947.pdf",
    "4": "DIN V 18599-4_2018-09-00_DE_2874950.pdf",
    "5": "DIN V 18599-5_2018-09-00_DE_2875514.pdf",
    "6": "DIN V 18599-6_2018-09-00_DE_2874949.pdf",
    "7": "DIN V 18599-7_2018-09-00_DE_2877789.pdf",
    "8": "DIN V 18599-8_2018-09-00_DE_2878217.pdf",
    "9": "DIN V 18599-9_2018-09-00_DE_2874948.pdf",
    "10": "DIN V 18599-10_2018-09-00_DE_2874436.pdf",
    "11": "DIN V 18599-11_2018-09-00_DE_2874655.pdf",
    "bbl2": "DIN V 18599 Beiblatt 2_2012-06-00_DE_1893492.pdf",
}


def main():
    part, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    doc = fitz.open(PDF_DIR / FILES[part])
    print(f"Teil {part}: {doc.page_count} Seiten gesamt")
    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for legibility
    for n in range(start, end + 1):
        if n < 1 or n > doc.page_count:
            continue
        page = doc[n - 1]
        pix = page.get_pixmap(matrix=mat)
        out = OUT_DIR / f"teil{part}_p{n}.png"
        pix.save(out)
        print(f"  -> {out}")
    doc.close()


if __name__ == "__main__":
    main()
