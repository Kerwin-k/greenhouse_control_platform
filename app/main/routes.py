import json
import threading
import time
from pathlib import Path

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt

from ..services import weather_service
from ..services.SQLiteManager import SQLiteManager

# --- 全局状态字典 ---
greenhouses_data = {}
greenhouse_modes = {}

# --- MQTT 设置 ---
MQTT_BROKER = "broker-cn.emqx.io"
MQTT_PORT = 8083


class FlaskServer:
    def __init__(self):
        # 初始化Flask应用
        project_root = Path(__file__).resolve().parent.parent
        template_folder = str(project_root / 'templates')
        static_folder = str(project_root / 'static')

        self.app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
        self.app.secret_key = 'a-very-secret-key-for-sessions'

        # 初始化SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # 初始化数据库
        self.db = self.initialize_database()

        # 初始化MQTT客户端
        self.mqtt_client = self.initialize_mqtt()

        # 注册所有路由和事件
        self.setup_routes_and_events()

        # 启动后台自动化任务
        self.start_auto_mode_checker()

    def initialize_database(self):
        db = SQLiteManager("greenhouse_main.db")
        # 创建用户表
        db.create_table("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)
        # 创建传感器历史数据表
        db.create_table("""
            CREATE TABLE IF NOT EXISTS sensor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gh_id TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                timestamp TEXT DEFAULT (datetime('now', 'localtime'))
            );
        """)
        # 检查并创建默认用户
        if not db.select_one("users", "username = ?", ["root"]):
            db.insert("users", {"username": "root", "password": "123456"})
        return db

    def initialize_mqtt(self):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
        client.on_connect = self.on_mqtt_connect
        client.on_message = self.on_mqtt_message
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print(f"MQTT Connection Error: {e}")
        return client

    def on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"Successfully connected to MQTT Broker ({MQTT_BROKER})!")
            client.subscribe("ucsi/mdt1001/greenhouse/+/telemetry/#")
        else:
            print(f"MQTT Connection failed with code: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            gh_id = msg.topic.split('/')[3]
            payload = json.loads(msg.payload.decode())

            if gh_id not in greenhouses_data:
                greenhouses_data[gh_id] = {}
            greenhouses_data[gh_id].update(payload)

            # 如果消息包含温湿度，则存入历史数据库
            if 'temperature' in payload and 'humidity' in payload:
                self.db.insert("sensor_history", {
                    "gh_id": gh_id,
                    "temperature": payload['temperature'],
                    "humidity": payload['humidity']
                })

            # 通过SocketIO将最新数据推送到前端
            self.socketio.emit('update_data', greenhouses_data)
        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    def setup_routes_and_events(self):
        # --- HTTP 路由 ---
        self.app.add_url_rule('/', 'root', self.root)
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET'])
        self.app.add_url_rule('/realLogin', 'real_login', self.real_login, methods=['POST'])
        self.app.add_url_rule('/home', 'home', self.home)
        self.app.add_url_rule('/status', 'status', self.status)
        self.app.add_url_rule('/stats', 'stats', self.stats)
        self.app.add_url_rule('/logout', 'logout', self.logout)

        # --- SocketIO 事件 ---
        self.socketio.on_event('connect', self.handle_connect)
        self.socketio.on_event('control_event', self.handle_control_event)
        self.socketio.on_event('mode_change_event', self.handle_mode_change)
        self.socketio.on_event('global_control_event', self.handle_global_control)
        self.socketio.on_event('global_mode_change_event', self.handle_global_mode_change)
        self.socketio.on_event('request_global_weather', self.handle_weather_action)

    def run(self, host, port):
        # 在后台线程中运行MQTT客户端
        threading.Thread(target=self.mqtt_client.loop_forever, daemon=True).start()
        # 运行Web服务器
        self.socketio.run(self.app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True, use_reloader=False)

    # --- 路由函数实现 ---
    def root(self):
        return redirect(url_for('login'))

    def login(self):
        return render_template('login.html')

    def real_login(self):
        data = request.get_json()
        user = self.db.select_one("users", "username = ? AND password = ?",
                                  [data.get("username"), data.get("password")])
        if user:
            session['username'] = user[1]
            return jsonify(success=True, message="Login successful")
        return jsonify(success=False, message="Invalid credentials"), 401

    def home(self):
        if 'username' not in session:
            return redirect(url_for('login'))
        return render_template('home.html', username=session['username'])

    def status(self):
        if 'username' not in session:
            return redirect(url_for('login'))
        return render_template('status.html', greenhouses_data=greenhouses_data)

    def stats(self):
        if 'username' not in session:
            return redirect(url_for('login'))

        rows = self.db.select("sensor_history")
        data = {}
        for row in rows:
            gh_id, temp, hum, time_str = row[1], row[2], row[3], row[4]
            if gh_id not in data:
                data[gh_id] = {'temperature': [], 'humidity': [], 'time': []}
            data[gh_id]['temperature'].append(temp)
            data[gh_id]['humidity'].append(hum)
            data[gh_id]['time'].append(time_str.split(" ")[1])  # 只取时间部分
        return render_template('stats.html', data=data)

    def logout(self):
        session.pop('username', None)
        return redirect(url_for('login'))

    # --- SocketIO 事件函数实现 ---
    def handle_connect(self):
        print('A client has connected via SocketIO!')
        self.socketio.emit('mode_updated', greenhouse_modes)

    def handle_control_event(self, data):
        gh_id, device, command = data.get('gh_id'), data.get('device'), data.get('command')
        if all([gh_id, device, command]):
            topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/{device}"
            self.mqtt_client.publish(topic, json.dumps({"command": command}))

    def handle_mode_change(self, data):
        gh_id, mode = data.get('gh_id'), data.get('mode')
        if gh_id and mode:
            greenhouse_modes[gh_id] = mode
            self.socketio.emit('mode_updated', greenhouse_modes)

    def handle_global_control(self, data):
        device, command = data.get('device'), data.get('command')
        if all([device, command]):
            for gh_id in greenhouses_data.keys():
                topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/{device}"
                self.mqtt_client.publish(topic, json.dumps({"command": command}))

    def handle_global_mode_change(self, data):
        mode = data.get('mode')
        if mode:
            for gh_id in greenhouses_data.keys():
                greenhouse_modes[gh_id] = mode
            self.socketio.emit('mode_updated', greenhouse_modes)

    def handle_weather_action(self):
        weather = weather_service.get_current_weather()
        if weather:
            message = f"Current Weather: {weather['condition']}, Temp: {weather['temperature']}°C. "
            if weather['condition'] == 'Rain':
                message += "Suggestion: Keep ventilation closed."
            elif weather['temperature'] > 30:
                message += "Suggestion: Enable strong ventilation."
            else:
                message += "Conditions are good."
            self.socketio.emit('global_weather_result', {'message': message})
        else:
            self.socketio.emit('global_weather_result', {'message': 'Failed to get weather data.'})

    # --- 后台自动化任务 ---
    def check_auto_mode_task(self):
        while True:
            with self.app.app_context():
                for gh_id, mode in list(greenhouse_modes.items()):
                    if mode == 'auto' and gh_id in greenhouses_data:
                        data = greenhouses_data[gh_id]
                        temp, humidity = data.get('temperature'), data.get('humidity')
                        if temp is not None:
                            fan_command = "ON" if temp > 28.0 else "OFF"
                            self.mqtt_client.publish(f"ucsi/mdt1001/greenhouse/{gh_id}/control/fan",
                                                     json.dumps({"command": fan_command}))
                        if humidity is not None:
                            sprinkler_command = "ON" if humidity < 40.0 else "OFF"
                            self.mqtt_client.publish(f"ucsi/mdt1001/greenhouse/{gh_id}/control/sprinkler",
                                                     json.dumps({"command": sprinkler_command}))
            time.sleep(5)

    def start_auto_mode_checker(self):
        threading.Thread(target=self.check_auto_mode_task, daemon=True).start()