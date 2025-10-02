import pickle
import RPi.GPIO as GPIO
from support_classes import *
from timescapes import *
from time import sleep
import smbus
import numpy as np

DEVICE = 0x20  # Device address (A0-A2)
SETUP_A = 0x00  # Pin direction register
SETUP_B = 0x01  # Pin direction register
INPUT_A = 0x12  # Register for inputs on A
INPUT_B = 0x13  # Register for inputs on B
OUTPUT_A = 0x14  # Register for outputs on A
OUTPUT_B = 0x15  # Register for outputs on B


def led_test():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(16, GPIO.OUT)
    GPIO.setup(20, GPIO.OUT)
    GPIO.setup(21, GPIO.OUT)

    GPIO.output(20, GPIO.HIGH)
    sleep(5)
    GPIO.output(20, GPIO.LOW)
    sleep(2)
    GPIO.output(21, GPIO.HIGH)
    sleep(5)
    GPIO.output(21, GPIO.LOW)
    GPIO.cleanup()


def extra_gpio_test():
    expander = Expander()
    for i in range(2):
        for j in range(8):
            print(i)
            print(j)
            expander.on(i, j)
            sleep(1)
            expander.off(i, j)


def save_change():
    with open('durations.pkl', 'wb') as f:
        durations = {
            1: 0.0165,
            2: 0.01
        }
        pickle.dump(durations, f)


def test_sol(repeats=100, interval=.1):
    with open('durations.pkl', 'rb') as f:
        durations = pickle.load(f)
    GPIO.setmode(GPIO.BCM)
    ports = []
    exp_dist = {'distribution': exp_decreasing,
                'cumulative': 5,
                'staring_probability': 1}
    background_dist = {'distribution': 'background',
                       'rates': [.4, .8, .4, .8, .4, .8],
                       'duration': 5}
    port_dict = {
        'exp': Port(1, dist_info=exp_dist, duration=durations[1]),
        'background': Port(2, dist_info=background_dist, duration=durations[2])
    }
    ports = port_dict.values()
    try:
        for _ in range(repeats):
            for port in ports:
                port.sol_on()
                sleep(port.base_duration)
                port.sol_off()
                sleep(interval)
    finally:
        for port in ports:
            port.sol_off()


if __name__ == '__main__':
    save_change()
    test_sol()
    # led_test()
    # extra_gpio_test()
