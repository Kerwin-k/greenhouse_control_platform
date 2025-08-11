# 导入我们新的服务器主类
from app.main.routes import FlaskServer

if __name__ == '__main__':
    # 实例化并运行服务器
    server = FlaskServer()
    server.run(host='0.0.0.0', port=5000)