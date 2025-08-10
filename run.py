from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # 使用socketio.run来启动，以便支持WebSocket
    # 添加 allow_unsafe_werkzeug=True 参数以在开发环境中运行
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)