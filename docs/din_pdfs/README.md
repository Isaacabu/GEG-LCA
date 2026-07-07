Anleitung: DIN PDFs für Extraktion

- Lege deine DIN-PDF-Dateien in diesen Ordner: `docs/din_pdfs` (z. B. `DIN_*.pdf`).
- Starte die Extraktion:

```bash
pip install pdfplumber
python tools/extract_din_pdfs.py --input docs/din_pdfs --output output/din_texts
```

Ausgabe:
- `output/din_texts/<pdfname>.json` enthält: filename, raw_text, pages[], sections[].
- `output/din_texts/<pdfname>.txt` enthält den rohen Text.

Nächste Schritte:
- Lade die restlichen 11 PDFs hier hoch oder verschiebe sie in `docs/din_pdfs`.
- Sag mir, welches Ausgabeformat du bevorzugst (JSON, CSV, TypeScript-Module, Python-Module, HTML-Report).