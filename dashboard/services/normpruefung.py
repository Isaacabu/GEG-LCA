"""Konsolidierte Normpruefung: aggregiert die Ampel-Bewertungen (gruen/gelb/rot) der bereits
berechneten Einzel-Nachweise (Heizwaermebedarf nach DIN V 18599-2, Primaerenergie/CO2 aus der
Anlagentechnik, sowie die DIN-4108-Nachweise Mindestwaermeschutz/sommerlicher Waermeschutz/
Tauwasser/Luftdichtheit) zu einer Gesamtuebersicht.

Rein regelbasiert: es wird nichts neu berechnet und kein Sprachmodell aufgerufen. Die Funktion
liest ausschliesslich die rating_*/system_*-Felder aus, die die jeweiligen Services
(din18599.py, din18599_anlage.py, din4108.py) bereits liefern, und fasst sie zusammen.
"""

# Reihenfolge + Zuordnung: welcher Payload-Schluessel enthaelt welches Nachweis-Ergebnis, und
# unter welchem Feldnamen steht dort Ampelfarbe/-label/-meldung (die Services nennen das
# uneinheitlich rating_* bzw. system_*).
_CHECKS = [
    {
        "key": "heizwaermebedarf",
        "input": "heizwaerme",
        "name": "Heizwärmebedarf Q_h,b (DIN V 18599-2)",
        "value_key": "specific_heat_demand",
        "unit": "kWh/(m²a)",
        "label_key": "rating_label",
        "color_key": "rating_color",
        "message_key": "rating_message",
    },
    {
        "key": "primaerenergie",
        "input": "anlage",
        "name": "Primärenergie / CO₂ (Anlagentechnik, Teil 5/6/8)",
        "value_key": "specific_primary_energy",
        "unit": "kWh/(m²a)",
        "label_key": "system_label",
        "color_key": "system_color",
        "message_key": "system_message",
    },
    {
        "key": "mindestwaermeschutz",
        "input": "mindestwaermeschutz",
        "name": "Mindestwärmeschutz (DIN 4108-2, Tab. 3)",
        "value_key": None,
        "unit": "",
        "label_key": "rating_label",
        "color_key": "rating_color",
        "message_key": "rating_message",
    },
    {
        "key": "sommerlicher_waermeschutz",
        "input": "sommerlicher_waermeschutz",
        "name": "Sommerlicher Wärmeschutz (DIN 4108-2, §8.4)",
        "value_key": "s_vorh",
        "unit": "",
        "label_key": "rating_label",
        "color_key": "rating_color",
        "message_key": "rating_message",
    },
    {
        "key": "tauwasser",
        "input": "tauwasser",
        "name": "Tauwasser / Glaser-Verfahren (DIN 4108-3, Anhang A)",
        "value_key": "mc_total",
        "unit": "kg/m²",
        "label_key": "rating_label",
        "color_key": "rating_color",
        "message_key": "rating_message",
    },
    {
        "key": "luftdichtheit",
        "input": "luftdichtheit",
        "name": "Luftdichtheit n50 (DIN 4108-7)",
        "value_key": "n50_grenze",
        "unit": "h⁻¹",
        "label_key": "rating_label",
        "color_key": "rating_color",
        "message_key": "rating_message",
    },
]

_FARB_RANG = {"red": 0, "yellow": 1, "green": 2}

_GESAMT_LABEL = {
    "green": "Alle geprüften Nachweise erfüllt",
    "yellow": "Erfüllt mit Vorbehalt / Hinweisen",
    "red": "Mindestens ein Nachweis nicht erfüllt",
}


def pruefe_norm_konformitaet(payload):
    """Nimmt ein Dict mit den bereits berechneten Einzel-Ergebnissen entgegen (Schlüssel wie
    in _CHECKS[*]['input']: 'heizwaerme', 'anlage', 'mindestwaermeschutz',
    'sommerlicher_waermeschutz', 'tauwasser', 'luftdichtheit' — jeweils optional) und gibt die
    konsolidierte Ampel-Übersicht zurück."""
    pruefungen = []
    schlechteste_farbe = None

    for check in _CHECKS:
        teil = payload.get(check["input"])
        if not isinstance(teil, dict) or teil.get("ok") is False:
            pruefungen.append({
                "key": check["key"],
                "name": check["name"],
                "status": "fehlt",
                "wert": None,
                "einheit": check["unit"],
                "rating_label": None,
                "rating_color": None,
                "rating_message": "Noch nicht berechnet.",
            })
            continue

        color = teil.get(check["color_key"])
        label = teil.get(check["label_key"])
        message = teil.get(check["message_key"])
        wert = teil.get(check["value_key"]) if check["value_key"] else None

        pruefungen.append({
            "key": check["key"],
            "name": check["name"],
            "status": "geprueft",
            "wert": wert,
            "einheit": check["unit"],
            "rating_label": label,
            "rating_color": color,
            "rating_message": message,
        })

        if color in _FARB_RANG:
            if schlechteste_farbe is None or _FARB_RANG[color] < _FARB_RANG[schlechteste_farbe]:
                schlechteste_farbe = color

    anzahl_geprueft = sum(1 for p in pruefungen if p["status"] == "geprueft")
    anzahl_fehlend = len(pruefungen) - anzahl_geprueft

    if anzahl_geprueft == 0:
        gesamt_farbe = None
        gesamt_label = "Keine Nachweise vorhanden"
    else:
        gesamt_farbe = schlechteste_farbe or "green"
        gesamt_label = _GESAMT_LABEL[gesamt_farbe]

    return {
        "ok": True,
        "pruefungen": pruefungen,
        "anzahl_geprueft": anzahl_geprueft,
        "anzahl_fehlend": anzahl_fehlend,
        "gesamt_farbe": gesamt_farbe,
        "gesamt_label": gesamt_label,
    }
