# 可扩展的物联网智能温室集群管控平台
### A Scalable IoT Smart Greenhouse Cluster Management Platform

---

## 📖 项目简介 (Introduction)

本项目旨在解决城市农业和精准园艺中，对高价值植物生长环境进行精确控制的挑战。我们设计并实现了一个功能完备、架构先进的物联网（IoT）平台，能够对多个智能温室进行集中监控和管理。

系统采用“中心化平台与模块化节点”的现代物联网架构，通过 **Wokwi** 在线环境对基于 **ESP32** 的智能温室节点进行高保真模拟。后端服务器采用 **Python Flask** 框架构建，通过 **MQTT** 协议与设备节点进行高效、低延迟的双向通信；前端则利用 **Flask-SocketIO** 技术，构建了一个无需刷新、能够实时显示数据和响应控制的动态Web仪表盘。

## ✨ 主要功能 (Features)

* **实时环境监控:** 在Web仪表盘上实时显示所有温室节点的温度、湿度和门窗状态。
* **动态可扩展架构:** 无需修改任何后端代码，平台能够自动发现并接纳新增的温室节点。
* **智能控制模式:**
    * **自动模式:** 后端自动化引擎根据预设规则（如温度过高/湿度过低），自动控制风扇和花洒。
    * **手动模式:** 用户可以随时接管，通过网页上的开关手动控制所有设备。
* **全局控制面板:** 当系统中存在多个温室时，自动出现全局面板，可一键切换所有温室的模式或开关所有灯光。
* **天气API联动:** 集成OpenWeatherMap API，可根据用户所在地的真实天气，为农业操作提供智能决策建议。
* **可视化状态同步:** 所有设备（灯、风扇、花洒）的开关状态都能在网页上与模拟器中的物理状态实时同步。
* **动态更新倒计时:** 每个温室卡片都会显示下一次数据更新的倒计时，如果数据超时未上报，则会显示“数据延迟”警告。

## 🏗️ 系统架构 (System Architecture)

本项目采用经典的物联网分层架构：

1.  **设备层 (Device Layer):** 由Wokwi模拟的ESP32智能温室节点组成，负责采集传感器数据和执行控制指令。
2.  **通信层 (Communication Layer):** 使用公共MQTT Broker (`broker-cn.emqx.io`)作为消息中介，解耦设备与后端服务。
3.  **应用层 (Application Layer):** 基于Python Flask和SocketIO构建的后端服务器，负责处理业务逻辑、运行自动化引擎和与前端实时通信。
4.  **表现层 (Presentation Layer):** 用户通过浏览器访问的HTML/CSS/JavaScript动态网页。

*[图：系统架构图]*

## 🛠️ 技术栈 (Technology Stack)

* **后端 (Backend):** Python, Flask, Flask-SocketIO, Paho-MQTT, Requests
* **前端 (Frontend):** HTML5, CSS3, JavaScript, Socket.IO Client
* **设备端/固件 (Device/Firmware):** C++ (Arduino Framework), Wokwi (Simulator)
* **依赖库 (Firmware Libraries):** `PubSubClient`, `ArduinoJson`, `DHT sensor library`, `ESP32Servo`
* **通信协议 (Protocol):** MQTT, WebSocket
* **开发环境 (IDE):** PyCharm, Wokwi

## 📁 项目结构 (Project Structure)
```
Greenhouse_Control_Platform/
├── app/
│   ├── init.py         # 应用工厂
│   ├── main/               # 主蓝图
│   │   ├── init.py
│   │   ├── events.py       # SocketIO事件处理器
│   │   └── routes.py       # 网页路由
│   ├── services/           # 核心服务
│   │   ├── init.py
│   │   ├── mqtt_client.py  # MQTT客户端与自动化引擎
│   │   └── weather_service.py # 天气API服务
│   ├── static/             # 静态文件
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/          # HTML模板
│       └── index.html
│
├── wokwi_esp32_firmware/   # 固件代码
│   └── greenhouse_node_gh1/
│       ├── diagram.json    # Wokwi硬件布局
│       ├── platformio.ini  # PlatformIO配置
│       └── src/
│           └── main.cpp    # 固件主程序
│
├── config.py             # 配置文件
├── requirements.txt      # Python依赖清单
└── run.py                # 项目启动脚本
```
## 🚀 快速开始 (Getting Started)

请按照以下步骤在本地运行此项目。

### **1. 环境准备**

* 安装 [Python 3.8+](https://www.python.org/downloads/)
* 安装 [PyCharm](https://www.jetbrains.com/pycharm/download/) 或其他Python IDE
* 一个有效的 [OpenWeatherMap API Key](https://openweathermap.org/api)

### **2. 后端服务器设置**

1.  **克隆仓库:**
    ```bash
    git clone [https://github.com/your-username/Greenhouse_Control_Platform.git](https://github.com/your-username/Greenhouse_Control_Platform.git)
    cd Greenhouse_Control_Platform
    ```
2.  **创建并激活虚拟环境:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS / Linux
    source venv/bin/activate
    ```
3.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **配置API Key:**
    * 打开 `app/services/weather_service.py` 文件。
    * 将 `API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"` 中的占位符替换为您自己的有效API密钥。
5.  **运行服务器:**
    ```bash
    python run.py
    ```
    服务器现在应该已在 `http://127.0.0.1:5000` 上运行。

### **3. 设备端模拟设置**

1.  **打开Wokwi:** 访问 [wokwi.com](https://wokwi.com/)。
2.  **创建新项目:** 选择 `ESP32` 作为开发板。
3.  **复制代码:**
    * 将 `wokwi_esp32_firmware/greenhouse_node_gh1/src/main.cpp` 文件中的**全部**C++代码，粘贴到Wokwi编辑器的`sketch.cpp`中。
4.  **添加依赖库:**
    * 切换到 `libraries.txt` 标签页，并确保其中包含以下内容：
        ```
        PubSubClient
        DHT sensor library
        ESP32Servo
        ArduinoJson
        ```
5.  **（可选）加载硬件布局:**
    * 将 `wokwi_esp32_firmware/greenhouse_node_gh1/diagram.json` 的内容粘贴到Wokwi的`diagram.json`标签页，可以快速加载所有硬件并自动连线。

## 🕹️ 如何使用 (Usage)

1.  **启动后端:** 确保您的PyCharm服务器正在运行。
2.  **启动设备:** 在Wokwi中，点击绿色的“▶”(Start Simulation)按钮。您应该能在Wokwi的串口监视器中看到`Published data...`的日志。
3.  **访问网页:** 打开您的浏览器，访问 `http://127.0.0.1:5000`。
4.  **观察与控制:**
    * 网页上会自动出现温室卡片，并开始实时更新数据和倒计时。
    * 您可以切换“自动/手动”模式，并控制各个设备。
5.  **测试可扩展性:**
    * 在Wokwi中复制您的项目，只修改`main.cpp`中的`GREENHOUSE_ID`为`"gh2"`。
    * **同时运行两个Wokwi模拟**。
    * 刷新网页，您会看到两个温室卡片和顶部的全局控制面板。

## 👥 贡献者 (Contributors)

* 刘坤（Liu Kun)
* 刘炎麟（Liu YanLin）
* 马升（Ma Sheng）

## 📄 许可证 (License)

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。