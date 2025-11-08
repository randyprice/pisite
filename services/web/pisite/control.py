from collections.abc import Iterable
from dataclasses import dataclass
from threading import Lock

import gpiod
from gpiod import LineSettings
from gpiod.line import Direction, Value

gpio_lock = Lock()

@dataclass
class State:
    leds: Value = Value.ACTIVE
    fan: Value = Value.ACTIVE

def _set_pins(device: str, pins: Iterable[int], value: Value) -> None:
    config = {
        pin: LineSettings(direction=Direction.OUTPUT, output_value=value)
        for pin in pins
    }
    with gpio_lock, gpiod.request_lines(
        device,
        config=config,
        consumer="pisite",
    ) as request:
        for pin in pins:
            request.set_value(pin, value)

def toggle_value(value: Value) -> Value:
    return Value.INACTIVE if value == Value.ACTIVE else Value.ACTIVE

def activate_pins(device: str, pins: Iterable[int]) -> None:
    _set_pins(device, pins, Value.ACTIVE)

def toggle_pins(device: str, pins: Iterable[int], current_value: Value) -> None:
    new_value = toggle_value(current_value)
    _set_pins(device, pins, new_value)

def toggle_pin(device: str, pin: int, current_value: Value) -> None:
    toggle_pins(device, {pin}, current_value)
