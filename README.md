# 🌤️ IoT Weather Station with ML Predictions

A real-time IoT weather monitoring system built with ESP32, featuring machine learning-based weather predictions, live data visualization, and a beautiful web dashboard.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![ESP32](https://img.shields.io/badge/ESP32-supported-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📹 Demo

![WhatsApp Image 2025-10-18 at 20 02 25_b5b3c975](https://github.com/user-attachments/assets/87dcf1a1-159a-4440-aac4-a5bd20af2fd0)

![WhatsApp Image 2025-10-18 at 20 03 01_331eb3d5](https://github.com/user-attachments/assets/5b1d849b-5728-48ea-a181-1b8b887f3d20)
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/0603be6f-4d95-4f3d-b2f1-a88230f88013" />


## ✨ Features


### Hardware & Sensors
- 🌡️ **Real-time Weather Monitoring** - Temperature, Pressure, Humidity, Altitude, Light intensity
- 📱 **OLED Display** - 5 different display modes with potentiometer control
- 📡 **WiFi Connectivity** - WebSocket communication for real-time data streaming
- ⚡ **ESP32 Powered** - Low-power, high-performance microcontroller

### Software & Intelligence
- 🤖 **Machine Learning Predictions** - Linear Regression model predicts weather 5 minutes ahead
- 📊 **Live Dashboard** - Beautiful, responsive web interface with real-time charts
- 💾 **Data Logging** - Automatic CSV logging of all readings and predictions
- 🔄 **WebSocket Communication** - Real-time bidirectional data flow
- 📈 **Historical Analysis** - Visual charts showing trends and predictions

### Web Dashboard
- ⚡ Real-time metric cards with live updates
- 📉 Interactive Chart.js visualizations
- 🎨 Modern, gradient-based design
- 📱 Fully responsive for mobile/tablet/desktop
- 🔮 Prediction visualization with historical data

## 🛠️ Hardware Components

| Component | Model | Purpose |
|-----------|-------|---------|
| Microcontroller | ESP32 | Main processing unit |
| Temperature/Pressure Sensor | BMP180 | Measures temperature, pressure, altitude |
| Light Sensor | LDR (Photoresistor) | Measures ambient light |
| Display | SSD1306 OLED (128x64) | Shows readings locally |
| Potentiometer | 10kΩ | Switches between display modes |

### Pin Configuration

```
ESP32 Connections:
├── BMP180 (I2C Bus 1)
│   ├── SDA → GPIO 21
│   └── SCL → GPIO 22
├── OLED Display (I2C Bus 0)
│   ├── SDA → GPIO 26
│   └── SCL → GPIO 27
├── Sensors (Analog)
│   ├── LDR → GPIO 34
│   └── Potentiometer → GPIO 35
└── Power
    ├── VCC → 3.3V
    └── GND → GND
```

> 📝 **Note:** Circuit diagram will be added soon!

## 🚀 Getting Started

### Prerequisites

**Hardware:**
- ESP32 Development Board
- BMP180 Sensor Module
- SSD1306 OLED Display (128x64)
- LDR (Light Dependent Resistor)
- 10kΩ Potentiometer
- 10kΩ Resistor (for LDR voltage divider)
- Breadboard and jumper wires

**Software:**
- Arduino IDE (1.8.x or higher) or PlatformIO
- Python 3.8 or higher
- pip (Python package manager)

### Arduino Libraries Required

Install these libraries via Arduino Library Manager:

```
- WiFi (built-in)
- WebSocketsClient by Markus Sattler
- Wire (built-in)
- Adafruit BMP085 Library
- ArduinoJson by Benoit Blanchon
- Adafruit GFX Library
- Adafruit SSD1306
```

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/darshansai/iot-weather-station-ml.git
cd iot-weather-station-ml
```

#### 2. Setup Python Server

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure ESP32

Open `Weather_Station.ino` in Arduino IDE and update:

```cpp
// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Python server IP (find using ipconfig/ifconfig)
const char* ws_host = "YOUR_COMPUTER_IP";
const uint16_t ws_port = 8765;
```

#### 4. Upload to ESP32

1. Select **ESP32 Dev Module** from Tools → Board
2. Select the correct COM port
3. Click Upload

#### 5. Run the Server

```bash
python server.py
```

The server will start:
- 🌐 **Web Dashboard:** http://localhost:5000
- 🔌 **WebSocket Server:** ws://0.0.0.0:8765

## 📊 How It Works

### Data Flow

```
ESP32 Sensors → WebSocket → Python Server → ML Model → Web Dashboard
     ↓              ↓              ↓              ↓           ↓
  OLED Display   Real-time    CSV Logging   Predictions   Live Charts
```

### Machine Learning Pipeline

1. **Data Collection:** ESP32 sends readings every 5 seconds
2. **Training Trigger:** After 3 minutes (36 data points), ML model trains
3. **Prediction:** Linear Regression predicts next 5 minutes (60 data points)
4. **Visualization:** Predictions displayed on charts with historical data
5. **CSV Storage:** All predictions saved with timestamps for analysis

### Prediction Model

- **Algorithm:** Linear Regression (scikit-learn)
- **Features:** Temperature, Pressure, Humidity, Altitude
- **Training Data:** Rolling window of last 100 readings
- **Prediction Window:** 5 minutes ahead (60 predictions at 5-second intervals)
- **Update Frequency:** Model retrains with each new data point

## 📁 Project Structure

```
iot-weather-station-ml/
├── Basic_Enginearing_Project.ino    # ESP32 Arduino code
├── server.py                         # Python server with Flask + WebSocket
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── LICENSE                           # MIT License
├── .gitignore                        # Git ignore rules
├── data/                             # Generated data files (gitignored)
│   ├── weather_data.csv             # Real-time sensor readings
│   └── weather_predictions.csv      # ML predictions log
└── docs/                             # Documentation (coming soon)
    ├── circuit_diagram.png
    └── setup_guide.md
```

## 📈 Data Format

### Real-time Data CSV (`weather_data.csv`)

```csv
timestamp,temperature,pressure,humidity,altitude,light
2025-10-18T10:30:45,28.5,1013.2,65.3,42.1,78.9
```

### Predictions CSV (`weather_predictions.csv`)

```csv
prediction_time,target_time,temperature,pressure,humidity,altitude
2025-10-18T10:30:45,2025-10-18T10:35:45,28.7,1013.1,65.5,42.0
```

## 🎯 Future Enhancements

- [ ] Add more sensors (Rain sensor, Wind speed, UV index)
- [ ] Implement advanced ML models (LSTM, Prophet)
- [ ] Weather alerts and notifications
- [ ] Historical data analysis dashboard
- [ ] Mobile app integration
- [ ] Cloud storage (Firebase/AWS)
- [ ] API endpoints for third-party integration
- [ ] Solar power option for outdoor deployment
- [ ] Multi-location support
- [ ] Weather forecast comparison with actual data

## 🔧 Troubleshooting

### ESP32 won't connect to WiFi
- Double-check SSID and password
- Ensure WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check WiFi signal strength

### WebSocket connection fails
- Verify server IP address in Arduino code
- Ensure firewall allows port 8765
- Check if server is running (`python server.py`)

### BMP180 sensor not found
- Verify I2C connections (SDA → 21, SCL → 22)
- Check sensor power (3.3V, not 5V)
- Try I2C scanner sketch to detect address

### OLED display not working
- Confirm separate I2C bus initialization
- Check I2C address (usually 0x3C)
- Verify power connections

### Dashboard shows no data
- Wait for ESP32 to send first reading (5 seconds)
- Check browser console for errors
- Refresh the page

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Darshan Sai**

- GitHub: [@darshansai](https://github.com/darshansai)

## 🙏 Acknowledgments

- Adafruit for excellent sensor libraries
- Chart.js for beautiful visualizations
- ESP32 community for amazing support
- scikit-learn for ML capabilities

## 📞 Support

If you have any questions or need help, please:
- Open an issue in the repository
- Check existing issues for solutions

---

⭐ **Star this repo if you find it helpful!**

Made with ❤️ by Darshan Sai
