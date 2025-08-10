from flask import render_template
from . import main

@main.route('/')
def index():
    # 暂时传入一个空字典，后续会替换成真实的温室数据
    greenhouses_data = {}
    return render_template('index.html', greenhouses_data=greenhouses_data)