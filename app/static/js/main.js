document.addEventListener('DOMContentLoaded', function () {
    // 用于管理所有温室的状态，包括数据、模式和倒计时
    let greenhouseState = {};
    let initialTimerId = null;

    // 获取DOM元素
    const socket = io();
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
            clearInterval(initialTimerId);
            loader.style.display = 'none';
        }

        for (const gh_id in greenhouses) {
            if (greenhouses.hasOwnProperty(gh_id)) {
                if (!greenhouseState[gh_id]) greenhouseState[gh_id] = {};
                Object.assign(greenhouseState[gh_id], greenhouses[gh_id]);
                if (!greenhouseState[gh_id].mode) {
                    greenhouseState[gh_id].mode = 'manual';
                }
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

    // 监听后端发回的全局天气联动结果
    socket.on('global_weather_result', function(data) {
        if (weatherResultP) {
            weatherResultP.innerText = data.message;
        }
    });

    // --- 核心修正：新增监听单个温室的天气结果 ---
    socket.on('weather_action_result', function(data) {
        const gh_id = data.gh_id;
        const message = data.message;
        const resultP = document.getElementById(gh_id + '_action_result');
        if (resultP) {
            resultP.innerText = message;
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
                <h2>Greenhouse ID: ${gh_id}</h2>
                <div class="mode-control">
                    <span>Mode: <span id="${gh_id}_mode_text">Manual</span></span>
                    <label class="switch">
                        <input type="checkbox" class="mode-switch" data-ghid="${gh_id}">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="controls">
                    <span>Supplemental Light:</span>
                    <label class="switch">
                        <input type="checkbox" class="control-switch" data-ghid="${gh_id}" data-device="light">
                        <span class="slider"></span>
                    </label>
                </div>
                <hr>
                <p><strong>Temperature:</strong> <span class="data-value" id="${gh_id}_temperature">N/A</span> °C</p>
                <p><strong>Humidity:</strong> <span class="data-value" id="${gh_id}_humidity">N/A</span> %</p>
                <p><strong>Door Status:</strong> <span class="data-value" id="${gh_id}_door">N/A</span></p>
                <p class="countdown">Next Update Countdown: <span class="timer" id="${gh_id}_timer">--</span> s</p>
                <hr>
                <div class="manual-controls">
                    <h4>Manual Control</h4>
                    <div class="controls">
                        <span>Fan:</span>
                        <label class="switch">
                            <input type="checkbox" class="control-switch" data-ghid="${gh_id}" data-device="fan">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="controls">
                        <span>Sprinkler:</span>
                        <label class="switch">
                            <input type="checkbox" class="control-switch" data-ghid="${gh_id}" data-device="sprinkler">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
                <hr>
                <h4>Smart Actions</h4>
                <div class="controls">
                    <button class="action-btn" data-ghid="${gh_id}">Get Weather Suggestion</button>
                </div>
                <p class="action-result" id="${gh_id}_action_result"></p>
            `;
            if (container) container.appendChild(card);
        }

        // 无论创建还是更新，都执行“局部更新”
        updateCardUI(gh_id, data);

        // 收到新数据后，解锁该卡片的所有开关
        const allSwitches = document.querySelectorAll(`#card_${gh_id} .control-switch, #card_${gh_id} .mode-switch`);
        allSwitches.forEach(sw => sw.disabled = false);
    }

    function updateCardUI(gh_id, data) {
        const isAutoMode = data.mode === 'auto';
        document.getElementById(`${gh_id}_temperature`).innerText = data.temperature !== undefined ? data.temperature.toFixed(2) : 'N/A';
        document.getElementById(`${gh_id}_humidity`).innerText = data.humidity !== undefined ? data.humidity.toFixed(2) : 'N/A';
        const doorSpan = document.getElementById(`${gh_id}_door`);
        doorSpan.innerText = data.door || 'N/A';
        doorSpan.className = `data-value ${data.door === 'OPEN' ? 'status-open' : ''}`;

        document.querySelector(`#card_${gh_id} .mode-switch`).checked = isAutoMode;
        document.querySelector(`#card_${gh_id} #${gh_id}_mode_text`).innerText = isAutoMode ? 'Auto' : 'Manual';
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
                    timerSpan.innerText = 'Data Delayed...';
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

            // 临时禁用该卡片的所有开关，提供即时反馈
            if (target.matches('.control-switch') || target.matches('.mode-switch')) {
                const allSwitches = document.querySelectorAll(`#card_${gh_id} .control-switch, #card_${gh_id} .mode-switch`);
                allSwitches.forEach(sw => sw.disabled = true);
            }

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
                const resultP = document.getElementById(`${gh_id}_action_result`);
                if(resultP) resultP.innerText = 'Fetching weather data...';
                // --- 核心修正：确保发送正确的事件名 ---
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
                if(weatherResultP) weatherResultP.innerText = 'Fetching weather data...';
                socket.emit('request_global_weather');
            }
        });

        // --- 新增代码：在全局控制面板动态添加一个“查看统计”按钮 ---
        const globalButtonsDiv = globalControls.querySelector('.global-buttons');
        if (globalButtonsDiv && !document.getElementById('global-stats-btn')) {
            const statsButton = document.createElement('button');
            statsButton.id = 'global-stats-btn';
            statsButton.className = 'global-btn';
            statsButton.textContent = 'View Statistics';
            statsButton.onclick = () => { window.location.href = '/stats'; };
            globalButtonsDiv.appendChild(statsButton);
        }
    }

    // 更新全局控制面板的可见性
    function updateGlobalControlsVisibility() {
        if (globalControls) {
            const greenhouseCount = Object.keys(greenhouseState).length;
            globalControls.style.display = greenhouseCount > 0 ? 'block' : 'none';
        }
    }
});
