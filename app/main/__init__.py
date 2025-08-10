from flask import Blueprint

main = Blueprint('main', __name__)

# 导入路由和事件处理，确保它们能被注册
from . import routes, events