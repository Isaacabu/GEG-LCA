# GEG-LCA – Django-App (Ein-Zonen-DIN-V-18599-/DIN-4108-Rechner)
FROM python:3.12-slim

# Python-Container-Konventionen: kein Bytecode-Cache, ungepufferte Logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Abhängigkeiten zuerst (Layer-Caching): ändert sich requirements.txt nicht,
# wird pip install aus dem Cache bedient.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektcode (die lokale db.sqlite3 wird per .dockerignore ausgeschlossen –
# die Datenbank wird beim ersten Start frisch initialisiert).
COPY . .

# Entrypoint ausführbar machen; evtl. CRLF (Windows-Checkout) entfernen.
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000

# Der Entrypoint migriert, initialisiert einmalig die Daten und startet den Server.
ENTRYPOINT ["./docker-entrypoint.sh"]
