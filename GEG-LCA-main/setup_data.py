#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geglca.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Material, Konstruktion, MaterialSchicht, KonstruktionSchicht, FensterTyp

# Superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.de', 'admin')
    print("✓ Superuser 'admin' erstellt")

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
        print(f"  ✓ {data['name']}")

# Sample Fenstertypen
fenster_data = [
    {'name': 'Standard 3-fach', 'u_w': 1.1, 'g_value': 0.6, 'psi_edge': 0.06},
    {'name': 'High-Performance', 'u_w': 0.75, 'g_value': 0.55, 'psi_edge': 0.03},
    {'name': 'Altbau 2-fach', 'u_w': 2.8, 'g_value': 0.75, 'psi_edge': 0.12},
]

for data in fenster_data:
    if not FensterTyp.objects.filter(name=data['name']).exists():
        FensterTyp.objects.create(**data)
        print(f"  ✓ {data['name']}")

print("\n✓✓✓ Sample-Daten erfolgreich erstellt!")
print("Admin: http://localhost:8000/admin/")
print("Benutzer: admin | Passwort: admin")
