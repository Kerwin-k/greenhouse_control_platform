import paho.mqtt.client as mqtt
import json
import threading
from flask import current_app

# --- 全局状态字典 ---
greenhouses_data = {}
greenhouse_modes = {}  # e.g., {"gh1": "auto", "gh2": "manual"}

# --- MQTT 设置 ---
MQTT_BROKER = "broker-cn.emqx.io"
MQTT_PORT = 8083
MQTT_TOPIC_SUBSCRIBE = "ucsi/mdt1001/greenhouse/+/telemetry/#"


class MQTTClient:
    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def init_app(self, app, socketio):
        """延迟初始化，以避免循环导入"""
        self.app = app
        self.socketio = socketio

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"成功连接到MQTT Broker ({MQTT_BROKER})!")
            client.subscribe(MQTT_TOPIC_SUBSCRIBE)
            print(f"已订阅主题: {MQTT_TOPIC_SUBSCRIBE}")
        else:
            print(f"连接失败，返回码: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            gh_id = msg.topic.split('/')[3]
            payload = json.loads(msg.payload.decode())

            if gh_id not in greenhouses_data:
                greenhouses_data[gh_id] = {}

            greenhouses_data[gh_id].update(payload)

            if self.socketio:
                self.socketio.emit('update_data', greenhouses_data)

        except (IndexError, json.JSONDecodeError, KeyError) as e:
            print(f"处理消息时出错: {e}, 消息: {msg.payload.decode()}")

    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            self.start_auto_mode_checker()  # 启动后台自动化任务
        except Exception as e:
            print(f"无法连接到MQTT Broker: {e}")

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def check_auto_mode(self):
        # 使用self.app.app_context()确保在后台线程中可以访问Flask的上下文
        with self.app.app_context():
            print("后台任务：正在检查自动模式...")
            for gh_id, mode in list(greenhouse_modes.items()):
                if mode == 'auto' and gh_id in greenhouses_data:
                    data = greenhouses_data[gh_id]
                    temp = data.get('temperature')
                    humidity = data.get('humidity')

                    if temp is not None and humidity is not None:
                        # 自动化规则1: 风扇控制
                        fan_command = "ON" if temp > 28.0 else "OFF"
                        fan_topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/fan"
                        self.publish(fan_topic, json.dumps({"command": fan_command}))

                        # 自动化规则2: 花洒控制
                        sprinkler_command = "ON" if humidity < 40.0 else "OFF"
                        sprinkler_topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/sprinkler"
                        self.publish(sprinkler_topic, json.dumps({"command": sprinkler_command}))

        # 递归调用，设置5秒后再次检查
        threading.Timer(5, self.check_auto_mode).start()

    def start_auto_mode_checker(self):
        print("启动自动化模式检查后台任务...")
        threading.Timer(5, self.check_auto_mode).start()