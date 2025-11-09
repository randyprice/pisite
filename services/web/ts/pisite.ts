// Token for internal `POST`s.
const token = document.querySelector<HTMLMetaElement>('meta[name="token"]')?.content ?? '';

// POST JSON data to the URL and return its response.
async function postJson(url: string): Promise<any> {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Token': token,
        }
    });
    return response.json();
}

// Add a simple listener to a toggle switch.
function registerSwitch(elementId: string, url: string) {
    const checkbox = document.getElementById(elementId) as HTMLInputElement | null;
    if (checkbox == null) {
        console.error(`checkbox id=${elementId} not found`)
        return;
    }
    checkbox.addEventListener('change', () => {
        postJson(url)
        .then((data: { on: boolean }) => {
            checkbox.checked = data.on;
        })
        .catch(err => console.error(`error toggling ${elementId}: `, err));
    })
}

// Update the service monitor table.
function _updateServiceMonitor(elementId: string, url: string) {
    const tableBody = document.getElementById(elementId) as HTMLTableSectionElement | null;
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
            const row = document.createElement('tr');
            // Service name.
            const nameCell = document.createElement('td');
            nameCell.textContent = service.service_name;
            // Service status.
            const statusCell = document.createElement('td');
            statusCell.textContent = service.service_status?.Status || 'unknown';
            const state = service.service_status?.State;
            if (state === 'running') {
                statusCell.style.color = 'green';
            } else if (state === 'stopped') {
                statusCell.style.color = 'red';
            } else {
                statusCell.style.color = 'black';
            }
            // Create row.
            row.appendChild(nameCell);
            row.appendChild(statusCell);
            tableBody.appendChild(row);
        });
    })
    .catch(err => {
        console.error('error updating service monitor table: ', err)
            tableBody.textContent = 'error';
    });
}

// Update metrics.
function _updateMetrics(elementId: string, url: string) {
    const span = document.getElementById(elementId) as HTMLSpanElement | null;
    if (span == null) {
        console.error(`span id=${elementId} not found`);
        return;
    }
    postJson(url)
    .then(data => {
        if (data.temperature !== null && data.temperature !== undefined) {
            span.textContent = data.temperature.toFixed(2) + ' C';
        } else {
            span.textContent = '—';
        }
    })
    .catch(err => {
        console.error(`error reading metric for span id=${elementId}:`, err);
        span.textContent = 'error';
    });
}

// Add callbacks to each switch.
const switches: [string, string][] = [
    // format: [<element id>, <url>]
    ['leds-switch', '/toggle/leds'],
    ['fan-switch', '/toggle/fan'],
];
switches.forEach(([elemendId, url]) => {
    registerSwitch(elemendId, url)
});

// Service monitor.
const serviceMonitorTableBodyElementId = 'service-monitor-table-body';
const updateServiceMonitorUrl = '/service-monitor/update'
const updateServiceMonitor = () => _updateServiceMonitor(
    serviceMonitorTableBodyElementId,
    updateServiceMonitorUrl,
);

// Metrics.
const cpuTemperatureSpanElementId = 'cpu-temperature';
const updateMetricsUrl = '/metrics/update'
const updateMetrics = () => _updateMetrics(
    cpuTemperatureSpanElementId,
    updateMetricsUrl,
);

// Start repeating tasks.
const repeatingTasks: [() => void, number][] = [
    [updateServiceMonitor, 60],
    [updateMetrics, 1],
]
repeatingTasks.forEach(([task, time_sec]) => {
    setInterval(task, time_sec * 1000);
    task();
})
