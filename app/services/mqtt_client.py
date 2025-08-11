import time

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
    def __init__(self):
        self.callback = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
        self.connected = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"成功连接到MQTT Broker ({MQTT_BROKER})!")
            client.subscribe(MQTT_TOPIC_SUBSCRIBE)
            self.connected = True
            print(f"已订阅主题: {MQTT_TOPIC_SUBSCRIBE}")
        else:
            print(f"连接失败，返回码: {rc}")
            self.connected = False

    def on_disconnect(self, client):
        self.connected = False

    def on_message(self, client, userdata, msg):
        gh_id = msg.topic.split('/')[3]
        payload = json.loads(msg.payload.decode())
        self.callback(gh_id, payload)

    def conn(self, callback):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.callback = callback
        self.client.connect(MQTT_BROKER, MQTT_PORT, 120)
        self.start_auto_mode_checker()
        # self.client.loop_start()

    def connect(self):
        threading.Thread(target=self.conn, daemon=True).start()

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def check_auto_mode(self):
        while True:
            print("后台任务：正在检查自动模式...")
            if self.connected:
                for gh_id, mode in list(greenhouse_modes.items()):
                    if mode == 'auto' and gh_id in greenhouses_data:
                        data = greenhouses_data[gh_id]
                        temp = data.get('temperature')
                        humidity = data.get('humidity')

                        if temp is not None:
                            # 自动化规则1: 风扇控制
                            fan_command = "ON" if temp > 28.0 else "OFF"
                            fan_topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/fan"
                            self.publish(fan_topic, json.dumps({"command": fan_command}))
                        if humidity is not None:
                            # 自动化规则2: 花洒控制
                            sprinkler_command = "ON" if humidity < 40.0 else "OFF"
                            sprinkler_topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/sprinkler"
                            self.publish(sprinkler_topic, json.dumps({"command": sprinkler_command}))
            time.sleep(3)

    def start_auto_mode_checker(self):
        print("启动自动化模式检查后台任务...")
        threading.Thread(target=self.check_auto_mode, daemon=True).start()
        # threading.Timer(5, self.check_auto_mode).start()