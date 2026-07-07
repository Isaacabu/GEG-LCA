#!/usr/bin/env sh
# Container-Start: Datenbank migrieren, beim ersten Start einmalig befüllen,
# dann den Django-Server starten. Idempotent – ein zweiter Start (persistentes
# Volume) überspringt die (teure) Ökobaudat-Import-Erstinitialisierung.
set -e

echo "==> Datenbank-Migrationen"
python manage.py migrate --noinput

# Seed nur nötig, solange die Ökobaudat-Tabelle leer ist.
NEED_SEED=$(python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geglca.settings")
django.setup()
from dashboard.models import EkobaudatMaterial
print("yes" if not EkobaudatMaterial.objects.exists() else "no")
PY
)

if [ "$NEED_SEED" = "yes" ]; then
    echo "==> Erstinitialisierung: Superuser (admin/admin), Beispieldaten, Ökobaudat-Import"
    # setup.py ist idempotent (Superuser/Sample werden nur bei Bedarf angelegt);
    # schlägt der CSV-Import fehl (z. B. Datei fehlt), startet der Server trotzdem.
    python setup.py || echo "==> WARN: Setup mit Warnungen abgeschlossen – Server startet trotzdem"
else
    echo "==> Datenbank bereits befüllt – Seed übersprungen"
fi

echo "==> Starte Django auf 0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000 --noreload
