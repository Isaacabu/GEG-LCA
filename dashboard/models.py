from django.db import models


class EkobaudatMaterial(models.Model):
    name = models.CharField(max_length=250)
    producer = models.CharField(max_length=250, blank=True)
    category = models.CharField(max_length=250, blank=True)
    u_value = models.FloatField(null=True, blank=True)
    embodied_co2 = models.FloatField(null=True, blank=True, help_text="kg CO₂e pro m³ oder m²")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
