import json
import logging
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from flask import current_app, request, Blueprint, Flask, jsonify, render_template

from pisite import control

_logger = logging.getLogger()

@dataclass
class GpioConfig:
    power_led_control_pin: int
    io_led_control_pin: int
    fan_control_pin: int

    @staticmethod
    def from_json(config_path: str) -> Self:
        with open(config_path) as file:
            data = json.load(file)
        return GpioConfig(**data)

    def led_control_pins(self) -> set[int]:
        return {self.power_led_control_pin, self.io_led_control_pin}

class MyApp(Flask):
    def __init__(self, import_name: str, config_path: str, monitor_file: str, *args, **kwargs):
        super().__init__(import_name, *args, **kwargs)
        self.gpio_config = GpioConfig.from_json(config_path)
        self.control_state = control.State()
        self.token = secrets.token_hex(16)
        self.monitor_path = Path(monitor_file)


# App.
admin = Blueprint('admin', __name__)

@admin.route('/')
def index():
    return render_template(
        'index.html',
        leds_on=bool(current_app.control_state.leds),
        fan_on=bool(current_app.control_state.fan),
        token=current_app.token,
    )

@admin.route('/toggle/leds', methods=['POST'])
def toggle_leds():
    token = request.headers.get('X-Token')
    if token != current_app.token:
        return jsonify({'error': 'invalid token'}), 403
    control.toggle_pins(
        current_app.gpio_config.led_control_pins(),
        current_app.control_state.leds,
    )
    current_app.control_state.leds = control.toggle_value(current_app.control_state.leds)
    current_app.logger.info(f'LEDs set to {current_app.control_state.leds.name}')
    return jsonify({'leds_on': bool(current_app.control_state.leds)})

@admin.route('/toggle/fan', methods=['POST'])
def toggle_fan():
    token = request.headers.get('X-Token')
    if token != current_app.token:
        return jsonify({'error': 'invalid token'}), 403
    control.toggle_pins(
        {current_app.gpio_config.fan_control_pin},
        current_app.control_state.fan,
    )
    current_app.control_state.fan = control.toggle_value(current_app.control_state.fan)
    current_app.logger.info(f'fan set to {current_app.control_state.fan.name}')
    return jsonify({'fan_on': bool(current_app.control_state.fan)})

def _parse_monitor_file(monitor_file: Path, service_names: set[str]) -> dict:
    with monitor_file.open() as file:
        container_statuses = json.load(file)
    parsed_data = []
    for service_name in service_names:
        matching_container_statuses = [
            container_status
            for container_status in container_statuses
            if any(service_name in container_name for container_name in container_status['Names'])
        ]
        if not matching_container_statuses:
            current_app.logger.warning(f'container {service_name} does not match any container names found in `podman ps`')
            service_status = {}
        elif len(matching_container_statuses) > 1:
            current_app.logger.warning(f'multiple containers ({', '.join([container_status['Id'] for container_status in matching_container_statuses])}) match name "{service_name}"')
            service_status = {}
        else:
            service_status = matching_container_statuses[0]
        parsed_data.append({
            'service_name': service_name,
            'service_status': service_status,
        })

    return parsed_data


@admin.route('/service-monitor/update', methods=['POST'])
def update_service_monitor():
    token = request.headers.get('X-Token')
    if token != current_app.token:
        return jsonify({'error': 'invalid token'}), 403
    try:
        # FIXME sanitize service names!!!!
        service_statuses = _parse_monitor_file(current_app.monitor_path, {'yapper', 'yoinker'})
    except FileNotFoundError, ValueError:
        service_statuses = []
    return jsonify(service_statuses)

@admin.route('/metrics/update', methods=['POST'])
def update_metrics():
    token = request.headers.get('X-Token')
    if token != current_app.token:
        return jsonify({'error': 'invalid token'}), 403
    try:
        temperature_c = (
            int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())
            / 1000.0
        )
    except:
        temperature_c = None
    return jsonify({'temperature': temperature_c})



def create_app(config_file: str, monitor_file: str) -> MyApp:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    app = MyApp(__name__, config_file, monitor_file)
    app.register_blueprint(admin)
    app.logger.setLevel(logging.INFO)
    # Turn everything on!
    control.activate_pins({
        app.gpio_config.power_led_control_pin,
        app.gpio_config.io_led_control_pin,
        app.gpio_config.fan_control_pin,
    })

    return app

if __name__ == '__main__':
    pass
