from django.shortcuts import render
from .models import Coins, OhlcvData


# Create your views here.

def home(request):
    coins = Coins.objects.all()
    context = {'coins': coins}
    return render(request, 'home.html', context)


def login(request):
    return render(request, 'login.html')


def signup(request):
    return render(request, 'signup.html')


def coin_detail(request, symbol):
    symbol_obj = Coins.objects.get(symbol=symbol)
    ohlcv_data = OhlcvData.objects.filter(symbol=symbol)
    context = {'symbol_obj': symbol_obj,
               'ohlcv_data': ohlcv_data}
    return render(request, 'coin_detail.html', context)
