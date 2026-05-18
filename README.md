# GEG & LCA Projekt

## 📋 Beschreibung
Dieses Projekt ist eine web-basierte Plattform zur Analyse von Gebäudedaten mit Fokus auf:
- **GEG** (Gebäudeenergiegesetz)
- **LCA** (Lebenszyklusanalyse)
- **Ökobaudat-Materialien-Datenbank**
- **Thermische Berechnungen** (DIN V 18599)

## 🎯 Ziel
Entwicklung einer digitalen Lösung für eine integrierte Gebäudebewertung mit realistischen U-Werten und Lebenszyklusanalyse.

## 👥 Team
- Ken Truong
- Berke Bozdogan
- Ahmet Yetisir 
- Yunus Cevik

---

## 🚀 Quick Start (für Kommilitonen)

### Voraussetzungen
- Python 3.9+
- Git
- Virtual Environment (optional aber empfohlen)

### 1️⃣ Repository klonen
```bash
git clone https://github.com/Isaacabu/GEG-LCA.git
cd GEG-LCA
```

### 2️⃣ Virtual Environment erstellen (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Oder auf Mac/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4️⃣ **Automatisches Setup (WICHTIG!)**
```bash
python setup.py
```

Dieses Script macht automatisch folgendes:
- ✅ Erstellt die Datenbank
- ✅ Führt Django-Migrationen durch
- ✅ Erstellt Admin-Account (admin / admin)
- ✅ Importiert **alle Ökobaudat-Materialien mit U-Werten**

### 5️⃣ Server starten
```bash
python manage.py runserver
```

### 6️⃣ Im Browser öffnen
- **Website:** http://localhost:8000
- **Admin:** http://localhost:8000/admin/
- **Benutzer:** admin
- **Passwort:** admin

---

## 📂 Projektstruktur

```
GEG-LCA/
├── backend/              # Django-Backend-Logik
├── dashboard/            # Hauptanwendung
│   ├── data/             # Ökobaudat CSV-Dateien
│   ├── management/       # Django Management Commands
│   ├── services/         # DIN V 18599 Berechnungen
│   ├── models.py         # Datenbankmodelle
│   └── views.py          # Django Views
├── geglca/               # Django-Einstellungen
├── frontend/             # HTML/CSS/JavaScript
├── manage.py             # Django Management
├── setup.py              # Automatisiertes Setup-Script
└── requirements.txt      # Python Dependencies
```

---

## 🗄️ Datenbank & Daten

### Wichtig: U-Werte werden nicht angezeigt?
Falls die U-Werte nicht sichtbar sind, stelle sicher, dass du:

1. **Das Setup-Script ausgeführt hast:**
   ```bash
   python setup.py
   ```

2. **Datenbank löschen und neu aufsetzen (falls nötig):**
   ```bash
   rm db.sqlite3  # oder auf Windows: del db.sqlite3
   python setup.py
   ```

3. **Manuell Ökobaudat-Daten importieren (nur falls automatisch nicht geklappt hat):**
   ```bash
   python manage.py import_ekobaudat
   ```

### Welche Daten sind im System?
Nach dem Setup sind folgende Materialien verfügbar:
- ✅ **Ökobaudat 2024-Materialien** (1000+ Einträge mit realen U-Werten)
- ✅ **Fenstertypen** (Standard 3-fach, High-Performance, Altbau 2-fach)
- ✅ **Basis-Materialien** (Ziegel, Beton, Holz, Dämmstoffe, etc.)

---

## 🔧 Häufige Probleme & Lösungen

### ❌ "ModuleNotFoundError: No module named 'django'"
**Lösung:** Requirements installieren
```bash
pip install -r requirements.txt
```

### ❌ "db.sqlite3 existiert nicht"
**Lösung:** Setup-Script ausführen
```bash
python setup.py
```

### ❌ "U-Werte werden nicht angezeigt"
**Lösung:** Ökobaudat-Daten importieren
```bash
python setup.py
# oder manuell:
python manage.py import_ekobaudat --list
python manage.py import_ekobaudat "OBD_2024_I_2026-05-02T11_45_16 (1).csv"
```

### ❌ "Port 8000 wird bereits verwendet"
**Lösung:** Anderen Port nutzen
```bash
python manage.py runserver 8001
```

### ❌ "Permission denied" (Linux/Mac)
**Lösung:** Permissions setzen
```bash
chmod +x setup.py
python setup.py
```

---

## 📊 Admin-Interface

Nach dem Login im Admin-Panel (`/admin/`) kannst du:
- ✅ **Materialien verwalten** (U-Werte editieren)
- ✅ **Fenstertypen konfigurieren**
- ✅ **Ökobaudat-Materialien durchsuchen**
- ✅ **Benutzer & Berechtigungen verwalten**

---

## 🔐 Sicherheit (Wichtig für Produktion!)

**⚠️ WARNUNG:** Die Default-Credentials (`admin/admin`) und Debug-Modus sind NUR für Entwicklung gedacht!

Für den produktiven Betrieb in `geglca/settings.py` anpassen:
```python
DEBUG = False
ALLOWED_HOSTS = ['example.com']  # Domain eintragen
SECRET_KEY = 'neue-geheime-key-generieren'
```

---

## 📱 API & Zugriff

### Frontend
- Startseite: http://localhost:8000/
- Tabellen-Ansicht: http://localhost:8000/#bautechnik

### Backend (Admin)
- Admin-Panel: http://localhost:8000/admin/
- Material-Liste: http://localhost:8000/admin/dashboard/material/

---

## 🤝 Beitragen

Änderungen machen und hochladen:
```bash
git add .
git commit -m "Beschreibung der Änderung"
git push origin main
```

---

## 📝 Lizenz
Dieses Projekt ist Teil des Architektur-Studiums.

---

## ❓ Support & Fragen
Bei Problemen:
1. Dieses README durchlesen (besonders "Häufige Probleme")
2. `python setup.py` ausführen
3. Issue auf GitHub erstellen
