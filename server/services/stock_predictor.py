# services/stock_predictor.py

import numpy as np
from tensorflow.keras.models import load_model
import joblib

def predict_next_day_price(stock_data, model_path, scaler_path):
    """Predicts the closing price for the next single day."""
    model = load_model(model_path)
    scaler = joblib.load(scaler_path)

    # Drop NaN values and check for sufficient data length
    close_prices_df = stock_data[['Close']].dropna()
    look_back = 60
    if len(close_prices_df) < look_back:
        raise ValueError(f"Prediction requires at least {look_back} valid data points, but only got {len(close_prices_df)}.")
        
    close_prices = close_prices_df.values
    scaled_prices = scaler.transform(close_prices)

    last_sequence = scaled_prices[-look_back:]
    X_pred = last_sequence.reshape((1, look_back, 1))

    predicted_price_scaled = model.predict(X_pred, verbose=0)
    predicted_price = scaler.inverse_transform(predicted_price_scaled)[0][0]

    return [predicted_price]


def predict_future_prices(stock_data, model_path, scaler_path, days_to_predict=7):
    """
    Predicts stock prices for a future number of days.
    """
    model = load_model(model_path)
    scaler = joblib.load(scaler_path)

    # Drop NaN values and check for sufficient data length
    close_prices_df = stock_data[['Close']].dropna()
    look_back = 60
    if len(close_prices_df) < look_back:
        raise ValueError(f"Prediction requires at least {look_back} valid data points, but only got {len(close_prices_df)}.")
        
    close_prices = close_prices_df.values
    scaled_prices = scaler.transform(close_prices)

    input_sequence = list(scaled_prices[-look_back:].flatten())
    predictions_scaled = []

    for _ in range(days_to_predict):
        X_pred = np.array(input_sequence[-look_back:]).reshape((1, 60, 1))
        predicted_price_scaled = model.predict(X_pred, verbose=0)[0][0]
        input_sequence.append(predicted_price_scaled)
        predictions_scaled.append(predicted_price_scaled)

    predicted_prices = scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1))
    
    return predicted_prices.flatten().tolist()
