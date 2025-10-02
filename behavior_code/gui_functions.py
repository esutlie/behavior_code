from support_classes import *
from time import sleep
from timescapes import *
import RPi.GPIO as GPIO
import random
import pickle


def run_behavior(mouse):
    print(f"running behavior for {mouse}")


def calibrate(port):
    print(f'calibrating port {port}')
    with open('stand_alone/durations.pkl', 'rb') as f:
        durations = pickle.load(f)
    GPIO.setmode(GPIO.BCM)
    port_object = Port(port, dist_info='filler', duration=durations[port])
    for _ in range(100):
        port_object.sol_on()
        sleep(port_object.base_duration)
        port_object.sol_off()
        sleep(.1)


def increase(port):
    with open('stand_alone/durations.pkl', 'rb') as f:
        durations = pickle.load(f)
    durations[port] += .0005
    print(f'increasing port {port} to {durations[port]}')
    with open('stand_alone/durations.pkl', 'wb') as f:
        pickle.dump(durations, f)


def decrease(port):
    with open('stand_alone/durations.pkl', 'rb') as f:
        durations = pickle.load(f)
    durations[port] -= .0005
    print(f'decreasing port {port} to {durations[port]}')
    with open('stand_alone/durations.pkl', 'wb') as f:
        pickle.dump(durations, f)


def reset():
    print('resetting task')


def stop():
    print('stopping task')


def party():
    print('partying')

#
# if __name__ == '__main__':
#     durations = {1: .01,
#                  2: .01,
#                  3: .01}
#     with open('durations.pkl', 'wb') as f:
#         pickle.dump(durations, f)
