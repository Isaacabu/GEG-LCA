from django.db import models
from django.core.validators import MinValueValidator


# ===== BAUTECHNIK: Material & Schichten =====
class Material(models.Model):
    """Baumaterial mit thermischen Eigenschaften"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Thermische Eigenschaften
    rohdichte = models.FloatField(validators=[MinValueValidator(0)], help_text="kg/m³")  # Rohdichte
    lambda_value = models.FloatField(validators=[MinValueValidator(0)], help_text="W/mK")  # Wärmeleitfähigkeit
    
    # Weitere
    c_specific = models.FloatField(default=1.0, validators=[MinValueValidator(0)], help_text="kJ/kgK")  # Spezifische Wärmekapazität
    mu_value = models.FloatField(default=1.0, help_text="Wasserdampf-Diffusionswiderstand")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Materials"
    
    def __str__(self):
        return f"{self.name} (λ={self.lambda_value} W/mK, ρ={self.rohdichte} kg/m³)"


class MaterialSchicht(models.Model):
    """Materialschicht für Konstruktionsaufbau"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    thickness_mm = models.FloatField(validators=[MinValueValidator(0.1)], help_text="Schichtdicke mm")
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.material.name} - {self.thickness_mm}mm"
    
    @property
    def r_value(self):
        """R-Wert berechnen: R = d / λ"""
        d_meter = self.thickness_mm / 1000
        return d_meter / self.material.lambda_value if self.material.lambda_value > 0 else 0


class Konstruktion(models.Model):
    """Konstruktionstyp (z.B. Außenwand, Dach, Boden)"""
    TYPEN = [
        ('aussen_wand', 'Außenwand'),
        ('dach', 'Dach'),
        ('bodenplatte', 'Bodenplatte'),
        ('decke', 'Decke/Zwischendecke'),
        ('keller_wand', 'Kellerwand'),
    ]
    
    name = models.CharField(max_length=200)
    typ = models.CharField(max_length=20, choices=TYPEN)
    description = models.TextField(blank=True)
    
    # Schichtenaufbau (M2M mit Ordnung)
    schichten = models.ManyToManyField(MaterialSchicht, through='KonstruktionSchicht')
    
    # Berechnung
    r_si = models.FloatField(default=0.13, help_text="R_si Wärmewiderstand innen (m²K/W)")
    r_se = models.FloatField(default=0.04, help_text="R_se Wärmewiderstand außen (m²K/W)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['typ', 'name']
        unique_together = ('name', 'typ')
    
    def __str__(self):
        return f"{self.get_typ_display()}: {self.name}"
    
    @property
    def u_value(self):
        """U-Wert berechnen: U = 1 / (R_si + Σ R_schichten + R_se)"""
        r_total = self.r_si + self.r_se
        for ks in self.konstruktionschicht_set.all().order_by('order'):
            r_total += ks.schicht.r_value
        return 1 / r_total if r_total > 0 else 0
    
    @property
    def r_value_total(self):
        """Gesamter Wärmewiderstand"""
        r_total = self.r_si + self.r_se
        for ks in self.konstruktionschicht_set.all().order_by('order'):
            r_total += ks.schicht.r_value
        return r_total


class KonstruktionSchicht(models.Model):
    """Zuordnung Material-Schichten zu Konstruktion (mit Ordnung)"""
    konstruktion = models.ForeignKey(Konstruktion, on_delete=models.CASCADE)
    schicht = models.ForeignKey(MaterialSchicht, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ('konstruktion', 'schicht', 'order')
    
    def __str__(self):
        return f"{self.konstruktion.name} - {self.schicht} (Pos {self.order})"


# ===== FENSTER =====
class FensterTyp(models.Model):
    """Fenstertyp mit U-Wert, g-Wert, etc."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Verglasung & Rahmen
    u_w = models.FloatField(validators=[MinValueValidator(0)], help_text="Uw-Wert W/m²K")
    g_value = models.FloatField(validators=[MinValueValidator(0), MinValueValidator(1)], help_text="g-Wert (0-1)")
    psi_edge = models.FloatField(default=0.06, help_text="Ψ_Randverbund W/mK")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (Uw={self.u_w}, g={self.g_value})"


# ===== TÜREN / TORE =====
class TürTyp(models.Model):
    """Tür-/Tortyp"""
    name = models.CharField(max_length=200, unique=True)
    u_value = models.FloatField(validators=[MinValueValidator(0)], help_text="U-Wert W/m²K")
    luftdichtheit = models.FloatField(default=1.0, help_text="Luftdichtheitsklasse (m³/h·m²)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (U={self.u_value})"


# ===== SONNENSCHUTZ =====
class SonnenschutzTyp(models.Model):
    """Sonnenschutzvorrichtung"""
    POSITIONEN = [
        ('innen', 'Innen'),
        ('außen', 'Außen'),
    ]
    TYP_CHOICES = [
        ('fest', 'Fest'),
        ('variabel', 'Variabel'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    position = models.CharField(max_length=10, choices=POSITIONEN)
    typ = models.CharField(max_length=10, choices=TYP_CHOICES)
    
    # Eigenschaften
    reduktionsfaktor = models.FloatField(
        validators=[MinValueValidator(0), MinValueValidator(1)],
        help_text="Reduktionsfaktor (0-1)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_position_display()}, {self.get_typ_display()})"


# ===== GEBÄUDEDATEN =====
class Gebäude(models.Model):
    """Hauptgebäude-Entity"""
    name = models.CharField(max_length=200)
    standort = models.CharField(max_length=200, blank=True)
    
    # Geometrie
    bgf = models.FloatField(validators=[MinValueValidator(0)], help_text="Brutto-Grundfläche m²")
    
    # Klima
    gradstunden = models.FloatField(default=78000, help_text="Gradstunden/Jahr Kh/a")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.bgf} m²)"


# ===== BAUTEILE / FLÄCHEN =====
class Bauteil(models.Model):
    """Einzelnes Bauteil (Fläche) im Gebäude"""
    ORIENTIERUNGEN = [
        ('nord', 'Nord'),
        ('süd', 'Süd'),
        ('ost', 'Ost'),
        ('west', 'West'),
        ('horizontal', 'Horizontal (Dach/Boden)'),
    ]
    
    gebäude = models.ForeignKey(Gebäude, on_delete=models.CASCADE, related_name='bauteile')
    name = models.CharField(max_length=200)
    
    # Eigenschaften
    orientierung = models.CharField(max_length=15, choices=ORIENTIERUNGEN)
    fläche = models.FloatField(validators=[MinValueValidator(0)], help_text="m²")
    
    # Zuordnung
    konstruktion = models.ForeignKey(Konstruktion, on_delete=models.SET_NULL, null=True, blank=True)
    fenster_typ = models.ForeignKey(FensterTyp, on_delete=models.SET_NULL, null=True, blank=True)
    fenster_fläche = models.FloatField(default=0, validators=[MinValueValidator(0)], help_text="Fensterfläche m²")
    
    sonnenschutz = models.ForeignKey(SonnenschutzTyp, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['orientierung', 'name']
    
    def __str__(self):
        return f"{self.gebäude.name} - {self.name} ({self.fläche} m²)"
    
    @property
    def transmissionsverlust(self):
        """Transmissionswärmeverlust: H = U × A"""
        if not self.konstruktion:
            return 0
        h_konstruktion = self.konstruktion.u_value * (self.fläche - self.fenster_fläche)
        
        h_fenster = 0
        if self.fenster_typ and self.fenster_fläche > 0:
            h_fenster = self.fenster_typ.u_w * self.fenster_fläche
        
        return h_konstruktion + h_fenster
