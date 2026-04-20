from django.shortcuts import render
from django.http import JsonResponse
import json


# Seite anzeigen
def index(request):
    return render(request, "dashboard/index.html")


# Berechnung (Pipeline!)
def calculate_heat_loss(request):
    if request.method == "POST":
        data = json.loads(request.body)

        area = float(data.get("area", 0))
        u_value = float(data.get("u_value", 0))

        heat_loss = area * u_value

        return JsonResponse({
            "heat_loss": heat_loss
        })
