from flask import Flask
from flask_socketio import SocketIO
from config import Config
from .services.mqtt_client import MQTTClient

# 先创建扩展实例，但不绑定app
socketio = SocketIO()
mqtt_client = MQTTClient()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 使用init_app方法，将扩展与app实例绑定
    # 这可以避免循环导入问题，并且是更标准的做法
    socketio.init_app(app)
    mqtt_client.init_app(app, socketio)

    mqtt_client.connect()

    # 注册蓝图
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app