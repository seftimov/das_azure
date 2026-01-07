import json
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import train_and_forecast


# Create your views here.

@csrf_exempt
def lstm_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        payload = json.loads(request.body)
        ohlcv = payload["ohlcv"]
        lookback = int(payload.get("lookback", 30))
        epochs = int(payload.get("epochs", 20))
        horizon = int(payload.get("horizon", 7))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    df = pd.DataFrame(ohlcv)
    df["date"] = pd.to_datetime(df["date"])

    try:
        result = train_and_forecast(df, lookback, epochs, horizon)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse(result)
