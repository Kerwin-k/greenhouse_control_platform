import requests

# --- 配置 ---
# 替换为自己的Key
API_KEY = "96e1b6c6ec74d11799effbd674bbf10e"
CITY = "Kuala Lumpur, MY"  # 您所在的城市

# OpenWeatherMap API的URL
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_current_weather():
    """
    调用OpenWeatherMap API获取指定城市的当前天气。
    返回一个包含天气状况和温度的字典，或者在失败时返回None。
    """
    params = {
        'q': CITY,
        'appid': API_KEY,
        'units': 'metric'  # 使用'metric'单位，温度会以摄氏度返回
    }

    print(f"正在向OpenWeatherMap请求'{CITY}'的天气...")

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()  # 如果请求失败(如401, 404), 会抛出异常

        data = response.json()

        # 从返回的复杂JSON中提取我们需要的信息
        condition = data.get('weather', [{}])[0].get('main', 'Unknown')  # e.g., "Rain", "Clouds"
        temp_celsius = data.get('main', {}).get('temp', 'N/A')

        print(f"成功获取天气: 状况={condition}, 温度={temp_celsius}°C")

        return {
            "condition": condition,
            "temperature": temp_celsius
        }

    except requests.exceptions.RequestException as e:
        print(f"获取天气时发生网络错误: {e}")
        return None
    except Exception as e:
        print(f"处理天气数据时发生未知错误: {e}")
        return None


# --- 独立测试 ---
if __name__ == '__main__':
    weather = get_current_weather()
    if weather:
        print("\n测试成功！")
        print(f"当前城市: {CITY}")
        print(f"天气状况: {weather['condition']}")
        print(f"当前温度: {weather['temperature']}°C")
    else:
        print("\n测试失败。请检查您的API Key是否已激活或网络连接是否正常。")