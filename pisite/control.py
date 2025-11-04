from dataclasses import dataclass
from typing import Self

import gpiod
from gpiod import LineSettings
from gpiod.line import Direction, Value

@dataclass
class State:
    leds: Value = Value.ACTIVE
    fan: Value = Value.ACTIVE

def _set_pins(pins: set[int], value: Value):
    config = {
        pin: LineSettings(direction=Direction.OUTPUT, output_value=value)
        for pin in pins
    }
    with gpiod.request_lines(
        "/dev/gpiochip4",
        consumer="blink-example",
        config=config,
    ) as request:
        for pin in pins:
            request.set_value(pin, value)

def toggle_value(value: Value) -> Value:
    return Value.INACTIVE if value == Value.ACTIVE else Value.ACTIVE

def activate_pins(pins: set[int]):
    _set_pins(pins, Value.ACTIVE)

def toggle_pins(pins: set[int], current_value: Value):
    new_value = toggle_value(current_value)
    _set_pins(pins, new_value)
