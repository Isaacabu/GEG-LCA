from django.shortcuts import render
from django.http import JsonResponse
import json

def index(request):
    return render(request, 'dashboard/index.html')


def calculate(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        area = float(data.get('area', 0))
        u_value = float(data.get('u_value', 0))

        heat_loss = area * u_value

        return JsonResponse({
            'heat_loss': heat_loss
        })
        })
