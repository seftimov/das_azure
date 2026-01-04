import json
import pandas as pd
from datetime import date
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignupUserForm, CoinFilterForm, OnchainSentimentForm
from .models import Coins, OhlcvData, News, OnchainMetrics
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

    # Base queryset
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

        df_complete = df.dropna(subset=[
            "open", "high", "low", "close",
            "ema_20", "sma_20", "wma_20",
            "bb_upper", "bb_lower", "vwap",
            "rsi", "stoch", "macd", "macd_signal", "adx", "cci"
        ]).reset_index(drop=True)

        if len(df_complete) < 5:
            context.update({
                "selected_symbol": symbol,
                "timeframe": timeframe,
                "table": df.tail(40).to_html(classes="table table-striped", index=False),
                "error": f"Not enough {timeframe} data to plot indicators (need 5+, got {len(df_complete)}).",
            })
            return render(request, "technical_analysis.html", context)

        signals = []
        scores = []
        for i, row in df_complete.iterrows():
            score = 0
            if row["rsi"] < 35:
                score += 1
            elif row["rsi"] > 65:
                score -= 1
            if row["macd"] > row["macd_signal"]:
                score += 1
            elif row["macd"] < row["macd_signal"]:
                score -= 1
            if row["close"] > row["ema_20"]:
                score += 1
            elif row["close"] < row["ema_20"]:
                score -= 1
            trending = row["adx"] > 20

            signal = "BUY" if (score >= 2 and trending) else "SELL" if (score <= -2 and trending) else "HOLD"
            signals.append(signal)
            scores.append(score)

        df_complete["score"] = scores
        df_complete["signal"] = signals

        df_chart = df_complete.tail(300)

        candlestick_data = []
        markers_data = []
        ema20_data = []
        sma20_data = []
        wma20_data = []
        rsi_data = []
        macd_data = []
        macd_signal_data = []
        stoch_data = []
        adx_data = []
        cci_data = []
        bb_upper_data = []
        bb_lower_data = []
        vwap_data = []

        for _, row in df_chart.iterrows():
            t = row["date"].strftime("%Y-%m-%d")

            candlestick_data.append({
                "time": t,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
            })

            if row["signal"] == "BUY":
                markers_data.append({
                    "time": t,
                    "position": "belowBar",
                    "color": "#26a69a",
                    "shape": "arrowUp",
                    "text": "BUY",
                })
            elif row["signal"] == "SELL":
                markers_data.append({
                    "time": t,
                    "position": "aboveBar",
                    "color": "#ef5350",
                    "shape": "arrowDown",
                    "text": "SELL",
                })

            ema20_data.append({"time": t, "value": row["ema_20"]})
            sma20_data.append({"time": t, "value": row["sma_20"]})
            wma20_data.append({"time": t, "value": row["wma_20"]})
            vwap_data.append({"time": t, "value": row["vwap"]})
            bb_upper_data.append({"time": t, "value": row["bb_upper"]})
            bb_lower_data.append({"time": t, "value": row["bb_lower"]})

            rsi_data.append({"time": t, "value": row["rsi"]})
            stoch_data.append({"time": t, "value": row["stoch"]})
            macd_data.append({"time": t, "value": row["macd"]})
            macd_signal_data.append({"time": t, "value": row["macd_signal"]})
            adx_data.append({"time": t, "value": row["adx"]})
            cci_data.append({"time": t, "value": row["cci"]})

        context.update({
            "selected_symbol": symbol,
            "timeframe": timeframe,
            "table": df_complete[
                ['date', 'rsi', 'macd', 'macd_signal', 'stoch', 'adx', 'cci', 'sma_20', 'ema_20', 'wma_20', 'bb_mid',
                 'bb_upper', 'bb_lower', 'vwap', 'score', 'signal']].tail(40).to_html(classes="table table-striped",
                                                                                      index=False),
            "candlestick_data": json.dumps(candlestick_data),
            "markers_data": json.dumps(markers_data),
            "ema20_data": json.dumps(ema20_data),
            "sma20_data": json.dumps(sma20_data),
            "wma20_data": json.dumps(wma20_data),
            "vwap_data": json.dumps(vwap_data),
            "bb_upper_data": json.dumps(bb_upper_data),
            "bb_lower_data": json.dumps(bb_lower_data),
            "rsi_data": json.dumps(rsi_data),
            "stoch_data": json.dumps(stoch_data),
            "macd_data": json.dumps(macd_data),
            "macd_signal_data": json.dumps(macd_signal_data),
            "adx_data": json.dumps(adx_data),
            "cci_data": json.dumps(cci_data),
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


REQUIRED_COLUMNS = [
    "time",
    "date",
    "adractcnt",
    "txcnt",
    "txtfrcnt",
    "flowinexusd",
    "flowoutexusd",
    "hashrate",
    "capmrktcurusd",
    "nvt_ratio",
    "capmvrvcur",
    "sentiment_score",
    "sentiment_label",
]


def label_sentiment(x):
    if pd.isna(x):
        return "no news"
    if x > 0.05:
        return "positive"
    if x < -0.05:
        return "negative"
    return "neutral"


def get_news_items(symbol: str | None):
    if not symbol:
        return []

    qs = (
        News.objects.filter(symbol__iexact=symbol)
        .order_by("-news_datetime")
    )

    items = []
    now = pd.Timestamp.utcnow()

    for n in qs:
        dt = n.news_datetime
        if dt:
            news_date = (
                dt.strftime("%b %d") if dt.year == now.year else dt.strftime("%b %d, %Y")
            )
        else:
            news_date = "Recent"

        # Pick best available text
        final_text = next(
            (v.strip() for v in (n.description, n.text, n.title) if v and v.strip()),
            "No description available",
        )

        score = float(n.vader_score) if n.vader_score is not None else None

        items.append({
            "title": str(n.title or "No title")[:100].strip(),
            "text": final_text[:120],
            "date": news_date,
            "symbol": symbol.upper(),
            "vader_score": score,
            "url": n.url or None,
        })

    return items


def onchain_sentiment_page(request):
    db_symbols = Coins.objects.order_by("market_cap_rank").values_list("symbol", flat=True)
    symbols = [s.upper() for s in db_symbols if s]  # skip nulls
    symbol_choices = [(s, s) for s in symbols]

    rows = None
    selected_symbol = None
    news_items = []

    form = OnchainSentimentForm(request.POST or None)
    form.fields["symbol"].choices = symbol_choices

    if request.method == "POST" and form.is_valid():
        selected_symbol = form.cleaned_data["symbol"]
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")
        only_with_news = form.cleaned_data.get("only_with_news")

        qs = OnchainMetrics.objects.filter(symbol__iexact=selected_symbol)

        if start_date:
            qs = qs.filter(time__date__gte=start_date)
        if end_date:
            qs = qs.filter(time__date__lte=end_date)
        if only_with_news:
            qs = qs.filter(sentiment_score__isnull=False)

        qs = qs.order_by("time")

        # Convert queryset to list of dicts
        rows = []
        for row in qs:
            row_dict = {
                "time": row.time,
                "date": row.date,
                "adractcnt": row.adractcnt,
                "txcnt": row.txcnt,
                "txtfrcnt": row.txtfrcnt,
                "flowinexusd": row.flowinexusd,
                "flowoutexusd": row.flowoutexusd,
                "hashrate": row.hashrate,
                "capmrktcurusd": row.capmrktcurusd,
                "nvt_ratio": row.nvt_ratio,
                "capmvrvcur": row.capmvrvcur,
                "sentiment_score": row.sentiment_score,
            }
            # Add sentiment_label
            row_dict["sentiment_label"] = label_sentiment(row.sentiment_score)
            rows.append(row_dict)

        news_items = get_news_items(selected_symbol)

    return render(
        request,
        "onchain_sentiment.html",
        {
            "form": form,
            "columns": REQUIRED_COLUMNS,
            "rows": rows,
            "selected_symbol": selected_symbol,
            "news_items": news_items,
        },
    )
