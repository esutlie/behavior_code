import RPi.GPIO as GPIO
import time
import datetime
import os
from timescapes import *
import pexpect
import pickle
import tempfile
import smbus
import numpy as np


class Error(Exception):
    """Base class for other exceptions"""
    pass


class PortNumberError(Error):
    """Raised when there are the wrong number of ports passed"""
    pass


class TaskNameError(Error):
    """Raised when the task name is not recognized"""
    pass


class MouseSettingsError(Error):
    """Raised when settings aren't defined for the mouse"""
    pass


global_num_trials = 200
global_max_time = 30  # minutes


def test(i):
    print('test ' + str(i))


def ssh(host, cmd, user, password, timeout=30, bg_run=False):
    """SSH'es to a host using the supplied credentials and executes a command.
    Throws an exception if the command doesn't return 0.
    bgrun: run command in the background"""

    options = '-q -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oPubkeyAuthentication=no'
    if bg_run:
        options += ' -f'

    ssh_cmd = 'ssh %s@%s %s \'%s\'' % (user, host, options, cmd)
    print(ssh_cmd)
    child = pexpect.spawnu(ssh_cmd, timeout=timeout)
    child.expect(['[Pp]assword: '])
    child.sendline(password)
    child.expect(pexpect.EOF)
    child.close()


def scp(host, filename, destination, user, password, timeout=30, bg_run=False, recursive=False, cmd=False):
    """Scp's to a host using the supplied credentials and executes a command.
    Throws an exception if the command doesn't return 0.
    bgrun: run command in the background"""

    options = '-q -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oPubkeyAuthentication=no'
    if recursive:
        options += ' -r'
    if bg_run:
        options += ' -f'
    scp_cmd = 'scp %s %s %s@%s:\'"%s"\'' % (options, filename, user, host, os.path.join(destination, filename))
    print(scp_cmd)
    if cmd:
        return scp_cmd
    child = pexpect.spawnu(scp_cmd, timeout=timeout)  # spawnu for Python 3
    child.expect(['[Pp]assword: '])
    child.sendline(password)
    child.expect(pexpect.EOF)
    child.close()
    return child.exitstatus


def sync_stream(self):
    pin_map = {'session': 25,
               'trial': 8,
               'head1': 7,
               'head2': 16,
               'lick1': 20,
               'lick2': 21,
               'sol1': 5,
               'sol2': 6,
               'led1': 6,
               'led2': 6
               }
    for val in pin_map.values():
        GPIO.setup(val, GPIO.OUT)
        GPIO.output(val, GPIO.LOW)


def perform(task):
    try:
        task.initialize()
        task.structure(task)
    except KeyboardInterrupt:
        task.interrupted()
        raise KeyboardInterrupt
    task.end()


class Session:
    def __init__(self, mouse):
        self.ip = '192.168.137.1'
        self.user = 'Shichen'
        self.password = 'shuler'
        self.mouse = mouse
        self.ssh_path = os.path.join('OneDrive - Johns Hopkins', 'ShulerLab', 'behavior_code', 'data', self.mouse)
        self.data_send_path = os.path.join('C:', 'Users','Shichen', self.ssh_path)

        # error with 0: re.compile('[Pp]assword: ') means you need to update the ip address. open command prompt and
        # type ipconfig/all then press enter. Find the ip address starting with 10 and update it here
        # self.user = 'Elissa'
        self.host_name = os.uname()[1]
        self.data_write_path = "/data/" + self.mouse
        self.datetime = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = "data_" + self.datetime + ".txt"
        # self.ssh_path = 'GoogleDrive/Code/Python/behavior_code/data/' + self.mouse
        # self.data_send_path = 'C:/Users/Elissa/' + self.ssh_path + '/'
        self.halted = False
        self.smooth_finish = False
        GPIO.setmode(GPIO.BCM)
        print(os.getcwd())
        os.system('sudo -u pi mkdir -p ' + os.getcwd() + self.data_write_path)
        os.chdir(os.getcwd() + self.data_write_path)
        os.system('sudo touch ' + self.filename)
        os.system('sudo chmod o+w ' + self.filename)
        self.f = open(self.filename, 'w')
        self.start_time = None
        self.sync_pins = {'LED1': 25,
                          'LED2': 8,
                          'trial': 7,
                          'head1': 16,
                          'head2': 20,
                          'lick1': 21,
                          'lick2': 5,
                          'reward1': 6,
                          'reward2': 13}
        self.camera_pin = 10
        GPIO.setup(self.camera_pin, GPIO.OUT)
        GPIO.output(self.camera_pin, GPIO.LOW)

    def start(self, task_list):
        for val in self.sync_pins.values():
            GPIO.setup(val, GPIO.OUT)
            GPIO.output(val, GPIO.LOW)

        info_fields = 'mouse,date,time,task,port1_info,port2_info,box'
        data_fields = 'session_time,task,task_time,trial,trial_time,phase,port,value,key'

        self.f.write(info_fields + '\n')
        for task in task_list:
            info = [self.mouse, self.datetime[0:10], self.datetime[11:19], task.name]
            for port in task.ports:
                info = info + [str(port.dist_info)]
            info.append(self.host_name)
            info_string = ','.join(info)
            self.f.write(info_string + '\n')
        self.f.write('\n'.join(['# Data', data_fields, '']))

        self.start_time = time.time()
        self.log('nan,nan,nan,nan,setup,nan,1,session')
        for task in task_list:
            perform(task)

    def log(self, string):  # Adds session time stamp to beginning of string and logs it
        session_time = time.time() - self.start_time
        new_line = str(session_time) + ',' + string + '\n'
        # print(new_line)
        self.f.write(new_line)

    def end(self):
        self.log('nan,nan,nan,nan,setup,nan,0,session')
        self.f.close()
        os.system('sudo chmod o-w ' + self.filename)
        mkdir_command = 'if not exist "%s" mkdir "%s"' % (
            self.ssh_path.replace('/', '\\'), self.ssh_path.replace('/', '\\'))
        ssh(self.ip, mkdir_command, self.user, self.password)
        if not scp(self.ip, self.filename, self.data_send_path, self.user, self.password):
            print('\nSuccessful file transfer to "%s"\nDeleting local file from pi.' % self.data_send_path)
            os.remove(self.filename)
        else:
            print('connection back to desktop timed out')
        GPIO.cleanup()
        os.chdir(os.path.join(os.getcwd(), '..', '..'))
        print('\nFile closed and clean up complete')
        if self.halted:
            print('Session stopped early via KeyboardInterrupt')
        elif self.smooth_finish:
            print('Session ran smoothly to the end')
        else:
            print('Session ended due to an error:\n')


class Port:
    def __init__(self, name, dist_info, duration=None):
        if duration:
            self.base_duration = duration
        else:
            durations_path = os.path.join(os.getcwd(), '..', '..', 'durations.pkl')
            with open(durations_path, 'rb') as f:
                durations = pickle.load(f)
            self.base_duration = durations[name]

        pins = {1: [4, 27, 17, 9],
                2: [18, 24, 23, 11]}
        self.name = name
        [self.led_pin, self.ir_head_pin, self.ir_lick_pin, self.sol_pin] = pins[name]
        # self.led_pin = led_pin
        # self.ir_head_pin = ir_head_pin
        # self.ir_lick_pin = ir_lick_pin
        # self.sol_pin = sol_pin
        GPIO.setup(self.led_pin, GPIO.OUT)
        GPIO.output(self.led_pin, GPIO.LOW)
        GPIO.setup(self.sol_pin, GPIO.OUT)
        GPIO.output(self.sol_pin, GPIO.LOW)
        GPIO.setup(self.ir_head_pin, GPIO.IN)
        GPIO.setup(self.ir_lick_pin, GPIO.IN)
        print(f'Port {self.name} head status: {GPIO.input(self.ir_head_pin)}')
        print(f'Port {self.name} lick status: {GPIO.input(self.ir_lick_pin)}')
        self.head_status = 0
        self.lick_status = 0
        self.sol = False
        self.led = False
        self.dist_info = dist_info
        # self.distribution = distribution
        # self.dist_args = dist_args
        self.sol_opened_time = None
        self.led_on_time = None
        self.led_duration = 1
        print(str(name) + ' dur=' + str(self.base_duration))
        self.available = False
        self.licked = True
        self.led_stay = False
        self.lick_start_time = time.time()

    def sol_on(self):
        GPIO.output(self.sol_pin, GPIO.HIGH)
        self.sol = True
        self.sol_opened_time = time.time()
        return time.time()

    def sol_off(self):
        GPIO.output(self.sol_pin, GPIO.LOW)
        self.sol = False
        return time.time()

    def sol_cleanup(self):
        if self.sol and self.sol_opened_time + self.base_duration < time.time():
            duration = time.time() - self.sol_opened_time
            GPIO.output(self.sol_pin, GPIO.LOW)
            self.sol = False
            return duration
        return False

    def led_cleanup(self):
        if self.led and self.led_on_time + self.led_duration < time.time() and not self.led_stay:
            duration = time.time() - self.led_on_time
            GPIO.output(self.led_pin, GPIO.LOW)
            self.led = False
            return duration
        return False

    def led_on(self):
        GPIO.output(self.led_pin, GPIO.HIGH)
        self.led_on_time = time.time()
        self.led = True
        print('led on')
        return time.time()

    def led_off(self):
        GPIO.output(self.led_pin, GPIO.LOW)
        self.led = False
        print('led off')
        return time.time()

    def head_status_change(self):
        change = GPIO.input(self.ir_head_pin) - self.head_status
        self.head_status += change
        return change

    def lick_status_change(self):
        change = GPIO.input(self.ir_lick_pin) - self.lick_status
        self.lick_status += change
        if change == 1:
            self.lick_start_time = time.time()
        elif change == -1:
            print(f'lick time: {time.time() - self.lick_start_time:.3f}')
        return change


class Task:
    def __init__(self, session, name='blank', structure=None, ports=None, limit='trials',
                 maximum=None, forgo=True, forced_trials=False):
        print('Starting task: %s' % name)
        self.structure = structure
        self.port_dict = ports
        self.ports = ports.values()
        # self.ports = initialize_ports(ports, distributions)
        self.session = session
        self.name = name
        self.limit = limit
        if limit == 'trials':
            self.num_trials = maximum if maximum else global_num_trials
            self.max_time = None
        elif limit == 'time':
            self.max_time = maximum * 60 if maximum else global_max_time * 60
            self.num_trials = None
        self.trial_number = 'nan'
        self.phase = 'setup'
        self.task_start_time = None
        self.trial_start_time = None
        self.last_video_start = None
        self.reward_count = 0
        self.last_report = 0
        self.report_interval = 5  # Seconds
        self.forgo = forgo
        self.forced_trials = forced_trials
        self.frame_rate = 25  # frames per second
        self.frame_interval = 1 / self.frame_rate
        self.last_frame = time.time()
        self.cam_high = False

    def initialize(self):
        self.task_start_time = time.time()
        for port in self.ports:
            port.head_status = GPIO.input(port.ir_head_pin)
            port.lick_status = GPIO.input(port.ir_lick_pin)

    def start(self):
        self.task_start_time = time.time()
        self.log('nan', 1, 'task')
        self.trial_start_time = time.time()
        self.trial_number = 0
        # self.check_video()

    def end(self):
        self.phase = 'setup'
        self.trial_number = 'nan'
        self.sol_cleanup()
        self.log('nan', 0, 'task')

    def interrupted(self):
        self.log('nan', 0, 'task_interrupted')

    def check_number_of_ports(self, num):
        if num != len(self.ports):
            raise PortNumberError('\n This task needs %i ports, but %i were initialized.' % (num, len(self.ports)))

    def log(self, port_name, start, key):  # Adds task name and timestamp, trial name and timestamp, and phase
        task_timestamp = time.time() - self.task_start_time
        if self.trial_number == 'nan':
            trial_timestamp = 'nan'
        else:
            trial_timestamp = time.time() - self.trial_start_time
        new_string = ','.join(
            [self.name, str(task_timestamp),
             str(self.trial_number), str(trial_timestamp),
             str(self.phase), str(port_name), str(start), key])
        if key in ['trial']:
            if start:
                GPIO.output(self.session.sync_pins[key], GPIO.HIGH)
            else:
                GPIO.output(self.session.sync_pins[key], GPIO.LOW)
        elif key in ['head', 'lick', 'LED', 'reward']:
            if key == 'led':
                print(self.session.sync_pins[key + str(port_name)])
            if start:
                GPIO.output(self.session.sync_pins[key + str(port_name)], GPIO.HIGH)
                if key == 'LED1':
                    GPIO.output(self.session.sync_pins['trial'], GPIO.LOW)
            else:
                GPIO.output(self.session.sync_pins[key + str(port_name)], GPIO.LOW)

        # elif key == 'sol':
        #     GPIO.output(self.session.sync_pins['sol' + str(port_name)], GPIO.HIGH)
        # elif key == 'sol_duration':
        #     GPIO.output(self.session.sync_pins['sol' + str(port_name)], GPIO.LOW)
        self.session.log(new_string)

    def start_trial(self, port_name='nan'):
        self.trial_start_time = time.time()
        self.log(port_name, 1, 'trial')
        current_time = (time.time() - self.task_start_time) / 60
        print('trial %i start at %f' % (self.trial_number, current_time))
        # print('time: %f' % current_time)

    def end_trial(self, port_name='nan'):
        self.log(port_name, 0, 'trial')
        self.trial_number += 1

    def next_trial(self, end_port_name='nan', start_port_name='nan'):
        self.end_trial(port_name=end_port_name)
        if self.condition():
            self.start_trial(port_name=start_port_name)

    def sol_cleanup(self):
        for port in self.ports:
            closed = port.sol_cleanup()
            if closed:
                self.log(port.name, 0, 'reward')

    def led_cleanup(self):
        for port in self.ports:
            if port.available == port.led:
                if port.available:
                    port.led_off()
                    self.log(port.name, 0, 'LED')
                else:
                    port.led_on()
                    self.log(port.name, 1, 'LED')

    def check_buttons(self, button_pad):
        button_presses = button_pad.presses()
        if 1 in button_presses[0:len(self.ports)]:
            index = button_presses.index(1)
            self.ports[index].sol_on()
            time.sleep(self.ports[index].base_duration)
            self.ports[index].sol_off()
            print('manual reward delivered in port  ' + str(index))
            self.log(self.ports[index].name, 1, 'manual_reward')

    def condition(self):
        if self.limit == 'trials':
            conditional = self.trial_number <= self.num_trials
        elif self.limit == 'time':
            conditional = time.time() - self.task_start_time < self.max_time
        else:
            conditional = False
        return conditional

    def check_video(self):
        minutes_per = 5
        if not self.last_video_start or time.time() - self.last_video_start > minutes_per * 60:
            print('video recording started')
            self.last_video_start = time.time()
            os.system(
                'ssh Elissa@10.194.169.93 \'Anaconda3\\Scripts\\activate open_cv && cd PycharmProjects\\open_cv_test && curl -X POST -H "Content-Type: application/json" -d "{\\"mouse\\":\\"' + self.session.mouse + '\\"}" localhost:8000/check_start\'')
            self.log('nan', 1, 'video')

    def check_time(self):
        if (time.time() - self.last_report) > self.report_interval:
            task_time = time.time() - self.task_start_time
            print('%i rewards in %s' % (
                int(self.reward_count), str(datetime.timedelta(seconds=task_time))[2:7]))
            self.last_report = time.time()
        if (time.time() - self.last_frame) > self.frame_interval:  # If the square wave period has passed, go high
            GPIO.output(self.session.camera_pin, GPIO.HIGH)
            self.last_frame = time.time()
            self.cam_high = True
            self.log('nan', 1, 'camera')
        # If half the period has passed and it's high, go low
        if (time.time() - self.last_frame) > self.frame_interval / 2 and self.cam_high:
            GPIO.output(self.session.camera_pin, GPIO.LOW)
            self.cam_high = False
            self.log('nan', 0, 'camera')


class Expander:
    def __init__(self, input_pins_a=None, input_pins_b=None):
        self.bus = smbus.SMBus(1)
        self.DEVICE = 0x20  # Device address (A0-A2)
        self.SETUP_REGISTER = [0x00, 0x01]  # Pin direction register
        self.INPUT_REGISTER = [0x12, 0x13]  # Register for inputs on A
        self.OUTPUT_REGISTER = [0x14, 0x15]  # Register for inputs on A
        self.output_pin_status = np.zeros([2, 8])
        self.input_pin_status = np.zeros([2, 8])
        self.input_pins = [input_pins_a, input_pins_b]
        for side in [0, 1]:
            self.bus.write_byte_data(self.DEVICE, self.SETUP_REGISTER[side], self.to_hex(self.input_pins[side]))

    def on(self, side, pin):
        self.output_pin_status[side, pin] = 1
        self.refresh_pins()

    def off(self, side, pin):
        self.output_pin_status[side, pin] = 0
        self.refresh_pins()

    def refresh_pins(self):
        for side in [0, 1]:
            self.bus.write_byte_data(self.DEVICE, self.OUTPUT_REGISTER[side],
                                     self.to_hex(np.where(self.output_pin_status[side])))
            input_status = self.bus.read_byte_data(self.DEVICE, self.INPUT_REGISTER[side])
            print(input_status)

    def to_hex(self, num_list=None):
        if not num_list:
            return 0
        else:
            return np.sum([2 ** num for num in num_list])


if __name__ == '__main__':
    expander = Expander()
    expander.on(0, [2, 3, 6])
    expander.output_pin_status[1, :-3] = 1
    expander.refresh_pins()
