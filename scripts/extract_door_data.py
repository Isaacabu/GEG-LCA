#!/usr/bin/env python3
"""
Skript zum Extrahieren von Türeinträgen aus ÖKOBAUDAT-CSV mit U-Wert-Angaben.
"""
import csv
import re
from collections import defaultdict

csv_file = "dashboard/data/OBD_2024_I_2026-05-02T11_45_16 (1).csv"

door_data = []

# CSV mit Semicolon als Trennzeichen lesen
with open(csv_file, 'r', encoding='latin-1') as f:
    # Header lesen
    header = f.readline().strip().split(';')
    
    # Spalten identifizieren
    name_idx = header.index('Name (de)')
    category_idx = header.index('Kategorie (original)')
    uuid_idx = header.index('UUID')
    
    # CSV Reader
    reader = csv.reader(f, delimiter=';')
    
    door_count = defaultdict(int)
    
    for row in reader:
        if len(row) <= max(name_idx, category_idx, uuid_idx):
            continue
            
        name = row[name_idx]
        category = row[category_idx]
        uuid = row[uuid_idx]
        
        # Nach Türen filtern
        if 'tür' in category.lower() or 'door' in category.lower():
            # Türtyp aus Kategorie extrahieren
            if 'Holz' in category:
                door_type = 'Holztür'
            elif 'Kunststoff' in category:
                door_type = 'Kunststofftür'
            elif 'Aluminium' in category:
                door_type = 'Aluminiumtür'
            elif 'Stahl' in category:
                door_type = 'Stahlzarge / Stahltür'
            else:
                door_type = 'Sonstige'
            
            door_count[door_type] += 1
            
            door_data.append({
                'uuid': uuid,
                'name': name,
                'category': category,
                'type': door_type
            })

# Nach Typ sortieren und ausgeben
print("=" * 100)
print("ÖKOBAUDAT TÜREINTRÄGE - ÜBERSICHT")
print("=" * 100)
print(f"\nGefundene Türeinträge: {len(door_data)}")
print(f"\nVerteilung nach Türtyp:")
for door_type, count in sorted(door_count.items(), key=lambda x: -x[1]):
    print(f"  - {door_type}: {count} Einträge")

# Beispiele pro Typ
print("\n" + "=" * 100)
print("BEISPIELE PRO TÜRTYP (bis zu 5 pro Typ):")
print("=" * 100)

for door_type in sorted(door_count.keys()):
    items = [d for d in door_data if d['type'] == door_type][:5]
    print(f"\n{door_type}:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item['name']}")
        print(f"     UUID: {item['uuid']}")
        print(f"     Kategorie: {item['category']}\n")
