import logging
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

import gpiod
from gpiod import LineSettings
from gpiod.line import Direction, Edge

# FIXME make CLI args
_DEVICE = '/dev/gpiochip4'
_TACH_PIN = 22

_logger = logging.getLogger(__name__)

def _parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('fan_rpm_file', metavar='fan-rpm-file', type=Path)
    return parser.parse_args()

def _init_logging() -> None:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def _measure_fan_rpm(pin: int) -> float:
    config = {
        pin: LineSettings(
            direction=Direction.INPUT,
            edge_detection=Edge.RISING,
        )
    }
    with gpiod.request_lines(
        _DEVICE,
        consumer="fan-reader",
        config=config,
    ) as request:
        time.sleep(0.1)
        num_events = len(request.read_edge_events())
        _logger.info(f'{num_events} events read')
        rpm = (num_events / 0.1) * 60
        return rpm

def main():
    args = _parse_args()
    _init_logging()
    while True:
        rpm = _measure_fan_rpm(_TACH_PIN)
        args.fan_rpm_file.write_text(f'{rpm}')
        time.sleep(0.9)

if __name__ == '__main__':
    main()