import os
from tkinter import *
import time
from os import walk
import pandas as pd
from csv import DictReader, reader
import numpy as np
from datetime import date
from upload_to_pi import reset_time, ping_host
from user_info import get_user_info
import shutil

info_dict = get_user_info()
initials = info_dict['initials']
pi_names = info_dict['pi_names']


def get_today_filepaths(days_back=0):
    file_paths = []
    for root, dirs, filenames in walk(os.path.join(os.getcwd(), 'data')):
        if len(dirs) == 0 and os.path.basename(root)[:2] == initials:
            mouse = os.path.basename(root)
            for f in filenames:
                if f == 'desktop.ini':
                    continue
                file_date = date(int(f[5:9]), int(f[10:12]), int(f[13:15]))
                dif = date.today() - file_date
                if dif.days <= days_back:
                    # if f[5:15] == time.strftime("%Y-%m-%d"):
                    file_paths.append(os.path.join(mouse, f))
    return file_paths


def gen_data(file_paths):
    d = {}
    for f in file_paths:
        if f[:5] == 'mouse':
            print('stop')
        mouse_name = f[:5]
        file_name = f[6:]
        path = os.path.join(os.getcwd(), 'data', f)
        data = pd.read_csv(path, na_values=['None'], skiprows=3)
        with open(path, 'r') as file:
            r = reader(file)
            info_keys = next(r)
            info_values = next(r)
        starts = np.where([True if s[0] == '{' else False for s in info_values])[0][::-1]
        ends = np.where([True if s[-1] == '}' else False for s in info_values])[0][::-1]
        for i in range(len(starts)):
            info_values = info_values[:starts[i]] + [",".join(info_values[starts[i]:ends[i] + 1])] + info_values[
                                                                                                     ends[i] + 1:]
        info = dict(zip(info_keys, info_values))
        num_reward = len(data[(data.key == 'reward') & (data.value == 1)])
        mouse = os.path.dirname(f)
        reward_string = f'{num_reward}({info["box"][-1]})'

        half_session_path = os.path.join(os.getcwd(), 'data', 'half_sessions', file_name)
        if data.session_time.max() < 800:
            print(f'moving {file_name} to half sessions, session time: {data.session_time.max():.2f} seconds')
            shutil.move(path, half_session_path)
            continue
        if num_reward == 0:
            ans = input(f'remove zero reward file? (y/n)\n{path}\n???')
            if ans == 'y':
                half_session_path = os.path.join(os.getcwd(), 'data', 'half_sessions', file_name)
                shutil.move(path, half_session_path)
        else:
            if mouse in d.keys():
                d[mouse].append(reward_string)
            else:
                d[mouse] = [reward_string]
    return d


class App(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.label = Label(text="", fg="Black", font=("Helvetica", 18))
        self.label.place(x=40, y=50)
        self.host_names = pi_names
        self.host_status = [True] * 3

        data = gen_data(get_today_filepaths())
        txt = '\n'.join([f'{key}: {", ".join(str(d) for d in data[key])}' for key in data])
        self.label.configure(text=txt)

    def update(self):
        data = gen_data(get_today_filepaths())
        txt = '\n'.join([f'{key}: {", ".join(str(d) for d in data[key])}' for key in data])
        self.label.configure(text=txt)
        new_host_status = [ping_host(name) for name in self.host_names]
        for i, (a, b) in enumerate(zip(new_host_status, self.host_status)):
            if a and not b:
                reset_time(self.host_names[i])
        self.host_status = new_host_status
        self.after(10000, self.update)


def run_gui():
    root = Tk()
    app = App(root)
    root.wm_title("Tracker")
    root.geometry("300x400+2500+300")
    root.after(10000, app.update)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
