from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator, CCIIndicator, SMAIndicator, EMAIndicator, WMAIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice as VWAP


def calculate_indicators(df):
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()

    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
    df["stoch"] = stoch.stoch()

    df["adx"] = ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()

    df["cci"] = CCIIndicator(high=df['high'], low=df['low'], close=df['close']).cci()

    df["sma_20"] = SMAIndicator(close=df["close"], window=20).sma_indicator()

    df["ema_20"] = EMAIndicator(close=df["close"], window=20).ema_indicator()

    df["wma_20"] = WMAIndicator(close=df["close"], window=20).wma()

    boll = BollingerBands(close=df["close"])
    df["bb_mid"] = boll.bollinger_mavg()
    df["bb_upper"] = boll.bollinger_hband()
    df["bb_lower"] = boll.bollinger_lband()

    df["vwap"] = VWAP(high=df['high'], low=df['low'], close=df['close'], volume=df['volume']).vwap

    return df
