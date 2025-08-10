from app import socketio, mqtt_client
from app.services.mqtt_client import greenhouse_modes, greenhouses_data
from app.services import weather_service
import json


@socketio.on('connect')
def handle_connect():
    """当有新的客户端连接时被调用"""
    print('一个客户端已连接到SocketIO！')
    # 当新客户端连接时，立即将当前模式状态发给它
    socketio.emit('mode_updated', greenhouse_modes)


@socketio.on('control_event')
def handle_control_event(data):
    """处理来自前端的单个设备控制事件"""
    gh_id = data.get('gh_id')
    device = data.get('device')
    command = data.get('command')
    if not all([gh_id, device, command]):
        return

    topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/{device}"
    payload = json.dumps({"command": command})
    mqtt_client.publish(topic, payload)


@socketio.on('mode_change_event')
def handle_mode_change(data):
    """处理来自前端的单个温室模式变更事件"""
    gh_id = data.get('gh_id')
    mode = data.get('mode')  # "auto" or "manual"
    if gh_id and mode:
        greenhouse_modes[gh_id] = mode
        print(f"温室 {gh_id} 模式已更改为: {mode}")
        # 广播模式变化，让所有前端同步
        socketio.emit('mode_updated', greenhouse_modes)


@socketio.on('global_control_event')
def handle_global_control(data):
    """处理来自前端的全局设备控制事件"""
    device = data.get('device')
    command = data.get('command')
    if not all([device, command]):
        return

    print(f"收到全局指令: 设备={device}, 命令={command}")
    for gh_id in greenhouses_data.keys():
        topic = f"ucsi/mdt1001/greenhouse/{gh_id}/control/{device}"
        payload = json.dumps({"command": command})
        mqtt_client.publish(topic, payload)


@socketio.on('global_mode_change_event')
def handle_global_mode_change(data):
    """处理来自前端的全局模式变更事件"""
    mode = data.get('mode')
    if not mode:
        return

    print(f"收到全局模式指令: 模式={mode}")
    for gh_id in greenhouses_data.keys():
        greenhouse_modes[gh_id] = mode
    socketio.emit('mode_updated', greenhouse_modes)


@socketio.on('request_global_weather')
def handle_weather_action():
    """处理来自前端的全局天气刷新请求"""
    print("收到来自网页的全局天气请求...")
    weather = weather_service.get_current_weather()

    if weather:
        if weather['condition'] == 'Rain':
            action_message = f"当前天气: 下雨 ({weather['condition']})，温度: {weather['temperature']}°C。建议：保持通风关闭，避免湿气进入。"
        elif weather['temperature'] > 30:
            action_message = f"当前天气: {weather['condition']}，温度: {weather['temperature']}°C。建议：天气炎热，可开启强力通风。"
        else:
            action_message = f"当前天气: {weather['condition']}，温度: {weather['temperature']}°C。状况良好。"

        # 将联动建议发送回前端，让用户看到
        socketio.emit('global_weather_result', {'message': action_message})
    else:
        socketio.emit('global_weather_result', {'message': '获取天气信息失败，请检查API Key或网络。'})