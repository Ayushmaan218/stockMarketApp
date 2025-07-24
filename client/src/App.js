// frontend/src/App.js

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler
);

const Spinner = () => (
  <div className="text-center my-8">
    <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-cyan-500 mx-auto"></div>
    <p className="mt-4 text-lg text-gray-400">Fetching Data...</p>
  </div>
);

function App() {
  const [ticker, setTicker] = useState('');
  const [predictions, setPredictions] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [predictionDays, setPredictionDays] = useState(1);
  const resultRef = useRef(null);
  const isInitialMount = useRef(true);

  const fetchPrediction = async () => {
    if (!ticker) return;
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('http://127.0.0.1:5000/predict', {
        ticker: ticker.toUpperCase(),
        prediction_days: predictionDays,
      });

      const data = response.data;
      setPredictions(data.predictions);
      const historical = data.historicalData;
      setChartData({
        labels: historical.dates,
        datasets: [{
          label: `${ticker.toUpperCase()} Close Price`,
          data: historical.prices,
          borderColor: 'rgba(56, 189, 248, 1)',
          backgroundColor: 'rgba(56, 189, 248, 0.2)',
          fill: true,
          tension: 0.3,
          pointRadius: 0,
        }],
      });
    } catch (err) {
      const errorMessage = err.response ? err.response.data.error : 'Could not connect to the server.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handlePredict = (e) => {
    e.preventDefault();
    setPredictions([]);
    setChartData(null);
    fetchPrediction();
  };

  useEffect(() => {
      if (isInitialMount.current) {
          isInitialMount.current = false;
          return;
      }
      if (ticker) {
          fetchPrediction();
      }
  }, [predictionDays]);


  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { 
      legend: { display: false }, 
      title: { 
        display: true, 
        text: '1-Year Historical Price', // Title is now static
        font: { size: 18, weight: 'bold' }, 
        color: '#E5E7EB' 
      } 
    },
    scales: {
      x: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
      y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
    },
  };

  const ControlButton = ({ value, label, state, setState }) => (
    <button
      onClick={() => setState(value)}
      className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors ${state === value ? 'bg-cyan-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans antialiased">
      <main className="container mx-auto px-4 py-10 sm:py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">AI Stock Predictor</h1>
          <p className="text-lg text-gray-400">Forecast future stock prices using an LSTM Neural Network</p>
        </div>

        <div className="max-w-2xl mx-auto bg-gray-800/50 backdrop-blur-sm p-6 sm:p-8 rounded-xl shadow-2xl border border-gray-700">
          <form onSubmit={handlePredict}>
            <div className="flex flex-col sm:flex-row gap-4">
              <input type="text" value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="e.g., AAPL, TSLA, GOOG" className="flex-grow w-full px-4 py-3 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500" />
              <button type="submit" disabled={loading} className="w-full sm:w-auto px-8 py-3 bg-cyan-600 font-semibold rounded-lg hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 transition-all duration-300 disabled:bg-gray-600 disabled:cursor-not-allowed">
                {loading ? 'Analyzing...' : 'Predict'}
              </button>
            </div>
          </form>
          {/* --- FIX APPLIED HERE --- */}
          {/* The History buttons have been removed for a cleaner UI. */}
          <div className="mt-6 border-t border-gray-700 pt-5 flex items-center justify-center gap-3">
              <span className="text-gray-400 text-sm font-medium">Forecast:</span>
              <ControlButton value={1} label="Next Day" state={predictionDays} setState={setPredictionDays} />
              <ControlButton value={7} label="7 Days" state={predictionDays} setState={setPredictionDays} />
          </div>
        </div>

        <div ref={resultRef} className="mt-8">
          {loading && <Spinner />}
          {error && <p className="text-center text-red-400 mt-6 text-lg bg-red-900/50 py-3 px-4 rounded-lg max-w-xl mx-auto">{error}</p>}
          {predictions.length > 0 && (
            <div className="mt-12 text-center animate-fade-in">
              <h2 className="text-2xl text-gray-400 mb-4">{predictionDays === 1 ? 'Predicted Next Close' : `Forecast for Next ${predictionDays} Days`} for {ticker.toUpperCase()}:</h2>
              {predictions.length === 1 ? (
                <p className="text-6xl font-bold text-cyan-400">${predictions[0]}</p>
              ) : (
                <div className="flex justify-center items-center gap-2 sm:gap-4 mt-4 flex-wrap">
                  {predictions.map((p, i) => (
                    <div key={i} className="bg-gray-800 p-3 rounded-lg min-w-[80px]">
                      <p className="text-xs text-gray-400">Day {i + 1}</p>
                      <p className="text-xl sm:text-2xl font-bold text-cyan-400">${p}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {chartData && (
            <div className="mt-8 max-w-4xl h-[400px] mx-auto bg-gray-800/50 p-4 sm:p-6 rounded-xl shadow-2xl border border-gray-700 animate-fade-in">
              <Line data={chartData} options={chartOptions} />
            </div>
          )}
        </div>

        <footer className="text-center mt-16 text-gray-500 text-sm">
          <p>Disclaimer: This is an educational project and not financial advice.</p>
        </footer>
      </main>
    </div>
  );
}

export default App;
