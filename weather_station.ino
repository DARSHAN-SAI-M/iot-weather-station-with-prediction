#include <WiFi.h>
#include <WebSocketsClient.h>
#include <Wire.h>
#include <Adafruit_BMP085.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED Display settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_SDA 26
#define OLED_SCL 27

// BMP180 I2C pins
#define BMP_SDA 21
#define BMP_SCL 22

// Sensor pins
#define LDR_PIN 34
#define POT_PIN 35

// Create separate I2C buses
TwoWire I2C_OLED = TwoWire(0);
TwoWire I2C_BMP = TwoWire(1);

// Initialize display and sensor
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &I2C_OLED, OLED_RESET);
Adafruit_BMP085 bmp;

// WiFi credentials
const char* ssid = "DARSHAN SAI's A26";
const char* password = "sjjuxticiubihwr";

// Python server details
const char* ws_host = "172.24.165.190";
const uint16_t ws_port = 8765;

WebSocketsClient webSocket;

// Display mode (0-4 for 5 different readings)
int displayMode = 0;
unsigned long lastPotRead = 0;

// Store latest readings
float currentTemp = 0;
float currentPressure = 0;
float currentHumidity = 0;
float currentAltitude = 0;
float currentLight = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize separate I2C buses
  I2C_OLED.begin(OLED_SDA, OLED_SCL, 100000);
  I2C_BMP.begin(BMP_SDA, BMP_SCL, 100000);
  
  // Initialize OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    while(1);
  }
  
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("Weather Station");
  display.println("Initializing...");
  display.display();
  delay(1000);
  
  // Initialize BMP180
  if (!bmp.begin(BMP085_STANDARD, &I2C_BMP)) {
    Serial.println("BMP180 not found!");
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("BMP180 Error!");
    display.display();
    while (1) {}
  }
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Connecting WiFi...");
  display.display();
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi Connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
  
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi Connected!");
  display.print("IP: ");
  display.println(WiFi.localIP());
  display.display();
  delay(2000);
  
  // Connect to WebSocket
  webSocket.begin(ws_host, ws_port, "/");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  webSocket.enableHeartbeat(15000, 3000, 2);
  
  Serial.println("Connecting to WebSocket server...");
}

void loop() {
  webSocket.loop();
  
  // Read potentiometer every 100ms to change display mode
  if (millis() - lastPotRead > 100) {
    lastPotRead = millis();
    int potValue = analogRead(POT_PIN);
    
    // Map 0-4095 to 0-4 (5 modes)
    int newMode = map(potValue, 0, 4095, 0, 5);
    if (newMode > 4) newMode = 4;
    
    if (newMode != displayMode) {
      displayMode = newMode;
      Serial.print("Display Mode: ");
      Serial.println(displayMode);
      updateDisplay();
    }
  }
  
  // Read sensors every 5 seconds
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 5000) {
    lastRead = millis();
    sendSensorData();
  }
}

void sendSensorData() {
  // Check if WebSocket is connected
  if (!webSocket.isConnected()) {
    Serial.println("Not connected, skipping send");
    return;
  }
  
  // Read BMP180
  currentTemp = bmp.readTemperature();
  currentPressure = bmp.readPressure() / 100.0;
  currentAltitude = bmp.readAltitude(101325);
  
  // Read LDR 
  int ldrValue = analogRead(LDR_PIN);
  currentLight = 100.0 - ((ldrValue / 4095.0) * 100);
  
  // Calculate humidity (approximation)
  currentHumidity = 50.0 + (25.0 - currentTemp) * 0.5;
  
  // Create JSON
  StaticJsonDocument<256> doc;
  doc["temperature"] = currentTemp;
  doc["pressure"] = currentPressure;
  doc["humidity"] = currentHumidity;
  doc["altitude"] = currentAltitude;
  doc["light"] = currentLight;
  doc["timestamp"] = millis();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send via WebSocket
  webSocket.sendTXT(jsonString);
  
  Serial.println("Sent: " + jsonString);
  
  // Update display with new data
  updateDisplay();
}

void updateDisplay() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Title bar
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextColor(SSD1306_BLACK);
  display.setCursor(2, 2);
  
  switch(displayMode) {
    case 0:
      display.print("TEMPERATURE");
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(3);
      display.setCursor(10, 25);
      display.print(currentTemp, 1);
      display.setTextSize(2);
      display.setCursor(85, 30);
      display.print("C");
      display.drawCircle(78, 28, 3, SSD1306_WHITE);
      break;
      
    case 1:
      display.print("PRESSURE");
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(2);
      display.setCursor(5, 25);
      display.print(currentPressure, 1);
      display.setTextSize(1);
      display.setCursor(35, 48);
      display.print("hPa");
      break;
      
    case 2:
      display.print("HUMIDITY");
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(3);
      display.setCursor(15, 25);
      display.print(currentHumidity, 1);
      display.setTextSize(2);
      display.setCursor(95, 30);
      display.print("%");
      break;
      
    case 3:
      display.print("ALTITUDE");
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(2);
      display.setCursor(5, 25);
      display.print(currentAltitude, 1);
      display.setTextSize(1);
      display.setCursor(35, 48);
      display.print("meters");
      break;
      
    case 4:
      display.print("LIGHT%");
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(3);
      display.setCursor(15, 25);
      display.print(currentLight, 1);
      display.setTextSize(2);
      display.setCursor(95, 30);
      display.print("%");
      break;
  }
  
  display.display();
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket Connected!");
      break;
    case WStype_TEXT:
      Serial.printf("Server reply: %s\n", payload);
      break;
    case WStype_ERROR:
      Serial.println("WebSocket Error");
      break;
  }
}