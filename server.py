import asyncio
import websockets
import json
import csv
import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string
from threading import Thread
import numpy as np
from sklearn.linear_model import LinearRegression
from collections import deque

# Data storage
data_history = deque(maxlen=100)
prediction_history = []  # Store all predictions
ml_model = LinearRegression()

# CSV file setup
CSV_FILE = 'weather_data.csv'
PREDICTION_CSV_FILE = 'weather_predictions.csv'
CSV_HEADERS = ['timestamp', 'temperature', 'pressure', 'humidity', 'altitude', 'light']
PRED_CSV_HEADERS = ['prediction_time', 'target_time', 'temperature', 'pressure', 'humidity', 'altitude']

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
    
    if not os.path.exists(PREDICTION_CSV_FILE):
        with open(PREDICTION_CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=PRED_CSV_HEADERS)
            writer.writeheader()

def save_to_csv(data):
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow({
            'timestamp': data['received_at'],
            'temperature': data['temperature'],
            'pressure': data['pressure'],
            'humidity': data.get('humidity', 0),
            'altitude': data.get('altitude', 0),
            'light': data['light']
        })

def save_predictions_to_csv(predictions_data):
    with open(PREDICTION_CSV_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=PRED_CSV_HEADERS)
        for pred in predictions_data:
            writer.writerow(pred)

app = Flask(__name__)

# Professional Dashboard HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Weather Station Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header {
            background: rgba(255,255,255,0.95);
            padding: 25px 30px;
            border-radius: 15px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { 
            font-size: 32px; 
            color: #2d3748; 
            margin-bottom: 8px;
            font-weight: 600;
        }
        .header .subtitle { 
            color: #718096; 
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .status { 
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: #48bb78;
            color: white;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        .status::before { 
            content: '●';
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .metric-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0,0,0,0.15);
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }
        .metric-card.temp::before { background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); }
        .metric-card.pressure::before { background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); }
        .metric-card.humidity::before { background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%); }
        .metric-card.altitude::before { background: linear-gradient(90deg, #fa709a 0%, #fee140 100%); }
        .metric-card.light::before { background: linear-gradient(90deg, #30cfd0 0%, #330867 100%); }
        
        .metric-icon {
            font-size: 32px;
            margin-bottom: 12px;
            opacity: 0.9;
        }
        .metric-label {
            font-size: 13px;
            color: #718096;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 42px;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 4px;
        }
        .metric-unit {
            font-size: 16px;
            color: #a0aec0;
            font-weight: 500;
        }
        .metric-prediction {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e2e8f0;
            font-size: 13px;
            color: #718096;
        }
        .metric-prediction strong {
            color: #4299e1;
            font-weight: 600;
        }
        
        .charts-section {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .charts-section h2 {
            font-size: 24px;
            color: #2d3748;
            margin-bottom: 25px;
            font-weight: 600;
        }
        .chart-wrapper {
            margin-bottom: 35px;
            padding-bottom: 35px;
            border-bottom: 1px solid #e2e8f0;
        }
        .chart-wrapper:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .chart-title {
            font-size: 16px;
            color: #4a5568;
            margin-bottom: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .chart-container {
            position: relative;
            height: 280px;
            background: white;
            border-radius: 10px;
            padding: 15px;
        }
        
        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }
            .metric-value { font-size: 32px; }
            .header h1 { font-size: 24px; }
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <script>
        let charts = {};
        
        function createChart(canvasId, label, color) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            return new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Current',
                        data: [],
                        borderColor: color,
                        backgroundColor: color + '15',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }, {
                        label: 'Predicted',
                        data: [],
                        borderColor: color,
                        backgroundColor: color + '30',
                        borderDash: [8, 4],
                        borderWidth: 2,
                        pointRadius: 8,
                        pointStyle: 'star',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'top',
                            labels: { 
                                color: '#4a5568',
                                font: { size: 12, weight: '500' },
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            padding: 12,
                            titleFont: { size: 13, weight: '600' },
                            bodyFont: { size: 12 }
                        }
                    },
                    scales: { 
                        y: { 
                            beginAtZero: false,
                            grid: { color: '#e2e8f0', drawBorder: false },
                            ticks: { color: '#718096', font: { size: 11 } }
                        },
                        x: { 
                            grid: { display: false, drawBorder: false },
                            ticks: { 
                                color: '#718096',
                                font: { size: 10 },
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 10
                            }
                        }
                    }
                }
            });
        }
        
        function initCharts() {
            charts.temp = createChart('tempChart', 'Temperature', '#f5576c');
            charts.pressure = createChart('pressureChart', 'Pressure', '#00f2fe');
            charts.humidity = createChart('humidityChart', 'Humidity', '#38f9d7');
            charts.altitude = createChart('altitudeChart', 'Altitude', '#fee140');
            charts.light = createChart('lightChart', 'Darkness', '#330867');
        }
        
        function updateValues() {
            fetch('/api/data')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('temp').innerText = data.temperature.toFixed(1);
                    document.getElementById('pressure').innerText = data.pressure.toFixed(1);
                    document.getElementById('humidity').innerText = data.humidity.toFixed(1);
                    document.getElementById('altitude').innerText = data.altitude.toFixed(1);
                    document.getElementById('light').innerText = data.light.toFixed(1);
                    
                    document.getElementById('pred-temp').innerText = data.pred_temperature.toFixed(1);
                    document.getElementById('pred-pressure').innerText = data.pred_pressure.toFixed(1);
                    document.getElementById('pred-humidity').innerText = data.pred_humidity.toFixed(1);
                    document.getElementById('pred-altitude').innerText = data.pred_altitude.toFixed(1);
                    
                    document.getElementById('time').innerText = new Date(data.timestamp).toLocaleString();
                    
                    // Update prediction status
                    const statusEl = document.getElementById('prediction-status');
                    if (data.is_predicting) {
                        statusEl.innerText = '🤖 AI Predicting';
                        statusEl.style.background = '#48bb78';
                    } else {
                        const mins = Math.floor(data.time_remaining / 60);
                        const secs = data.time_remaining % 60;
                        statusEl.innerText = `⏳ ${mins}:${secs.toString().padStart(2, '0')} until prediction`;
                        statusEl.style.background = '#ed8936';
                    }
                    
                    // Update prediction count
                    if (data.prediction_count !== undefined) {
                        document.getElementById('prediction-count').innerText = 
                            `${data.prediction_count} prediction sets saved`;
                    }
                });
        }
        
        function updateCharts() {
            fetch('/api/history')
                .then(r => r.json())
                .then(data => {
                    if (!data.is_predicting) {
                        // Before 3 minutes - show only historical data
                        const histLabels = data.timestamps.slice(-20);
                        
                        updateChartNoPredict(charts.temp, histLabels, data.temperatures.slice(-20));
                        updateChartNoPredict(charts.pressure, histLabels, data.pressures.slice(-20));
                        updateChartNoPredict(charts.humidity, histLabels, data.humidities.slice(-20));
                        updateChartNoPredict(charts.altitude, histLabels, data.altitudes.slice(-20));
                        updateLightChart(charts.light, histLabels, data.lights.slice(-20));
                    } else {
                        // After 3 minutes - show historical + predictions
                        const histLabels = data.timestamps.slice(-20);
                        const histTemps = data.temperatures.slice(-20);
                        const histPressures = data.pressures.slice(-20);
                        const histHumidities = data.humidities.slice(-20);
                        const histAltitudes = data.altitudes.slice(-20);
                        const histLights = data.lights.slice(-20);
                        const allLabels = [...histLabels, ...data.pred_timestamps];
                        
                        updateChartWithPredict(charts.temp, allLabels, histTemps, data.pred_temperatures);
                        updateChartWithPredict(charts.pressure, allLabels, histPressures, data.pred_pressures);
                        updateChartWithPredict(charts.humidity, allLabels, histHumidities, data.pred_humidities);
                        updateChartWithPredict(charts.altitude, allLabels, histAltitudes, data.pred_altitudes);
                        updateLightChart(charts.light, histLabels, histLights);
                    }
                });
        }
        
        function updateChartNoPredict(chart, labels, realData) {
            chart.data.labels = labels;
            chart.data.datasets[0].data = realData;
            chart.data.datasets[1].data = [];
            chart.update('none');
        }
        
        function updateChartWithPredict(chart, allLabels, realData, predData) {
            const histCount = realData.length;
            const predCount = predData.length;
            
            chart.data.labels = allLabels;
            // Real data for historical part, null for prediction part
            chart.data.datasets[0].data = [...realData, ...Array(predCount).fill(null)];
            // Null for historical part, prediction values for prediction part
            chart.data.datasets[1].data = [...Array(histCount).fill(null), ...predData];
            chart.update('none');
        }
        
        function updateLightChart(chart, labels, realData) {
            chart.data.labels = labels.slice(-20);
            chart.data.datasets[0].data = realData.slice(-20);
            chart.data.datasets[1].data = [];
            chart.update('none');
        }
        
        window.onload = function() {
            initCharts();
            updateValues();
            updateCharts();
            setInterval(updateValues, 2000);
            setInterval(updateCharts, 5000);
        };
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌤️ Weather Station </h1>
            <div class="subtitle">
                <span class="status">Live</span>
                <span id="time">--</span>
                <span id="prediction-status" style="margin-left: 20px; padding: 4px 12px; background: #ed8936; color: white; border-radius: 20px; font-size: 12px;">
                    Collecting data...
                </span>
                <span id="prediction-count" style="margin-left: 10px; color: #718096; font-size: 12px;">
                    0 predictions saved
                </span>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card temp">
                <div class="metric-icon">🌡️</div>
                <div class="metric-label">Temperature</div>
                <div>
                    <span class="metric-value" id="temp">--</span>
                    <span class="metric-unit">°C</span>
                </div>
                <div class="metric-prediction">
                    Predicted: <strong><span id="pred-temp">--</span>°C</strong>
                </div>
            </div>
            
            <div class="metric-card pressure">
                <div class="metric-icon">🌀</div>
                <div class="metric-label">Pressure</div>
                <div>
                    <span class="metric-value" id="pressure">--</span>
                    <span class="metric-unit">hPa</span>
                </div>
                <div class="metric-prediction">
                    Predicted: <strong><span id="pred-pressure">--</span> hPa</strong>
                </div>
            </div>
            
            <div class="metric-card humidity">
                <div class="metric-icon">💧</div>
                <div class="metric-label">Humidity</div>
                <div>
                    <span class="metric-value" id="humidity">--</span>
                    <span class="metric-unit">%</span>
                </div>
                <div class="metric-prediction">
                    Predicted: <strong><span id="pred-humidity">--</span>%</strong>
                </div>
            </div>
            
            <div class="metric-card altitude">
                <div class="metric-icon">⛰️</div>
                <div class="metric-label">Altitude</div>
                <div>
                    <span class="metric-value" id="altitude">--</span>
                    <span class="metric-unit">m</span>
                </div>
                <div class="metric-prediction">
                    Predicted: <strong><span id="pred-altitude">--</span> m</strong>
                </div>
            </div>
            
            <div class="metric-card light">
                <div class="metric-icon">💡</div>
                <div class="metric-label">Light</div>
                <div>
                    <span class="metric-value" id="light">--</span>
                    <span class="metric-unit">%</span>
                </div>
            </div>
        </div>
        
        <div class="charts-section">
            <h2>📊 Historical Data & ML Predictions</h2>
            
            <div class="chart-wrapper">
                <div class="chart-title">🌡️ Temperature Trend</div>
                <div class="chart-container">
                    <canvas id="tempChart"></canvas>
                </div>
            </div>
            
            <div class="chart-wrapper">
                <div class="chart-title">🌀 Atmospheric Pressure</div>
                <div class="chart-container">
                    <canvas id="pressureChart"></canvas>
                </div>
            </div>
            
            <div class="chart-wrapper">
                <div class="chart-title">💧 Relative Humidity</div>
                <div class="chart-container">
                    <canvas id="humidityChart"></canvas>
                </div>
            </div>
            
            <div class="chart-wrapper">
                <div class="chart-title">⛰️ Altitude Measurement</div>
                <div class="chart-container">
                    <canvas id="altitudeChart"></canvas>
                </div>
            </div>
            
            <div class="chart-wrapper">
                <div class="chart-title">💡 Light Intensity</div>
                <div class="chart-container">
                    <canvas id="lightChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# WebSocket Server
async def websocket_handler(websocket):
    client_addr = websocket.remote_address
    print(f"✅ Client connected: {client_addr}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                data['received_at'] = datetime.now().isoformat()
                data_history.append(data)
                
                # Save to CSV
                save_to_csv(data)
                
                print(f"📊 Temp={data['temperature']:.1f}°C, Pressure={data['pressure']:.1f}hPa, "
                      f"Humidity={data.get('humidity', 0):.1f}%, Altitude={data.get('altitude', 0):.1f}m, "
                      f"Light={data['light']:.1f}% | Saved to CSV")
                
                await websocket.send("OK")
                
                # Train ML model after 3 minutes (36 readings)
                if len(data_history) >= 36:
                    train_model()
            except json.JSONDecodeError as e:
                print(f"❌ JSON Error: {e}")
            except Exception as e:
                print(f"❌ Processing Error: {e}")
    except websockets.exceptions.ConnectionClosed:
        print(f"⚠️ Client disconnected: {client_addr}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def train_model():
    # Need at least 36 readings (3 minutes at 5 sec intervals)
    if len(data_history) < 36:
        return
    
    temps = [d['temperature'] for d in data_history]
    pressures = [d['pressure'] for d in data_history]
    humidities = [d.get('humidity', 50) for d in data_history]
    altitudes = [d.get('altitude', 0) for d in data_history]
    X = np.arange(len(temps)).reshape(-1, 1)
    
    # Train model only for temp, pressure, humidity, altitude (not light)
    ml_model.fit(X, np.column_stack([temps, pressures, humidities, altitudes]))
    print(f"🤖 ML Model trained with {len(temps)} data points")

def predict_future():
    """
    Predict future weather values
    Returns: tuple of (pred_temps, pred_pressures, pred_humidities, pred_altitudes)
    Each is a list of predicted values
    """
    # Need 36 readings (3 minutes) before predicting
    if len(data_history) < 36:
        return ([], [], [], [])
    
    # Predict next 60 points (5 minutes ahead at 5 sec intervals)
    current_len = len(data_history)
    future_indices = np.arange(current_len, current_len + 60).reshape(-1, 1)
    
    # Get predictions as numpy array
    predictions = ml_model.predict(future_indices)
    
    # Extract predictions for each variable
    # predictions shape is (60, 4) - 60 samples, 4 features
    pred_temps = predictions[:, 0].tolist()
    pred_pressures = predictions[:, 1].tolist()
    pred_humidities = predictions[:, 2].tolist()
    pred_altitudes = predictions[:, 3].tolist()
    
    # Store predictions with timestamp
    prediction_time = datetime.now()
    last_data_time = datetime.fromisoformat(data_history[-1]['received_at'])
    
    predictions_to_save = []
    for i in range(len(pred_temps)):
        target_time = last_data_time + timedelta(seconds=(i + 1) * 5)
        predictions_to_save.append({
            'prediction_time': prediction_time.isoformat(),
            'target_time': target_time.isoformat(),
            'temperature': pred_temps[i],
            'pressure': pred_pressures[i],
            'humidity': pred_humidities[i],
            'altitude': pred_altitudes[i]
        })
    
    # Save predictions to CSV
    save_predictions_to_csv(predictions_to_save)
    
    # Store in memory for plotting
    prediction_history.append({
        'prediction_time': prediction_time.isoformat(),
        'predictions': predictions_to_save
    })
    
    # Keep only last 20 prediction sets
    if len(prediction_history) > 20:
        prediction_history.pop(0)
    
    return pred_temps, pred_pressures, pred_humidities, pred_altitudes

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def get_data():
    if not data_history:
        return json.dumps({
            'temperature': 0, 'pressure': 0, 'humidity': 0, 'altitude': 0, 'light': 0,
            'pred_temperature': 0, 'pred_pressure': 0, 'pred_humidity': 0, 
            'pred_altitude': 0, 'is_predicting': False, 'time_remaining': 180,
            'timestamp': 'Waiting for data...'
        })
    
    latest = data_history[-1]
    
    # FIX: Properly unpack the tuple returned by predict_future()
    pred_temps, pred_pressures, pred_humidities, pred_altitudes = predict_future()
    
    # Calculate time remaining until predictions start
    time_remaining = max(0, 180 - (len(data_history) * 5))
    is_predicting = len(data_history) >= 36
    
    # Get last prediction value for display
    if is_predicting and len(pred_temps) > 0:
        pred_temp = pred_temps[-1]
        pred_pressure = pred_pressures[-1]
        pred_humidity = pred_humidities[-1]
        pred_altitude = pred_altitudes[-1]
    else:
        pred_temp = latest['temperature']
        pred_pressure = latest['pressure']
        pred_humidity = latest.get('humidity', 50)
        pred_altitude = latest.get('altitude', 0)
    
    return json.dumps({
        'temperature': latest['temperature'],
        'pressure': latest['pressure'],
        'humidity': latest.get('humidity', 50),
        'altitude': latest.get('altitude', 0),
        'light': latest['light'],
        'pred_temperature': pred_temp,
        'pred_pressure': pred_pressure,
        'pred_humidity': pred_humidity,
        'pred_altitude': pred_altitude,
        'is_predicting': is_predicting,
        'time_remaining': time_remaining,
        'prediction_count': len(prediction_history),
        'timestamp': latest['received_at']
    })

@app.route('/api/history')
def get_history():
    if not data_history:
        return json.dumps({
            'timestamps': [], 'temperatures': [], 'pressures': [], 
            'humidities': [], 'altitudes': [], 'lights': [],
            'pred_temperatures': [], 'pred_pressures': [], 
            'pred_humidities': [], 'pred_altitudes': [],
            'pred_timestamps': [], 'is_predicting': False
        })
    
    timestamps = [d['received_at'].split('T')[1][:8] for d in data_history]
    temperatures = [d['temperature'] for d in data_history]
    pressures = [d['pressure'] for d in data_history]
    humidities = [d.get('humidity', 50) for d in data_history]
    altitudes = [d.get('altitude', 0) for d in data_history]
    lights = [d['light'] for d in data_history]
    
    # FIX: Properly unpack the tuple returned by predict_future()
    pred_temps, pred_pressures, pred_humidities, pred_altitudes = predict_future()
    
    is_predicting = len(data_history) >= 36
    
    # Generate prediction timestamps
    if is_predicting and len(pred_temps) > 0:
        pred_timestamps = []
        last_time = datetime.fromisoformat(data_history[-1]['received_at'])
        # Only show first 12 predictions for chart clarity
        for i in range(min(12, len(pred_temps))):
            future_time = last_time + timedelta(seconds=(i + 1) * 5)
            pred_timestamps.append(future_time.strftime('%H:%M:%S'))
        
        # Limit predictions to 12 for display
        pred_temps = pred_temps[:12]
        pred_pressures = pred_pressures[:12]
        pred_humidities = pred_humidities[:12]
        pred_altitudes = pred_altitudes[:12]
    else:
        pred_timestamps = []
        pred_temps = []
        pred_pressures = []
        pred_humidities = []
        pred_altitudes = []
    
    return json.dumps({
        'timestamps': timestamps,
        'temperatures': temperatures,
        'pressures': pressures,
        'humidities': humidities,
        'altitudes': altitudes,
        'lights': lights,
        'pred_timestamps': pred_timestamps,
        'pred_temperatures': pred_temps,
        'pred_pressures': pred_pressures,
        'pred_humidities': pred_humidities,
        'pred_altitudes': pred_altitudes,
        'is_predicting': is_predicting
    })

def start_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def main():
        async with websockets.serve(
            websocket_handler, 
            "0.0.0.0", 
            8765,
            ping_interval=20,
            ping_timeout=10
        ):
            print("✅ WebSocket server started on ws://0.0.0.0:8765")
            await asyncio.Future()
    
    loop.run_until_complete(main())

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    print("🚀 Starting Professional Weather Station Server...")
    print("📊 Dashboard: http://localhost:5000")
    print("💾 Data logging to: weather_data.csv")
    print("🔮 Predictions logging to: weather_predictions.csv")
    
    # Initialize CSV file
    init_csv()
    
    ws_thread = Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    start_flask()