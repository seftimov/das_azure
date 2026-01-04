import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


def create_sequences(data: np.ndarray, lookback: int):
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i + lookback])
        y.append(data[i + lookback, 3])  # close = index 3
    return np.array(X), np.array(y)


def train_and_predict(
        df: pd.DataFrame,
        lookback: int = 30,
        epochs: int = 20,
        batch_size: int = 32,
        split_ratio: float = 0.7,
        save_model_path: str | None = None,
        verbose: int = 1
):
    df = df.sort_values("date").reset_index(drop=True).copy()

    features = ["open", "high", "low", "close", "volume"]
    data = df[features].astype(float).values

    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    X, y = create_sequences(data_scaled, lookback)
    if len(X) == 0:
        raise ValueError("Not enough data for chosen lookback.")

    split_index = int(len(X) * split_ratio)
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    n_features = X.shape[2]

    model = Sequential()
    model.add(LSTM(64, input_shape=(lookback, n_features), return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(32))
    model.add(Dropout(0.2))
    model.add(Dense(16, activation="relu"))
    model.add(Dense(1))

    model.compile(optimizer="adam", loss="mse")

    callbacks = [EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)]

    if save_model_path:
        os.makedirs(os.path.dirname(save_model_path), exist_ok=True)
        callbacks.append(ModelCheckpoint(save_model_path, monitor="val_loss", save_best_only=True))

    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=verbose
    )

    y_pred_scaled = model.predict(X_test).reshape(-1, 1)

    def invert_close(arr):
        n = len(arr)
        filler = np.zeros((n, data.shape[1]))
        filler[:, 3] = arr[:, 0]
        return scaler.inverse_transform(filler)[:, 3]

    y_test_inv = invert_close(y_test.reshape(-1, 1))
    y_pred_inv = invert_close(y_pred_scaled)

    rmse = float(np.sqrt(mean_squared_error(y_test_inv, y_pred_inv)))
    mape = float(mean_absolute_percentage_error(y_test_inv, y_pred_inv))
    r2 = float(r2_score(y_test_inv, y_pred_inv))

    test_start_idx = lookback + split_index
    test_dates = pd.to_datetime(
        df["date"].iloc[test_start_idx:test_start_idx + len(y_test_inv)]
    ).dt.strftime("%Y-%m-%d").tolist()

    return {
        "model": model,
        "history": history.history,
        "metrics": {"rmse": rmse, "mape": mape, "r2": r2},
        "y_test": y_test_inv.tolist(),
        "y_pred": y_pred_inv.tolist(),
        "test_dates": test_dates,
        "scaler": scaler
    }


def forecast_future(model, df, scaler, lookback, n_steps, freq="D"):
    features = ["open", "high", "low", "close", "volume"]
    data = df[features].astype(float).values
    data_scaled = scaler.transform(data)

    window = data_scaled[-lookback:].copy()
    preds_scaled = []

    for _ in range(n_steps):
        X_input = window.reshape(1, lookback, len(features))
        next_close_scaled = float(model.predict(X_input, verbose=0)[0, 0])
        preds_scaled.append(next_close_scaled)

        last_row = window[-1].copy()
        last_row[3] = next_close_scaled
        window = np.vstack([window[1:], last_row])

    filler = np.zeros((n_steps, len(features)))
    filler[:, 3] = preds_scaled
    preds = scaler.inverse_transform(filler)[:, 3]

    last_date = pd.to_datetime(df["date"].iloc[-1])

    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=n_steps,
        freq=freq
    ).strftime("%Y-%m-%d").tolist()

    return future_dates, preds.tolist()
