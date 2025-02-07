from django.shortcuts import render
from .models import StraddlePrice

def index(request):
    return render(request, 'straddle/index.html', {"straddle_prices": StraddlePrice.objects.all()})


