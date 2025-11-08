import json
import logging
import secrets
import tomllib
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Self

from flask import current_app, request, Blueprint, Flask, jsonify, render_template

from pisite import control

class MyApp(Flask):
    def __init__(self, import_name: str, *args, **kwargs) -> Self:
        super().__init__(import_name, *args, **kwargs)
        # States of fan and LEDs (active/inactive, i.e. on/off).
        self.control_state = control.State()
        # Secret token for internal requests.
        self.token = secrets.token_hex(16)

# App.
admin = Blueprint('admin', __name__)

# Decorator for methods that should only be called by the application
# itself, which is validated by the use of the application's token.
def requires_internal_token(function: Callable) -> Callable:
    @wraps(function)
    def decoratorated_function(*args, **kwargs):
        if request.headers.get('X-Token') != current_app.token:
            return jsonify({'error': 'invalid token'}), HTTPStatus.FORBIDDEN
        return function(*args, **kwargs)
    return decoratorated_function

@admin.route('/')
def index():
    return render_template(
        'index.html',
        leds_on=bool(current_app.control_state.leds),
        fan_on=bool(current_app.control_state.fan),
        token=current_app.token,
    )

@admin.route('/toggle/leds', methods=['POST'])
@requires_internal_token
def toggle_leds():
    control.toggle_pin(
        current_app.config['GPIO_DEVICE'],
        current_app.config['GPIO_PINS']['LED_CONTROL'],
        current_app.control_state.leds,
    )
    current_app.control_state.leds = control.toggle_value(current_app.control_state.leds)
    current_app.logger.info(f'LEDs set to {current_app.control_state.leds.name}')
    return jsonify({'leds_on': bool(current_app.control_state.leds)})

@admin.route('/toggle/fan', methods=['POST'])
@requires_internal_token
def toggle_fan():
    control.toggle_pin(
        current_app.config['GPIO_DEVICE'],
        current_app.config['GPIO_PINS']['FAN_CONTROL'],
        current_app.control_state.fan,
    )
    current_app.control_state.fan = control.toggle_value(current_app.control_state.fan)
    current_app.logger.info(f'fan set to {current_app.control_state.fan.name}')
    return jsonify({'fan_on': bool(current_app.control_state.fan)})

def _parse_monitor_file(monitor_file: str, service_names: set[str]) -> dict:
    with open(monitor_file) as file:
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
@requires_internal_token
def update_service_monitor():
    try:
        # FIXME sanitize service names!!!!
        service_statuses = _parse_monitor_file(
            current_app.config['SERVICE_MONITOR_FILE'],
            current_app.config['SERVICES'],
         )
    except FileNotFoundError, ValueError:
        service_statuses = []
    return jsonify(service_statuses)

@admin.route('/metrics/update', methods=['POST'])
@requires_internal_token
def update_metrics():
    try:
        temperature_c = (
            int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())
            / 1000.0
        )
    except:
        temperature_c = None
    return jsonify({'temperature': temperature_c})



def create_app(config_file: str, service_monitor_file: str, gpio_device: str) -> MyApp:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    app = MyApp(__name__)
    app.logger.setLevel(logging.INFO)
    app.config.from_file(config_file, load=tomllib.load, text=False)
    app.config.update({
        'SERVICE_MONITOR_FILE': service_monitor_file,
        'GPIO_DEVICE': gpio_device,
    })
    app.register_blueprint(admin)
    # Turn everything on!
    control.activate_pins(
        app.config['GPIO_DEVICE'],
        {
            app.config['GPIO_PINS']['LED_CONTROL'],
            app.config['GPIO_PINS']['FAN_CONTROL'],
        }
    )

    return app

if __name__ == '__main__':
    pass
