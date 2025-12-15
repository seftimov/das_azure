import json
import pandas as pd
from datetime import date
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignupUserForm, CoinFilterForm
from .models import Coins, OhlcvData
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .technical_analysis import calculate_indicators
from .lstm import train_and_predict, forecast_future


# Create your views here.

def home(request):
    query = request.GET.get('searched', '')

    if query:
        coins = Coins.objects.filter(symbol__icontains=query)
    else:
        coins = Coins.objects.all()

    context = {
        'coins': coins,
        'query': query
    }

    return render(request, 'home.html', context)


def login_user(request):
    if request.method == 'POST':
        email = request.POST["email"]
        password = request.POST["password"]

        try:
            user = User.objects.get(email=email)
            username = user.username
            user = authenticate(request, username=username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return redirect('login')
    else:
        return render(request, 'authenticate/login.html', {})


def logout_user(request):
    logout(request)
    return redirect('login')


def signup_user(request):
    if request.method == 'POST':
        form = SignupUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
    else:
        form = SignupUserForm()
    return render(request, 'authenticate/signup.html', {'form': form})


def signup(request):
    return render(request, 'authenticate/signup.html')


def convert_currency(value, from_currency, to_currency):
    if value is None:
        return "N/A"

    conversion_rates = {
        'USD': {'USD': 1.0, 'EUR': 0.92, 'MKD': 58.0},
        'EUR': {'USD': 1.09, 'EUR': 1.0, 'MKD': 61.5},
        'MKD': {'USD': 0.017, 'EUR': 0.016, 'MKD': 1.0},
    }

    currency_symbols = {
        'USD': ('$ ', 'before'),
        'EUR': ('€ ', 'before'),
        'MKD': (' ден.', 'after'),
    }

    converted_value = value * conversion_rates[from_currency][to_currency]
    symbol, position = currency_symbols[to_currency]

    formatted_value = f"{converted_value:,.2f}"

    return f"{symbol}{formatted_value}" if position == 'before' else f"{formatted_value}{symbol}"


def coin_detail(request, symbol):
    symbol_obj = get_object_or_404(Coins, symbol=symbol)
    selected_currency = 'USD'

    # base queryset
    ohlcv_data = OhlcvData.objects.filter(symbol=symbol_obj.symbol)

    if request.method == 'POST':
        form = CoinFilterForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            selected_currency = form.cleaned_data.get('currency', 'USD') or 'USD'

            if start_date and end_date:
                ohlcv_data = ohlcv_data.filter(date__range=[start_date, end_date])
            elif start_date:
                ohlcv_data = ohlcv_data.filter(date__gte=start_date)
            elif end_date:
                ohlcv_data = ohlcv_data.filter(date__lte=end_date)
    else:
        # Default to current year
        current_year = 2025
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 12, 31)
        ohlcv_data = ohlcv_data.filter(date__range=[start_date, end_date])
        form = CoinFilterForm()

    # Prepare candlestick data
    ohlcv_data = ohlcv_data.exclude(close__isnull=True).order_by("date")

    candlestick_data = []
    for row in ohlcv_data:
        open_price = float(row.open)
        high_price = float(row.high)
        low_price = float(row.low)
        close_price = float(row.close)

        # Convert values for table display
        row.open = convert_currency(row.open, 'USD', selected_currency)
        row.high = convert_currency(row.high, 'USD', selected_currency)
        row.low = convert_currency(row.low, 'USD', selected_currency)
        row.close = convert_currency(row.close, 'USD', selected_currency)
        row.volume = row.volume  # volume doesn't convert

        # Candlestick for JS chart
        candlestick_data.append({
            "time": row.date.strftime("%Y-%m-%d"),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
        })

    context = {
        "symbol_obj": symbol_obj,
        "ohlcv_data": ohlcv_data,
        "form": form,
        "selected_currency": selected_currency,
        "candlestick_data": json.dumps(candlestick_data),
    }

    return render(request, "coin_detail.html", context)


# def coin_detail(request, symbol):
#     symbol_obj = Coins.objects.get(symbol=symbol)
#     ohlcv_data = OhlcvData.objects.filter(symbol=symbol)
#     context = {'symbol_obj': symbol_obj,
#                'ohlcv_data': ohlcv_data}
#     return render(request, 'coin_detail.html', context)


def technical_analysis_page(request):
    symbols = Coins.objects.values_list("symbol", flat=True).order_by("market_cap_rank")

    context = {"symbols": symbols}

    if request.method == "POST":
        symbol = request.POST.get("symbol")
        timeframe = request.POST.get("timeframe")

        ohlcv = OhlcvData.objects.filter(symbol=symbol).order_by("date")

        df = pd.DataFrame(list(ohlcv.values("date", "open", "high", "low", "close", "volume")))

        if df.empty:
            context["error"] = "No data found for this symbol."
            return render(request, "technical_analysis.html", context)

        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)

        df['date'] = pd.to_datetime(df['date'])

        if timeframe == "1week":
            df = df.resample("W", on="date").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).reset_index()

        elif timeframe == "1month":
            df = df.resample("M", on="date").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).reset_index()

        df = calculate_indicators(df)

        signals = []
        scores = []

        for i, row in df.iterrows():
            score = 0

            # RSI Momentum
            if row["rsi"] < 35:
                score += 1
            elif row["rsi"] > 65:
                score -= 1

            # MACD Trend Direction
            if row["macd"] > row["macd_signal"]:
                score += 1
            elif row["macd"] < row["macd_signal"]:
                score -= 1

            # Moving Average Trend
            if row["close"] > row["ema_20"]:
                score += 1
            elif row["close"] < row["ema_20"]:
                score -= 1

            # ADX Trend Strength Filter
            trending = row["adx"] > 20

            # FINAL SIGNAL DECISION
            if score >= 2 and trending:
                signal = "BUY"
            elif score <= -2 and trending:
                signal = "SELL"
            else:
                signal = "HOLD"

            signals.append(signal)
            scores.append(score)

        df["score"] = scores
        df["signal"] = signals

        context.update({
            "selected_symbol": symbol,
            "timeframe": timeframe,
            "table": df.tail(40).to_html(classes="table table-striped", index=False)
        })

    return render(request, "technical_analysis.html", context)


def lstm_page(request):
    symbols = Coins.objects.values_list("symbol", flat=True).order_by("market_cap_rank")
    context = {"symbols": symbols}

    if request.method == "POST":
        symbol = request.POST.get("symbol")
        lookback = int(request.POST.get("lookback", 30))
        epochs = int(request.POST.get("epochs", 20))
        horizon = int(request.POST.get("horizon", 7))
        granularity = request.POST.get("granularity", "daily")

        ohlcv = OhlcvData.objects.filter(symbol=symbol).order_by("date")
        df = pd.DataFrame(list(ohlcv.values("date", "open", "high", "low", "close", "volume")))

        if df.empty or len(df) < (lookback + 20):
            context["error"] = "Not enough data for LSTM."
            return render(request, "lstm.html", context)

        df[["open", "high", "low", "close", "volume"]] = df[
            ["open", "high", "low", "close", "volume"]
        ].astype(float)
        df["date"] = pd.to_datetime(df["date"])

        # RESAMPLING
        if granularity == "weekly":
            df = df.resample("W", on="date").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).reset_index()
            freq = "W"
        elif granularity == "monthly":
            df = df.resample("M", on="date").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).reset_index()
            freq = "M"
        else:
            freq = "D"

        results = train_and_predict(df, lookback=lookback, epochs=epochs)
        model = results["model"]
        scaler = results["scaler"]

        future_dates, future_preds = forecast_future(
            model, df, scaler, lookback, horizon, freq=freq
        )

        test_dates = results["test_dates"]
        y_test = results["y_test"]
        y_pred = results["y_pred"]
        metrics = results["metrics"]

        chart_data = []

        # Historical predicted vs actual
        for date, actual, pred in zip(test_dates, y_test, y_pred):
            chart_data.append({
                "time": date if isinstance(date, str) else date.strftime("%Y-%m-%d"),
                "actual": float(actual),
                "predicted": float(pred)
            })

        # Future predictions
        for date, pred in zip(future_dates, future_preds):
            chart_data.append({
                "time": date if isinstance(date, str) else date.strftime("%Y-%m-%d"),
                "actual": None,
                "predicted": float(pred)
            })

        context.update({
            "selected_symbol": symbol,
            "metrics": metrics,
            "chart_data": json.dumps(chart_data),
            "future_rows": [
                (
                    d if isinstance(d, str) else d.strftime("%Y-%m-%d"),
                    float(p)
                )
                for d, p in zip(future_dates, future_preds)
            ],
            "lookback": lookback,
            "epochs": epochs,
            "horizon": horizon,
            "granularity": granularity
        })

    return render(request, "lstm.html", context)
