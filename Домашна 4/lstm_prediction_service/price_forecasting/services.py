import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tqdm.keras import TqdmCallback


def create_sequences(data: np.ndarray, lookback: int):
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i + lookback])
        y.append(data[i + lookback, 3])
    return np.array(X), np.array(y)


def train_and_forecast(
        df: pd.DataFrame,
        lookback: int,
        epochs: int,
        horizon: int,
        split_ratio: float = 0.7
):
    df = df.sort_values("date").reset_index(drop=True)

    features = ["open", "high", "low", "close", "volume"]
    data = df[features].astype(float).values

    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    X, y = create_sequences(data_scaled, lookback)
    if len(X) == 0:
        raise ValueError("Not enough data for LSTM")

    split = int(len(X) * split_ratio)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(lookback, X.shape[2])),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse")

    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=32,
        callbacks=[EarlyStopping(patience=5, restore_best_weights=True),
                   TqdmCallback(verbose=1)
                   ],
        verbose=0
    )

    y_pred_scaled = model.predict(X_test).reshape(-1, 1)

    def invert(arr):
        filler = np.zeros((len(arr), data.shape[1]))
        filler[:, 3] = arr[:, 0]
        return scaler.inverse_transform(filler)[:, 3]

    y_test_inv = invert(y_test.reshape(-1, 1))
    y_pred_inv = invert(y_pred_scaled)

    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test_inv, y_pred_inv))),
        "mape": float(mean_absolute_percentage_error(y_test_inv, y_pred_inv)),
        "r2": float(r2_score(y_test_inv, y_pred_inv))
    }

    window = data_scaled[-lookback:].copy()
    preds_scaled = []

    for _ in range(horizon):
        pred = model.predict(window.reshape(1, lookback, X.shape[2]), verbose=0)[0, 0]
        preds_scaled.append(pred)
        window = np.vstack([window[1:], np.hstack([window[-1][:3], pred, window[-1][4]])])

    filler = np.zeros((horizon, data.shape[1]))
    filler[:, 3] = preds_scaled
    future_preds = scaler.inverse_transform(filler)[:, 3]

    last_date = pd.to_datetime(df["date"].iloc[-1])
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=horizon,
        freq="D"
    ).strftime("%Y-%m-%d").tolist()

    return {
        "metrics": metrics,
        "test_dates": df["date"].iloc[lookback + split:lookback + split + len(y_test_inv)].dt.strftime(
            "%Y-%m-%d").tolist(),
        "y_test": y_test_inv.tolist(),
        "y_pred": y_pred_inv.tolist(),
        "future_dates": future_dates,
        "future_preds": future_preds.tolist()
    }
