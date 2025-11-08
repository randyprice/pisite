import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from threading import Lock

import gpiod
from gpiod import Chip, LineSettings, LineRequest
from gpiod.line import Direction, Edge, Value

_DEVICE = "/dev/gpiochip4"

_logger = logging.getLogger(__name__)
gpio_lock = Lock()

@dataclass
class State:
    leds: Value = Value.ACTIVE
    fan: Value = Value.ACTIVE

def _set_pins(pins: Iterable[int], value: Value) -> None:
    config = {
        pin: LineSettings(direction=Direction.OUTPUT, output_value=value)
        for pin in pins
    }
    with gpio_lock, gpiod.request_lines(
        _DEVICE,
        consumer="blink-example",
        config=config,
    ) as request:
        for pin in pins:
            request.set_value(pin, value)



def toggle_value(value: Value) -> Value:
    return Value.INACTIVE if value == Value.ACTIVE else Value.ACTIVE

def activate_pins(pins: Iterable[int]) -> None:
    _set_pins(pins, Value.ACTIVE)

def toggle_pins(pins: Iterable[int], current_value: Value) -> None:
    new_value = toggle_value(current_value)
    _set_pins(pins, new_value)
