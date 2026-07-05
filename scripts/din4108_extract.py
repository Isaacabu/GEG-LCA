#!/usr/bin/env python
"""Extract text from DIN 4108 PDF page ranges into readable .txt files.

Usage:
    python scripts/din4108_extract.py <key> <start> <end>
e.g. python scripts/din4108_extract.py 2 15 37   -> Teil 2, PDF pages 15..37

Output: scripts/_din4108_text/teil<key>_p<start>-<end>.txt
PDFs are local-only (copyrighted norm); folder is gitignored-style scratch.
"""
import sys
from pathlib import Path
import fitz

PDF_DIR = Path(__file__).resolve().parent.parent / "DIN_4108"
OUT_DIR = Path(__file__).resolve().parent / "_din4108_text"
OUT_DIR.mkdir(exist_ok=True)

FILES = {
    "2": "DIN 4108-2_2026-05-00_DE_3688761.pdf",
    "3": "DIN 4108-3_2024-03-00_DE_3498131.pdf",
    "4": "DIN 4108-4_2020-11-00_DE_3188939.pdf",
    "7": "DIN 4108-7_2026-04-00_DE_3669379.pdf",
    "10": "DIN 4108-10_2021-11-00_DE_3286456.pdf",
    "11": "DIN 4108-11_2018-11-00_DE_2868600.pdf",
    "bbl2": "DIN 4108 Beiblatt 2_2019-06-00_DE_3054799.pdf",
}


def main():
    key, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    doc = fitz.open(PDF_DIR / FILES[key])
    out = OUT_DIR / f"teil{key}_p{start}-{end}.txt"
    parts = []
    for n in range(start, end + 1):
        if n < 1 or n > doc.page_count:
            continue
        page = doc[n - 1]
        parts.append(f"\n===== Teil {key}  PDF-Seite {n} =====\n")
        parts.append(page.get_text("text"))
    out.write_text("".join(parts), encoding="utf-8")
    doc.close()
    print(f"-> {out}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
