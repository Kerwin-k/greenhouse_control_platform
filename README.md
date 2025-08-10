[查看中文版 (View Chinese Version)](README_zh-CN.md)

---
# A Scalable IoT Smart Greenhouse Cluster Management Platform


---

## 📖 Introduction

This project aims to solve the challenge of precisely controlling the growing environment for high-value plants in urban agriculture and precision horticulture. We have designed and implemented a fully-featured, architecturally advanced Internet of Things (IoT) platform capable of centrally monitoring and managing multiple smart greenhouses.

The system adopts a modern "Centralized Platform with Modular Nodes" IoT architecture, utilizing the **Wokwi** online environment for high-fidelity simulation of **ESP32**-based smart greenhouse nodes. The backend server is built with the **Python Flask** framework, enabling efficient, low-latency, two-way communication with device nodes via the **MQTT** protocol. The frontend leverages **Flask-SocketIO** to create a dynamic web dashboard that displays data and responds to controls in real-time without requiring page refreshes.

## ✨ Features

* **Real-Time Environmental Monitoring:** Displays real-time temperature, humidity, and door status for all greenhouse nodes on the web dashboard.
* **Dynamic & Scalable Architecture:** The platform can automatically discover and accommodate new greenhouse nodes without any backend code modifications.
* **Intelligent Control Modes:**
    * **Automatic Mode:** The backend automation engine automatically controls fans and sprinklers based on preset rules (e.g., high temperature/low humidity).
    * **Manual Mode:** Users can take over at any time to manually control all devices via switches on the webpage.
* **Global Control Panel:** A global panel automatically appears when multiple greenhouses are online, allowing one-click control to set all greenhouses to a specific mode or turn all lights on/off.
* **Weather API Integration:** Integrates with the OpenWeatherMap API to provide intelligent operational suggestions based on real-world local weather.
* **Visual State Synchronization:** The state of all devices (lights, fans, sprinklers) is synchronized in real-time between the web UI and the physical state in the simulator.
* **Dynamic Update Countdown:** Each greenhouse card displays a countdown to the next data update. A "Data Delayed" warning is shown if data is not received within the expected time.

## 🏗️ System Architecture

This project follows a classic layered IoT architecture:

1.  **Device Layer:** Consists of ESP32-based smart greenhouse nodes simulated in Wokwi, responsible for collecting sensor data and executing control commands.
2.  **Communication Layer:** Uses a public MQTT Broker (`broker-cn.emqx.io`) as a message intermediary to decouple devices from the backend service.
3.  **Application Layer:** A backend server built with Python Flask and SocketIO, responsible for handling business logic, running the automation engine, and enabling real-time communication with the frontend.
4.  **Presentation Layer:** A dynamic HTML/CSS/JavaScript webpage that users access through their browsers.

*[Image: System Architecture Diagram]*

## 🛠️ Technology Stack

* **Backend:** Python, Flask, Flask-SocketIO, Paho-MQTT, Requests
* **Frontend:** HTML5, CSS3, JavaScript, Socket.IO Client
* **Device/Firmware:** C++ (Arduino Framework), Wokwi (Simulator)
* **Firmware Libraries:** `PubSubClient`, `ArduinoJson`, `DHT sensor library`, `ESP32Servo`
* **Protocols:** MQTT, WebSocket
* **IDE:** PyCharm, Wokwi

## 📁 Project Structure
```
Greenhouse_Control_Platform/
├── app/
│   ├── init.py         # Application Factory
│   ├── main/               # Main Blueprint
│   │   ├── init.py
│   │   ├── events.py       # SocketIO Event Handlers
│   │   └── routes.py       # Web Routes
│   ├── services/           # Core Services
│   │   ├── init.py
│   │   ├── mqtt_client.py  # MQTT Client & Automation Engine
│   │   └── weather_service.py # Weather API Service
│   ├── static/             # Static Files
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/          # HTML Templates
│       └── index.html
│
├── wokwi_esp32_firmware/   # Firmware Code
│   └── greenhouse_node_gh1/
│       ├── diagram.json    # Wokwi Hardware Layout
│       ├── platformio.ini  # PlatformIO Configuration
│       └── src/
│           └── main.cpp    # Main Firmware Program
│
├── config.py             # Configuration File
├── requirements.txt      # Python Dependency List
└── run.py                # Project Start Script
```

## 🚀 Getting Started

Follow these steps to run the project locally.

### **1. Prerequisites**

* Install [Python 3.8+](https://www.python.org/downloads/)
* Install [PyCharm](https://www.jetbrains.com/pycharm/download/) or another Python IDE
* A valid [OpenWeatherMap API Key](https://openweathermap.org/api)

### **2. Backend Server Setup**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/Greenhouse_Control_Platform.git](https://github.com/your-username/Greenhouse_Control_Platform.git)
    cd Greenhouse_Control_Platform
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS / Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure the API Key:**
    * Open the file `app/services/weather_service.py`.
    * Replace the placeholder in `API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"` with your own valid API key.
5.  **Run the server:**
    ```bash
    python run.py
    ```
    The server should now be running at `http://127.0.0.1:5000`.

### **3. Device Simulation Setup**

1.  **Open Wokwi:** Visit [wokwi.com](https://wokwi.com/).
2.  **Create a new project:** Select `ESP32` as the board.
3.  **Copy the code:**
    * Paste the **entire** C++ code from `wokwi_esp32_firmware/greenhouse_node_gh1/src/main.cpp` into the Wokwi editor's `sketch.cpp` tab.
4.  **Add library dependencies:**
    * Switch to the `libraries.txt` tab and ensure it contains the following:
        ```
        PubSubClient
        DHT sensor library
        ESP32Servo
        ArduinoJson
        ```
5.  **(Optional) Load hardware layout:**
    * Paste the content of `wokwi_esp32_firmware/greenhouse_node_gh1/diagram.json` into Wokwi's `diagram.json` tab to quickly load all components and wiring.

## 🕹️ Usage

1.  **Start the backend:** Make sure your PyCharm server is running.
2.  **Start the device:** In Wokwi, click the green "▶" (Start Simulation) button. You should see `Published data...` logs in the Wokwi serial monitor.
3.  **Access the webpage:** Open your browser and navigate to `http://127.0.0.1:5000`.
4.  **Observe and Control:**
    * Greenhouse cards will appear automatically and start updating data and countdowns in real-time.
    * You can switch between "Automatic" and "Manual" modes and control individual devices.
5.  **Test Scalability:**
    * In Wokwi, create a copy of your project. In the copy, only change the `GREENHOUSE_ID` in `main.cpp` to `"gh2"`.
    * **Run both Wokwi simulations simultaneously.**
    * Refresh the webpage. You will see two greenhouse cards and the global control panel at the top.

## 👥 Contributors

* Liu Kun
* Liu YanLin
* Ma Sheng

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).