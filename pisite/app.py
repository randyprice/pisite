from dataclasses import dataclass
import json
import logging
import secrets
from typing import Self

from flask import current_app, request, Blueprint, Flask, jsonify, render_template

from pisite import control

@dataclass
class GpioConfig:
    power_led_control_pin: int
    io_led_control_pin: int
    fan_control_pin: int

    @classmethod
    def from_json(cls, config_path: str) -> Self:
        with open(config_path) as file:
            data = json.load(file)
        return GpioConfig(**data)

    def led_control_pins(self) -> set[int]:
        return {self.power_led_control_pin, self.io_led_control_pin}

class MyApp(Flask):
    def __init__(self, import_name: str, config_path: str, *args, **kwargs):
        super().__init__(import_name, *args, **kwargs)
        self.gpio_config = GpioConfig.from_json(config_path)
        self.control_state = control.State()
        self.token = secrets.token_hex(16)

# App.
admin = Blueprint('admin', __name__)

@admin.route('/')
def hello_world():
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
    # FIXME restore when curcuit is built.
    # control.toggle_pins(
    #     {current_app.gpio_config.fan_control_pin},
    #     current_app.control_state.fan,
    # )
    current_app.control_state.fan = control.toggle_value(current_app.control_state.fan)
    current_app.logger.info(f'fan set to {current_app.control_state.fan.name}')
    return jsonify({'fan_on': bool(current_app.control_state.fan)})

def create_app(config_file: str) -> MyApp:
    app = MyApp(__name__, config_file)
    app.register_blueprint(admin)
    app.logger.setLevel(logging.INFO)
    # Turn on the lights!
    # FIXME turn on the fan too
    control.activate_pins(app.gpio_config.led_control_pins())
    return app

if __name__ == '__main__':
    pass
