import uuid

from django.db import models


class Project(models.Model):
	project_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	project_name = models.CharField(max_length=255)
	project_number = models.CharField(max_length=120, blank=True)
	file_reference = models.CharField(max_length=120, blank=True)
	legal_basis = models.CharField(max_length=80, blank=True)
	energy_basis = models.CharField(max_length=80, blank=True)
	building_kind = models.CharField(max_length=80, blank=True)
	location = models.CharField(max_length=255, blank=True)
	payload = models.JSONField(default=dict)
	calculation = models.JSONField(default=dict)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.project_name


class ProjectZone(models.Model):
	project = models.ForeignKey(Project, related_name="zones", on_delete=models.CASCADE)
	zone_name = models.CharField(max_length=255)
	usage_profile = models.CharField(max_length=80)
	area = models.FloatField(default=0)
	setpoint_temperature = models.FloatField(default=0)
	air_change_rate = models.FloatField(default=0)
	internal_gains_density = models.FloatField(default=0)
	occupancy_hours = models.FloatField(default=0)
	gain_utilization_factor = models.FloatField(default=0)
	payload = models.JSONField(default=dict)

	def __str__(self):
		return f"{self.project.project_name} - {self.zone_name}"
