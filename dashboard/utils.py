"""
Gemeinsame Hilfsfunktionen für Validierung, Datentypen und Bewertungen.
Zentrale Stelle für alle wiederverwendeten Funktionen (DRY-Prinzip).
"""

from typing import Any, Dict, List


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Sichere Konvertierung eines Wertes zu Float.
    
    Args:
        value: Zu konvertierender Wert (kann Any type sein)
        default: Fallback-Wert, wenn Konvertierung fehlschlägt
        
    Returns:
        float: Konvertierter Wert oder default
    """
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_non_negative(name: str, value: float, errors: List[str]) -> None:
    """
    Validiere dass Wert nicht negativ ist.
    
    Args:
        name: Name des Feldes (für Fehlermeldung)
        value: Zu validierender Wert
        errors: Fehlerliste zum Anhängen
    """
    if value < 0:
        errors.append(f"{name} darf nicht negativ sein.")


def validate_positive(name: str, value: float, errors: List[str]) -> None:
    """
    Validiere dass Wert größer als 0 ist.
    
    Args:
        name: Name des Feldes (für Fehlermeldung)
        value: Zu validierender Wert
        errors: Fehlerliste zum Anhängen
    """
    if value <= 0:
        errors.append(f"{name} muss größer als 0 sein.")


def validate_u_value(name: str, value: float, errors: List[str]) -> None:
    """
    Validiere U-Wert (Wärmewiderstand).
    Prüft auf negative Werte und unrealistische Obergrenzen.
    
    Args:
        name: Name des Feldes (für Fehlermeldung)
        value: Zu validierender U-Wert
        errors: Fehlerliste zum Anhängen
    """
    if value < 0:
        errors.append(f"{name} darf nicht negativ sein.")
    elif value > 5:
        errors.append(f"{name} ist unrealistisch hoch (> 5 W/m²K).")


def get_rating(value_per_m2a: float) -> Dict[str, str]:
    """
    Bewerte Heizwärmebedarf in Kategorien (sehr gut / mittel / kritisch).
    
    Args:
        value_per_m2a: Spezifischer Heizwärmebedarf in kWh/m²a
        
    Returns:
        Dict mit label, color und message
    """
    if value_per_m2a <= 40:
        return {
            "label": "Sehr gut",
            "color": "green",
            "message": "Niedriger Heizwärmebedarf – energetisch günstig."
        }
    elif value_per_m2a <= 80:
        return {
            "label": "Mittel",
            "color": "yellow",
            "message": "Akzeptabler Bereich – Optimierung sinnvoll."
        }
    return {
        "label": "Kritisch",
        "color": "red",
        "message": "Hoher Heizwärmebedarf – Gebäudehülle verbessern."
    }
