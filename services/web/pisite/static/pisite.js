"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var _a, _b;
// Token for internal `POST`s.
const token = (_b = (_a = document.querySelector('meta[name="token"]')) === null || _a === void 0 ? void 0 : _a.content) !== null && _b !== void 0 ? _b : '';
// POST JSON data to the URL and return its response.
function postJson(url) {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Token': token,
            }
        });
        return response.json();
    });
}
// Add a simple listener to a toggle switch.
function registerSwitch(elementId, url) {
    const checkbox = document.getElementById(elementId);
    if (checkbox == null) {
        console.error(`checkbox id=${elementId} not found`);
        return;
    }
    checkbox.addEventListener('change', () => {
        postJson(url)
            .then((data) => {
            checkbox.checked = data.on;
        })
            .catch(err => console.error(`error toggling ${elementId}: `, err));
    });
}
// Update the service monitor table.
function _updateServiceMonitor(elementId, url) {
    const tableBody = document.getElementById(elementId);
    if (tableBody == null) {
        console.error(`table body id=${elementId} not found`);
        return;
    }
    postJson(url)
        .then(data => {
        if (!Array.isArray(data)) {
            console.error('expected JSON array, got JSON object');
            tableBody.textContent = 'error';
            return;
        }
        tableBody.innerHTML = '';
        data.forEach(service => {
            var _a, _b;
            const row = document.createElement('tr');
            // Service name.
            const nameCell = document.createElement('td');
            nameCell.textContent = service.service_name;
            // Service status.
            const statusCell = document.createElement('td');
            statusCell.textContent = ((_a = service.service_status) === null || _a === void 0 ? void 0 : _a.Status) || 'unknown';
            const state = (_b = service.service_status) === null || _b === void 0 ? void 0 : _b.State;
            if (state === 'running') {
                statusCell.style.color = 'green';
            }
            else if (state === 'stopped') {
                statusCell.style.color = 'red';
            }
            else {
                statusCell.style.color = 'black';
            }
            // Create row.
            row.appendChild(nameCell);
            row.appendChild(statusCell);
            tableBody.appendChild(row);
        });
    })
        .catch(err => {
        console.error('error updating service monitor table: ', err);
        tableBody.textContent = 'error';
    });
}
// Update metrics.
function _updateMetrics(elementId, url) {
    const span = document.getElementById(elementId);
    if (span == null) {
        console.error(`span id=${elementId} not found`);
        return;
    }
    postJson(url)
        .then(data => {
        if (data.temperature !== null && data.temperature !== undefined) {
            span.textContent = data.temperature.toFixed(2) + ' C';
        }
        else {
            span.textContent = '—';
        }
    })
        .catch(err => {
        console.error(`error reading metric for span id=${elementId}:`, err);
        span.textContent = 'error';
    });
}
// Add callbacks to each switch.
const switches = [
    // format: [<element id>, <url>]
    ['leds-switch', '/toggle/leds'],
    ['fan-switch', '/toggle/fan'],
];
switches.forEach(([elemendId, url]) => {
    registerSwitch(elemendId, url);
});
// Service monitor.
const serviceMonitorTableBodyElementId = 'service-monitor-table-body';
const updateServiceMonitorUrl = '/service-monitor/update';
const updateServiceMonitor = () => _updateServiceMonitor(serviceMonitorTableBodyElementId, updateServiceMonitorUrl);
// Metrics.
const cpuTemperatureSpanElementId = 'cpu-temperature';
const updateMetricsUrl = '/metrics/update';
const updateMetrics = () => _updateMetrics(cpuTemperatureSpanElementId, updateMetricsUrl);
// Start repeating tasks.
const repeatingTasks = [
    [updateServiceMonitor, 60],
    [updateMetrics, 1],
];
repeatingTasks.forEach(([task, time_sec]) => {
    setInterval(task, time_sec * 1000);
    task();
});
