from django.core.management.base import BaseCommand

from dashboard.csv_utils import import_materials_from_csv, list_data_files
from dashboard.models import EkobaudatMaterial


class Command(BaseCommand):
    help = "Importiere Ökobaudat-Materialien aus einer CSV-Datei im Ordner dashboard/data"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            nargs="?",
            help="Name der CSV-Datei in dashboard/data",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Liste der verfügbaren CSV-Dateien im Ordner dashboard/data anzeigen",
        )

    def handle(self, *args, **options):
        if options["list"]:
            files = list_data_files()
            if not files:
                self.stdout.write("Keine CSV-Dateien in dashboard/data gefunden.")
                return
            self.stdout.write("Verfügbare CSV-Dateien:")
            for name in files:
                self.stdout.write(f"- {name}")
            return

        filename = options["filename"]
        files = list_data_files()
        if not files:
            self.stdout.write(self.style.ERROR("Keine CSV-Dateien in dashboard/data gefunden."))
            return

        if not filename:
            if len(files) == 1:
                filename = files[0]
                self.stdout.write(f"Einzige Datei gefunden, importiere {filename}")
            else:
                self.stdout.write(self.style.ERROR(
                    "Mehrere CSV-Dateien gefunden. Bitte Dateinamen angeben oder --list verwenden."
                ))
                return

        if filename not in files:
            self.stdout.write(self.style.ERROR(
                f"Datei '{filename}' nicht in dashboard/data gefunden."
            ))
            return

        try:
            result = import_materials_from_csv(filename, EkobaudatMaterial)
            self.stdout.write(self.style.SUCCESS(
                f"Import abgeschlossen: {result['imported']} importiert, {result['updated']} aktualisiert, {result['skipped']} übersprungen (insgesamt {result['rows']} Zeilen)."
            ))
        except FileNotFoundError as exc:
            self.stdout.write(self.style.ERROR(str(exc)))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Fehler beim Import: {exc}"))
