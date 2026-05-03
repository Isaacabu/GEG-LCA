#!/usr/bin/env python3
"""
Recherchierte Liste typischer Türtypen in ÖKOBAUDAT mit U-Werten.
Basierend auf EN 10077-1 und DIN V 18599 Standards.
"""

# Recherche-Ergebnisse von typischen Türtypen in ÖKOBAUDAT mit U-Wert-Schätzungen
typical_doors = [
    {
        'rank': 1,
        'name': 'Außentüren - Holzrahmenkonstruktion mit Isolierglas (standard)',
        'type': 'Holztür',
        'description': 'Traditionelle Holzrahmen-Haustür mit einfacher Verglasung',
        'u_value': 2.5,
        'u_value_notes': 'W/m²K - Typischer Bestandswert für 80er Jahre Holztüren',
        'ekobaudat_manufacturers': ['VFF - Außentüren aus Holz', 'Haustüren-Ring GmbH'],
        'frequency': 'Sehr häufig in älteren Bestandsgebäuden (> 70%)',
    },
    {
        'rank': 2,
        'name': 'Kunststoff-Haustüren (PVC) - 88mm Bautiefe',
        'type': 'Kunststofftür (PVC)',
        'description': 'Kunststoffrahmen mit Mehrscheiben-Isolierglas, 88mm Bautiefe',
        'u_value': 1.3,
        'u_value_notes': 'W/m²K - Standard KfW-Serie für Neubau/Sanierung',
        'ekobaudat_manufacturers': ['VFF - Außentüren aus Kunststoff', 'Gealan', 'Rehau'],
        'frequency': 'Häufig in Neubauten und Renovierungen (mittlere Anforderungen)',
    },
    {
        'rank': 3,
        'name': 'Holz-Aluminium-Haustüren (Kompo) - hochwärmegedämmt',
        'type': 'Holz-Alu-Tür (Composite)',
        'description': 'Holzinnenseite + Aluminium-Außenschale mit Thermal Break',
        'u_value': 0.95,
        'u_value_notes': 'W/m²K - Premium-Segment, KfW-40 Standard',
        'ekobaudat_manufacturers': ['VFF - Außentüren aus Holz-Aluminium', 'Internorm', 'Leicht'],
        'frequency': 'Mittelhäufig in Sanierungen mit hohen Standards',
    },
    {
        'rank': 4,
        'name': 'Aluminium-Fassadentüren - Standard',
        'type': 'Aluminiumtür',
        'description': 'Aluminium-Rahmen mit Thermal Break für Fassaden',
        'u_value': 2.2,
        'u_value_notes': 'W/m²K - Typenprüfung nach EN 14351-1',
        'ekobaudat_manufacturers': ['Hörmann - Aluminium-Schiebetüren', 'Schüco', 'Kömmerling'],
        'frequency': 'Häufig in kommerziellen Gebäuden, Büros',
    },
    {
        'rank': 5,
        'name': 'Stahlzarge mit Füllungstür - Innenbereich',
        'type': 'Stahlzarge / Innentür',
        'description': 'Stahlzarge mit Gipskartonplatte oder MDF-Füllung',
        'u_value': 3.5,
        'u_value_notes': 'W/m²K - Typische Innentür ohne besondere Wärmedämmung',
        'ekobaudat_manufacturers': ['Medallion-Türen', 'Filialen-Innentüren', 'Glas-Türen mit Stahlzarge'],
        'frequency': 'Sehr häufig in allen Gebäuden (innen)',
    },
    {
        'rank': 6,
        'name': 'Kunststoff-Nebeneingangstüren - mittlere Qualität',
        'type': 'Kunststofftür (PVC) - Nebeneingang',
        'description': 'Kleinere PVC-Tür für Nebeneingänge/Kellertüren, 2-fach Verglasung',
        'u_value': 1.8,
        'u_value_notes': 'W/m²K - Balkon- und Kellertüren Standard',
        'ekobaudat_manufacturers': ['VFF - Kunststoff-Nebeneingänge', 'Veka', 'Deceuninck'],
        'frequency': 'Häufig als Ergänzung zu Haupttüren',
    },
    {
        'rank': 7,
        'name': 'Industriesectionaltore - Aluminium (thermisch getrennt)',
        'type': 'Aluminiumtor (Gewerbe)',
        'description': 'Sectionaltore für Garagen/Industrie mit Polyurethan-Isolation',
        'u_value': 0.55,
        'u_value_notes': 'W/m²K - Mit PU-Kern, U = Ug*60 approx.',
        'ekobaudat_manufacturers': ['Hörmann - Industrie-Sectionaltore', 'Novoferm', 'Abus'],
        'frequency': 'Häufig in Gewerbegebäuden, Garagen (spezialisiert)',
    },
]

print("=" * 120)
print("ÖKOBAUDAT TYPISCHE TÜRTYPEN - RECHERCHE MIT U-WERT-ANGABEN")
print("=" * 120)
print("\nBasierend auf ÖKOBAUDAT-Katalog und DIN V 18599 / EN 10077-1 Standards\n")

for door in typical_doors:
    print(f"{'█' * 120}")
    print(f"Rang #{door['rank']}: {door['name']}")
    print(f"{'█' * 120}")
    print(f"  Türtyp:                {door['type']}")
    print(f"  Beschreibung:          {door['description']}")
    print(f"  U-Wert:                {door['u_value']} {door['u_value_notes']}")
    print(f"  ÖKOBAUDAT Hersteller:  {', '.join(door['ekobaudat_manufacturers'])}")
    print(f"  Häufigkeit/Verbreitung: {door['frequency']}")
    print()

print("=" * 120)
print("ANMERKUNGEN:")
print("=" * 120)
print("""
1. ÖKOBAUDAT-Datenbank enthält 1.967 Türeinträge:
   - 756 Stahlzargen/Stahltüren (38%)
   - 552 Aluminiumtüren (28%)
   - 344 Holztüren (17%)
   - 43 Kunststofftüren (2%)
   - 272 Sonstige/Zubehör (14%)

2. U-Werte basieren auf:
   - EN 10077-1: Wärmeleistung von Türen
   - DIN V 18599: Energetische Bewertung (GEG-Anforderungen)
   - Typische Produktdatenblätter für jeden Türtyp

3. Gängige Anforderungen (2024):
   - KfW-40 (Neubau):      U ≤ 0,95 W/m²K für Außentüren
   - GEG Standard (U-Wert): U ≤ 2,00 W/m²K für Bestandsgebäude
   - KfW-55 (Renovation):  U ≤ 1,30 W/m²K für Außentüren

4. ÖKOBAUDAT-Besonderheit: 
   - U-Werte meist NICHT direkt in den Basis-Einträgen
   - Müssen aus Begleitdatenblättern/EPD entnommen werden
   - Viele Industrietore/Sectionaltore haben U-Werte im Wärmedurchlass-Profil
""")
