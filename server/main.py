# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from services.stock_predictor import predict_next_day_price, predict_future_prices
from services.utils import fetch_stock_data, format_historical_data
from services.model_trainer import train_and_save_model
import os
import re

app = Flask(__name__)
CORS(app)

# --- DYNAMIC TICKER MAPPING ---
nse_data, bse_data = {}, {}
try:
    from data.nse_tickers import nse_data
except ImportError:
    print("WARNING: Could not import NSE data. Run 'generate_data_files.py'.")
try:
    from data.bse_tickers import bse_data
except ImportError:
    print("WARNING: Could not import BSE data. Run 'generate_data_files.py'.")

TICKER_MAP = {**nse_data, **bse_data}
TICKER_MAP.update({
    "NIFTY 50": "^NSEI", "SENSEX": "^BSESN", "DOW JONES": "^DJI", "NASDAQ": "^IXIC",
})

def is_valid_ticker(ticker):
    """Validates the ticker symbol's characters after mapping."""
    if not ticker or len(ticker) > 20: return False
    return bool(re.match("^[A-Za-z0-9._^-]+$", ticker))

@app.route('/predict', methods=['POST'])
def predict_stock():
    request_data = request.get_json()
    ticker_input = request_data.get('ticker', '').upper()
    prediction_days = request_data.get('prediction_days', 1)

    if ticker_input in TICKER_MAP:
        ticker_symbol = TICKER_MAP[ticker_input]
    else:
        ticker_symbol = ticker_input

    if not is_valid_ticker(ticker_symbol):
        return jsonify({'error': 'Ticker contains invalid characters.'}), 400

    try:
        # --- FIX APPLIED HERE: HIERARCHICAL TICKER SEARCH ---
        # 1. First, try the symbol as is (e.g., for "AAPL" or a mapped symbol).
        stock_data = fetch_stock_data(ticker_symbol, years=1)
        final_ticker = ticker_symbol

        # 2. If no data, and the symbol contains a '.', try replacing it with a '-'.
        #    This handles cases like "BRK.A" -> "BRK-A".
        if stock_data.empty and '.' in ticker_symbol:
            ticker_with_hyphen = ticker_symbol.replace('.', '-')
            print(f"'{ticker_symbol}' not found. Trying '{ticker_with_hyphen}'...")
            stock_data = fetch_stock_data(ticker_with_hyphen, years=1)
            if not stock_data.empty:
                final_ticker = ticker_with_hyphen

        # 3. If still no data, and it's not an international ticker, try with .NS
        if stock_data.empty and not any(c in ticker_symbol for c in '.-'):
            print(f"'{final_ticker}' not found. Trying with '.NS' suffix...")
            final_ticker = f"{ticker_symbol}.NS"
            stock_data = fetch_stock_data(final_ticker, years=1)

        # 4. If still no data, try with .BO
        if stock_data.empty and not any(c in ticker_symbol for c in '.-'):
            print(f"'{final_ticker}' not found. Trying with '.BO' suffix...")
            final_ticker = f"{ticker_symbol}.BO"
            stock_data = fetch_stock_data(final_ticker, years=1)
        
        # 5. After all attempts, if data is still empty, then it's not found.
        if stock_data.empty:
            return jsonify({'error': f'"{ticker_input}" was not found in our database or on yfinance.'}), 404

        ticker_symbol = final_ticker
        # --- END OF FIX ---

        if len(stock_data) < 60:
            return jsonify({'error': f'Not enough historical data for "{ticker_input}" to make a prediction.'}), 400

        safe_filename = re.sub(r'[^A-Za-z0-9]', '_', ticker_symbol)
        model_path = f"models/{safe_filename}_model.h5"
        scaler_path = f"models/{safe_filename}_scaler.save"

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            print(f"Training new model for {ticker_symbol}...")
            training_data = fetch_stock_data(ticker_symbol, years=10)
            if len(training_data) < 70:
                 return jsonify({'error': f'Not enough historical data for "{ticker_input}" to train a new model.'}), 400
            train_and_save_model(training_data, model_path, scaler_path)

        if prediction_days == 1:
            predictions = predict_next_day_price(stock_data, model_path, scaler_path)
        else:
            predictions = predict_future_prices(stock_data, model_path, scaler_path, days_to_predict=prediction_days)
        
        historical_data = format_historical_data(stock_data)

        return jsonify({
            'predictions': [f'{p:.2f}' for p in predictions],
            'historicalData': historical_data
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    os.makedirs("models", exist_ok=True)
    app.run(debug=True, port=5000)
