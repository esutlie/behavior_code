import numpy as np
import tkinter as tk
import tkinter.font as font
import tkinter.ttk as ttk
from functools import partial
import RPi.GPIO as GPIO
from support_classes import *
import pickle
from time import sleep
from main import *
import pexpect
from user_settings import get_user_info
import os

info_dict = get_user_info()

# scp -r C:\Users\Elissa\GoogleDrive\Code\Python\behavior_code\stand_alone pi@elissapi0:\home\pi
# scp C:\Users\Elissa\GoogleDrive\Code\Python\behavior_code\stand_alone\scp_rescue.py pi@elissapi1:\home\pi\behavior

# scp -r "C:\Users\Shichen\OneDrive - Johns Hopkins\ShulerLab\behavior_code\stand_alone" pi@elissapi1:\home\pi\behavior1
pastel_colors = ['#ffffcc', '#99ccff', '#cc99ff', '#ff99cc', '#ffcc99', '#ffffcc', '#99ffcc', '#ccffff', '#ccccff',
                 '#ffccff', '#ffcccc', '#D3D3D3', '#f0a207']


class Gui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry('960x360')
        self.root.title('BehaviorGui')

        with open('durations.pkl', 'rb') as f:
            self.durations = pickle.load(f)
        self.calibration_text = {1: tk.StringVar(),
                                 2: tk.StringVar()}
        self.calibration_text[1].set(f'Port 1: {self.durations[1] * 1000}ms ')
        self.calibration_text[2].set(f'Port 2: {self.durations[2] * 1000}ms')
        myFont = font.Font(size=30)
        mouse_rows = len(info_dict['mouse_buttons'])
        self.mouse_assignments = info_dict['mouse_assignments']
        self.port_swap_assignments = info_dict['port_swap_assignments']
        self.block_swap_assignments = info_dict['block_swap_assignments']
        tasks = {
            'single_reward': single_reward,
            'multi_reward': multi_reward
        }
        for key in self.mouse_assignments.keys():
            self.mouse_assignments[key] = tasks[self.mouse_assignments[key]]
        # self.mouse_assignments = {
        #     'ES036': single_reward,
        #     'ES037': single_reward,
        #     'ES038': single_reward,
        #     'ES039': cued_forgo,
        #     'ES040': cued_forgo,
        #     'testmouse': cued_forgo,
        # }
        buttons = np.array(
            [*info_dict['mouse_buttons'],
             ['check_scp', 'check_ir', 'testmouse'],
             ['-0.25ms', self.calibration_text[1], '+0.25ms'],
             ['-0.25ms', self.calibration_text[2], '+0.25ms']])
        mouse_functions = np.array(
            [[partial(self.run_behavior, buttons[i, j]) for j in range(buttons.shape[1])] for i in range(mouse_rows)])
        control_func = np.array([[self.reset, self.check_ir, partial(self.run_behavior, 'testmouse')],
                                 [partial(self.decrease, 1), partial(self.calibrate, 1), partial(self.increase, 1)],
                                 [partial(self.decrease, 2), partial(self.calibrate, 2), partial(self.increase, 2)]])
        button_colors = [*info_dict['button_colors'],
                         [0, 0, 0],
                         [0, 0, 0],
                         [0, 0, 0],
                         ]
        functions = np.concatenate([mouse_functions, control_func])
        self.button_list = []
        for i in range(buttons.shape[0]):
            self.root.rowconfigure(i, weight=1, minsize=50)
            for j in range(buttons.shape[1]):
                self.root.columnconfigure(i, weight=1, minsize=75)
                frame = tk.Frame(
                    master=self.root,
                    # relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=i, column=j, sticky="nsew")
                if i in [mouse_rows + 1, mouse_rows + 2] and j == 1:
                    button = tk.Button(
                        textvariable=buttons[i, j],
                        font=myFont,
                        width=60,
                        height=7,
                        bg=pastel_colors[button_colors[i][j]],
                        fg="black",
                        master=frame,
                        command=functions[i, j])
                else:
                    button = tk.Button(
                        text=buttons[i, j],
                        font=myFont,
                        width=60,
                        height=7,
                        bg=pastel_colors[button_colors[i][j]],
                        fg="black",
                        master=frame,
                        command=functions[i, j])

                button.pack(fill=tk.BOTH, expand=True)
                self.button_list.append(button)
        self.root.mainloop()

    def run_behavior(self, mouse):
        task = self.mouse_assignments[mouse]
        swap_port = self.port_swap_assignments[mouse]
        swap_block = self.block_swap_assignments[mouse]
        print(f"running {task} for {mouse}")
        main(mouse, task, swap_port=swap_port, swap_block=swap_block)

    def calibrate(self, port):
        print(f'calibrating port {port}')
        GPIO.setmode(GPIO.BCM)
        port_object = Port(port, dist_info='filler', duration=self.durations[port])
        for _ in range(100):
            port_object.sol_on()
            sleep(port_object.base_duration)
            port_object.sol_off()
            sleep(.1)

    def increase(self, port):
        self.durations[port] = np.around(self.durations[port] + .00025, decimals=6)
        self.calibration_text[port].set(f'Port {port}: {self.durations[port] * 1000}ms')
        print(f'increasing port {port} to {self.durations[port]}')
        with open('durations.pkl', 'wb') as f:
            pickle.dump(self.durations, f)

    def decrease(self, port):
        self.durations[port] = np.around(self.durations[port] - .00025, decimals=6)
        self.calibration_text[port].set(f'Port {port}: {self.durations[port] * 1000}ms')
        print(f'decreasing port {port} to {self.durations[port]}')
        with open('durations.pkl', 'wb') as f:
            pickle.dump(self.durations, f)

    def reset(self):
        session = Session('testmouse')
        session.start_time = time.time()
        session.log('test_line')
        session.smooth_finish = True
        session.end()
        # GPIO.setmode(GPIO.BCM)
        # ports = [Port(1, None, duration=.01), Port(2, None, duration=.01)]
        # GPIO.cleanup()
        # print('box reset')

    def check_ir(self):
        GPIO.setmode(GPIO.BCM)
        ports = [Port(1, None, duration=.01), Port(2, None, duration=.01)]
        start = time.time()
        while time.time() - start < 20:
            for port in ports:
                for change, event in zip([port.head_status_change(), port.lick_status_change()], ['head', 'lick']):
                    if change:
                        action = 'in' if change == 1 else 'out'
                        print(f'Port {port.name} {event} {action}')
        GPIO.cleanup()
        print('Done')


def run_gui():
    app = Gui()


if __name__ == '__main__':
    run_gui()
