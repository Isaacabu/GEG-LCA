#!/usr/bin/env python
"""
Automatisiertes Setup-Script für GEG-LCA Projekt
Initialisiert Datenbank, erstellt Superuser und importiert Ökobaudat-Daten
"""

import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geglca.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from dashboard.models import Material, FensterTyp
from dashboard.csv_utils import import_materials_from_csv, list_data_files
from dashboard.models import EkobaudatMaterial


def run_migrations():
    """Führe Django-Migrationen durch"""
    print("\n🔄 Führe Migrationen durch...")
    try:
        call_command('migrate')
        print("✅ Migrationen erfolgreich durchgeführt")
    except Exception as e:
        print(f"❌ Fehler bei Migrationen: {e}")
        return False
    return True


def create_superuser():
    """Erstelle Admin-Benutzer"""
    print("\n👤 Erstelle Superuser...")
    if User.objects.filter(username='admin').exists():
        print("⏭️  Superuser 'admin' existiert bereits")
        return True
    
    try:
        User.objects.create_superuser('admin', 'admin@test.de', 'admin')
        print("✅ Superuser 'admin' erstellt (Passwort: admin)")
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Superusers: {e}")
        return False
    return True


def create_sample_data():
    """Erstelle Sample-Daten (Fenstertypen, Materialien)"""
    print("\n📦 Erstelle Sample-Daten...")
    
    # Sample Materials
    materials_data = [
        {'name': 'Ziegelmauerwerk 17.5cm', 'rohdichte': 1200, 'lambda_value': 0.6, 'c_specific': 1.0, 'mu_value': 8},
        {'name': 'Polystyrol (EPS)', 'rohdichte': 25, 'lambda_value': 0.04, 'c_specific': 1.45, 'mu_value': 40},
        {'name': 'Mineralwolle', 'rohdichte': 100, 'lambda_value': 0.035, 'c_specific': 0.84, 'mu_value': 2},
        {'name': 'Stahlbeton', 'rohdichte': 2400, 'lambda_value': 2.0, 'c_specific': 0.88, 'mu_value': 100},
        {'name': 'Holz Fichte', 'rohdichte': 500, 'lambda_value': 0.13, 'c_specific': 2.5, 'mu_value': 50},
        {'name': 'Kalkzementputz', 'rohdichte': 1800, 'lambda_value': 0.87, 'c_specific': 0.84, 'mu_value': 15},
    ]

    for data in materials_data:
        if not Material.objects.filter(name=data['name']).exists():
            Material.objects.create(**data)
            print(f"  ✅ {data['name']}")

    # Sample Fenstertypen
    fenster_data = [
        {'name': 'Standard 3-fach', 'u_w': 1.1, 'g_value': 0.6, 'psi_edge': 0.06},
        {'name': 'High-Performance', 'u_w': 0.75, 'g_value': 0.55, 'psi_edge': 0.03},
        {'name': 'Altbau 2-fach', 'u_w': 2.8, 'g_value': 0.75, 'psi_edge': 0.12},
    ]

    for data in fenster_data:
        if not FensterTyp.objects.filter(name=data['name']).exists():
            FensterTyp.objects.create(**data)
            print(f"  ✅ {data['name']}")
    
    return True


def import_ekobaudat_data():
    """Importiere Ökobaudat-Daten aus CSV"""
    print("\n🏗️  Importiere Ökobaudat-Materialien...")
    
    files = list_data_files()
    if not files:
        print("❌ Keine CSV-Dateien in dashboard/data gefunden!")
        print("   Bitte prüfe, ob die CSV-Datei existiert")
        return False
    
    # Wähle die erste verfügbare CSV-Datei
    filename = files[0]
    print(f"   Verwende: {filename}")
    
    try:
        result = import_materials_from_csv(filename, EkobaudatMaterial)
        print(f"✅ Import abgeschlossen:")
        print(f"   - {result['imported']} neue Materialien importiert")
        print(f"   - {result['updated']} aktualisiert")
        print(f"   - {result['skipped']} übersprungen")
        print(f"   - Gesamt: {result['rows']} Zeilen")
        return True
    except FileNotFoundError as e:
        print(f"❌ Datei nicht gefunden: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Import: {e}")
        return False


def main():
    """Haupt-Setup-Funktion"""
    print("=" * 60)
    print("🚀 GEG-LCA Projekt Setup")
    print("=" * 60)
    
    # Prüfe ob wir im richtigen Verzeichnis sind
    if not os.path.exists('geglca/settings.py'):
        print("❌ Fehler: manage.py oder geglca/settings.py nicht gefunden!")
        print("   Bitte führe dieses Script aus der Projektwurzel aus")
        sys.exit(1)
    
    all_success = True
    
    # Schritt 1: Migrationen
    if not run_migrations():
        all_success = False
    
    # Schritt 2: Superuser
    if not create_superuser():
        all_success = False
    
    # Schritt 3: Sample-Daten
    if not create_sample_data():
        all_success = False
    
    # Schritt 4: Ökobaudat-Import
    if not import_ekobaudat_data():
        all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("✅ Setup erfolgreich abgeschlossen!")
        print("\n📝 Nächste Schritte:")
        print("   1. Starte den Server: python manage.py runserver")
        print("   2. Öffne: http://localhost:8000")
        print("   3. Admin: http://localhost:8000/admin/")
        print("      Benutzer: admin | Passwort: admin")
    else:
        print("⚠️  Setup mit Fehlern abgeschlossen - bitte obige Fehler prüfen")
    print("=" * 60)


if __name__ == '__main__':
    main()
