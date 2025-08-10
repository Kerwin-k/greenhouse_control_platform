document.addEventListener('DOMContentLoaded', function () {
    // 用于管理所有温室的状态，包括数据、模式和倒计时
    let greenhouseState = {};
    const socket = io();

    // 获取dom元素
    const container = document.getElementById('greenhouse-container');
    const loader = document.getElementById('loading-indicator');
    const globalControls = document.getElementById('global-controls');
    const refreshWeatherBtn = document.getElementById('refresh-weather-btn');
    const weatherResultP = document.getElementById('weather-result');
    // 页面加载时的初始倒计时
    function startInitialCountdown() {
        let count = 10;
        const initialCountdownSpan = document.getElementById('initial-countdown');
        if (initialCountdownSpan) {
            initialCountdownSpan.innerText = count;
            initialTimerId = setInterval(function() {
                count--;
                if (count >= 0 && initialCountdownSpan) {
                    initialCountdownSpan.innerText = count;
                } else {
                    clearInterval(initialTimerId);
                }
            }, 1000);
        }
    }
    startInitialCountdown();

    // 监听与服务器的连接事件
    socket.on('connect', function() {
        console.log('Socket.IO 客户端已成功连接到服务器！');
    });

    // 监听来自服务器的完整数据更新
   socket.on('update_data', function (greenhouses) {
        if (loader && loader.style.display !== 'none') {
            loader.style.display = 'none';
        }

       for (const gh_id in greenhouses) {
            if (greenhouses.hasOwnProperty(gh_id)) {
                if (!greenhouseState[gh_id]) greenhouseState[gh_id] = {};
                Object.assign(greenhouseState[gh_id], greenhouses[gh_id]);
                if (!greenhouseState[gh_id].mode) greenhouseState[gh_id].mode = 'manual';
                if (greenhouseState[gh_id].interval) {
                    greenhouseState[gh_id].countdown = greenhouseState[gh_id].interval / 1000;
                }
                renderOrUpdateCard(gh_id);
            }
        }
        updateGlobalControlsVisibility();
    });

    // 监听来自服务器的模式更新
    socket.on('mode_updated', function(modes) {
        for (const gh_id in modes) {
            if (greenhouseState[gh_id]) {
                greenhouseState[gh_id].mode = modes[gh_id];
                renderOrUpdateCard(gh_id);
            }
        }
    });

    // 监听后端发回的天气联动结果
    socket.on('global_weather_result', function(data) {
        if (weatherResultP) {
            weatherResultP.innerText = data.message;
        }
    });

    // 渲染或更新单个卡片的函数
  function renderOrUpdateCard(gh_id) {
        const data = greenhouseState[gh_id];
        if (!data) return;

        let card = document.getElementById('card_' + gh_id);

        if (!card) {
            card = document.createElement('div');
            card.className = 'greenhouse-card';
            card.id = 'card_' + gh_id;
            card.innerHTML = `
                <h2>温室ID: ${gh_id}</h2>
                <div class="mode-control">
                    <span>模式: <span id="${gh_id}_mode_text">手动</span></span>
                    <label class="switch">
                        <input type="checkbox" class="mode-switch" data-ghid="${gh_id}">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="controls">
                    <span>补光灯:</span>
                    <label class="switch">
                        <input type="checkbox" class="control-switch" data-ghid="${gh_id}" data-device="light">
                        <span class="slider"></span>
                    </label>
                </div>
                <hr>
                <p><strong>温度:</strong> <span class="data-value" id="${gh_id}_temperature">N/A</span> °C</p>
                <p><strong>湿度:</strong> <span class="data-value" id="${gh_id}_humidity">N/A</span> %</p>
                <p><strong>门状态:</strong> <span class="data-value" id="${gh_id}_door">N/A</span></p>
                <p class="countdown">下次更新倒计时: <span class="timer" id="${gh_id}_timer">--</span> 秒</p>
                <hr>
                <div class="manual-controls">
                    <h4>手动控制</h4>
                    <div class="controls">
                        <span>风扇:</span>
                        <label class="switch">
                            <input type="checkbox" class="control-switch" data-ghid="${gh_id}" data-device="fan">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="controls">
                        <span>花洒:</span>
                        <label class="switch">
                            <input type="checkbox" class="control-switch" data-ghid="${gh_id}" data-device="sprinkler">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
            `;
            if (container) container.appendChild(card);
        }

        const isAutoMode = data.mode === 'auto';
        document.getElementById(`${gh_id}_temperature`).innerText = data.temperature !== undefined ? data.temperature.toFixed(2) : 'N/A';
        document.getElementById(`${gh_id}_humidity`).innerText = data.humidity !== undefined ? data.humidity.toFixed(2) : 'N/A';
        const doorSpan = document.getElementById(`${gh_id}_door`);
        doorSpan.innerText = data.door || 'N/A';
        doorSpan.className = `data-value ${data.door === 'OPEN' ? 'status-open' : ''}`;

        document.querySelector(`#card_${gh_id} .mode-switch`).checked = isAutoMode;
        document.querySelector(`#card_${gh_id} #${gh_id}_mode_text`).innerText = isAutoMode ? '自动' : '手动';
        document.querySelector(`#card_${gh_id} .manual-controls`).className = `manual-controls ${isAutoMode ? 'disabled' : ''}`;

        document.querySelector(`#card_${gh_id} .control-switch[data-device="light"]`).checked = (data.light_state === 'ON');
        document.querySelector(`#card_${gh_id} .control-switch[data-device="fan"]`).checked = (data.fan_state === 'ON');
        document.querySelector(`#card_${gh_id} .control-switch[data-device="sprinkler"]`).checked = (data.sprinkler_state === 'ON');
    }

    // 全局倒计时器
    setInterval(function() {
        for (const gh_id in greenhouseState) {
            const state = greenhouseState[gh_id];
            if (state.countdown > 0) state.countdown--;

            const timerSpan = document.getElementById(gh_id + '_timer');
            if (timerSpan) {
                if (state.countdown > 0) {
                    timerSpan.innerText = state.countdown;
                    timerSpan.className = 'timer';
                } else {
                    timerSpan.innerText = '数据延迟...';
                    timerSpan.className = 'timer timer-delayed';
                }
            }
        }
    }, 1000);

    // 主事件监听器（事件委托）
    if (container) {
        container.addEventListener('change', function(event) {
            const target = event.target;
            const gh_id = target.dataset.ghid;
            if (!gh_id) return;

            if (target.matches('.mode-switch')) {
                const newMode = target.checked ? 'auto' : 'manual';
                socket.emit('mode_change_event', { gh_id: gh_id, mode: newMode });
            }

            if (target.matches('.control-switch')) {
                const device = target.dataset.device;
                const command = target.checked ? 'ON' : 'OFF';
                socket.emit('control_event', { gh_id: gh_id, device: device, command: command });
            }
        });

        container.addEventListener('click', function(event) {
            const target = event.target;
            if (target.matches('.action-btn')) {
                const gh_id = target.dataset.ghid;
                console.log(`请求 ${gh_id} 的天气联动...`);
                socket.emit('weather_action_event', { gh_id: gh_id });
            }
        });
    }

    // 全局控制事件监听
    if (globalControls) {
        globalControls.addEventListener('click', function(event) {
            const target = event.target;
            if (target.matches('.global-btn')) {
                const action = target.dataset.action;
                const value = target.dataset.value;

                if (action === 'mode') {
                    socket.emit('global_mode_change_event', { mode: value });
                } else if (action === 'light') {
                    socket.emit('global_control_event', { device: 'light', command: value });
                }
            }
             if (target.matches('#refresh-weather-btn')) {
                weatherResultP.innerText = '正在获取天气数据...';
                socket.emit('request_global_weather');
            }
        });
    }

    // 更新全局控制面板的可见性
    function updateGlobalControlsVisibility() {
        if (globalControls) {
            const greenhouseCount = Object.keys(greenhouseState).length;
            globalControls.style.display = greenhouseCount > 1 ? 'block' : 'none';
        }
    }
});