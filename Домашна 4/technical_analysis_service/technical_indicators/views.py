import json
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import calculate_indicators


# Create your views here.

@csrf_exempt
def technical_analysis_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        ohlcv = data.get("ohlcv", [])
        if not ohlcv:
            return JsonResponse({"error": "No OHLCV data provided"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Invalid JSON: {str(e)}"}, status=400)

    df = pd.DataFrame(ohlcv)
    df["date"] = pd.to_datetime(df["date"])

    df_indicators = calculate_indicators(df)

    indicator_cols = ["date", "rsi", "macd", "macd_signal", "stoch",
                      "adx", "cci", "sma_20", "ema_20", "wma_20",
                      "bb_mid", "bb_upper", "bb_lower", "vwap"]

    df_indicators = df_indicators[indicator_cols]

    df_indicators = df_indicators.where(pd.notnull(df_indicators), None)

    return JsonResponse({"data": df_indicators.to_dict(orient="records")})
