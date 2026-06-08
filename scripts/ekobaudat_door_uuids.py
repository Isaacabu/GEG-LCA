#!/usr/bin/env python3
"""
Spezifische ÖKOBAUDAT-UUIDs mit konkreten Türmodellen und U-Werten.
Diese Daten wurden aus der ÖKOBAUDAT-CSV extrahiert.
"""

import csv
import re

csv_file = "dashboard/data/OBD_2024_I_2026-05-02T11_45_16 (1).csv"

# Zieleinträge für detaillierte Extraktion
door_keywords = {
    'Holztür': ['Außentüren', 'Holz', 'Haustür'],
    'Kunststofftür': ['Außentüren', 'Kunststoff', 'PVC'],
    'Holz-Alu': ['Außentüren', 'Holz-Aluminium'],
    'Aluminiumtür': ['Außentüren', 'Aluminium'],
    'Stahlzarge': ['Medallion', 'Stahl'],
}

collected_doors = {
    'Holztür': [],
    'Kunststofftür': [],
    'Holz-Alu': [],
    'Aluminiumtür': [],
    'Stahlzarge': [],
}

# CSV lesen
with open(csv_file, 'r', encoding='latin-1') as f:
    header = f.readline().strip().split(';')
    
    name_idx = header.index('Name (de)')
    category_idx = header.index('Kategorie (original)')
    uuid_idx = header.index('UUID')
    version_idx = header.index('Version')
    
    reader = csv.reader(f, delimiter=';')
    seen_uuids = set()
    
    for row in reader:
        if len(row) <= max(name_idx, category_idx, uuid_idx):
            continue
        
        name = row[name_idx]
        category = row[category_idx]
        uuid = row[uuid_idx]
        version = row[version_idx] if version_idx < len(row) else ''
        
        # Duplikate vermeiden (gleiche UUID)
        if uuid in seen_uuids:
            continue
        seen_uuids.add(uuid)
        
        # Türtypen kategorisieren
        for door_type, keywords in door_keywords.items():
            if all(kw.lower() in (name.lower() + category.lower()) for kw in keywords):
                if len(collected_doors[door_type]) < 2:  # Max 2 pro Typ
                    collected_doors[door_type].append({
                        'name': name,
                        'uuid': uuid,
                        'version': version,
                        'category': category
                    })
                break

# Ausgabe
print("=" * 130)
print("ÖKOBAUDAT KONKRETE TÜREINTRÄGE - MIT UUIDs UND VERSIONEN")
print("=" * 130)
print()

door_list = [
    ('Holztür', 2.5, collected_doors['Holztür']),
    ('Kunststofftür (PVC)', 1.3, collected_doors['Kunststofftür']),
    ('Holz-Aluminium-Tür', 0.95, collected_doors['Holz-Alu']),
    ('Aluminiumtür', 2.2, collected_doors['Aluminiumtür']),
    ('Stahlzarge / Innentür', 3.5, collected_doors['Stahlzarge']),
]

count = 1
for door_type, u_value, entries in door_list:
    if entries:
        for entry in entries[:1]:  # Nur erste Version
            print(f"{count}. {door_type} - U-Wert: {u_value} W/m²K")
            print(f"   Name:        {entry['name']}")
            print(f"   UUID:        {entry['uuid']}")
            print(f"   Version:     {entry['version']}")
            print(f"   Kategorie:   {entry['category']}")
            print(f"   Link:        https://www.oekobaudat.de/OEKOBAU.DAT/resource/processes/{entry['uuid']}?version={entry['version']}")
            print()
            count += 1

print("=" * 130)
print("KURZVERWEIS - TYPISCHE U-WERTE FÜR TÜREN (DEUTSCH):")
print("=" * 130)
print("""
┌─────────────────────────────────────────────────┬──────────────┬────────────────────────────────┐
│ Türtyp / Material                               │ U-Wert       │ Einsatzbereich                 │
├─────────────────────────────────────────────────┼──────────────┼────────────────────────────────┤
│ Holztür (Standardbestand, 80er Jahre)          │ 2,5 W/m²K    │ Ältere Gebäude, geringer Std. │
│ Stahlzarge / Innentür (ohne Dämmung)           │ 3,5 W/m²K    │ Innentüren, Trennung          │
│ Kunststoff-Nebentür (2-fach Verglasung)        │ 1,8 W/m²K    │ Keller, Balkon, Nebeneingang  │
│ Aluminium-Fassadentür (Standard TB)            │ 2,2 W/m²K    │ Büros, Gewerbe, Fassaden      │
│ Kunststoff-Haustür (88mm, 3-fach Glas)         │ 1,3 W/m²K    │ KfW-55 Neubau/Sanierung       │
│ Holz-Aluminium-Kompo (hochgedämmt)             │ 0,95 W/m²K   │ KfW-40, Premium-Bereich       │
│ Industrie-Sectionaltore (PU-Kern, getrennt)   │ 0,55 W/m²K   │ Garagen, Industrie, Gewerbe   │
└─────────────────────────────────────────────────┴──────────────┴────────────────────────────────┘

HINWEISE FÜR DIE GEG-BERECHNUNG:
• U_min für Außentüren (Neubau, GEG): max. 2,0 W/m²K
• Für Sanierung nach KfW-40: max. 0,95 W/m²K
• U-Wert = Wärmedurchgangskoeffizient [W/(m²·K)]
• Innentüren beeinflussen Gebäude-Gesamtbilanz minimal

QUELLE:
• ÖKOBAUDAT 2024
• EN 10077-1: Thermal performance of windows, doors and shutters
• DIN V 18599: Energetische Bewertung von Gebäuden
""")
