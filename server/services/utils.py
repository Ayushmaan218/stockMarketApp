# services/utils.py

import yfinance as yf
from datetime import datetime, timedelta

def fetch_stock_data(ticker, years=1):
    """
    Fetches historical stock data from Yahoo Finance for a given number of years.
    """
    today = datetime.today()
    start_date = today - timedelta(days=years * 365)

    return yf.download(
        ticker, 
        start=start_date.strftime('%Y-%m-%d'), 
        end=today.strftime('%Y-%m-%d')
    )

def format_historical_data(stock_data):
    """Formats the DataFrame for the JSON response."""
    return {
        'dates': [d.strftime('%Y-%m-%d') for d in stock_data.index],
        'prices': [float(p) for p in stock_data['Close'].dropna().values]
    }
