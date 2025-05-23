from datetime import date
import os
from tkinter import *
import time
from os import walk
import pandas as pd
from csv import DictReader, reader
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import matplotlib.gridspec as gridspec

from upload_cloud_backup import behavior_data_dir
from user_info import get_user_info
import shutil
from datetime import datetime
import pdb

info_dict = get_user_info()
initials = info_dict['initials']
start_date = info_dict['start_date']
data_dir = behavior_data_dir


def get_today_filepaths(days_back=0):
    file_paths = []
    for root, dirs, filenames in walk(data_dir):
        if len(dirs) == 0 and os.path.basename(root)[:2] in initials:
            mouse = os.path.basename(root)
            for f in filenames:
                if f == 'desktop.ini':
                    continue
                file_date = datetime.strptime(f[5:-4], '%Y-%m-%d_%H-%M-%S')
                # file_date = date(int(f[5:9]), int(f[10:12]), int(f[13:15]))
                dif = datetime.today() - file_date
                if dif.days <= days_back:
                    # if f[5:15] == time.strftime("%Y-%m-%d"):
                    file_paths.append(os.path.join(mouse, f))
    return file_paths


def min_dif(a, b, tolerance=0, return_index=False, rev=False):
    if type(a) == pd.core.series.Series:
        a = a.values
    if type(b) == pd.core.series.Series:
        b = b.values
    if rev:
        outer = -1 * np.subtract.outer(a, b)
        outer[outer <= tolerance] = np.nan
    else:
        outer = np.subtract.outer(b, a)
        outer[outer <= tolerance] = np.nan
    # noinspection PyBroadException
    mins = np.nanmin(outer, axis=0)

    if return_index:
        index = np.nanargmin(outer, axis=0)
        return index, mins
    return mins


def read_pi_meta(pi_dir):
    with open(pi_dir, 'r') as file:  # Read meta data from first two lines into a dictionary
        line1 = file.readline()[:-1]
        line2 = file.readline()[:-1]
        pieces = line2.split(',')
        if '{' in line2:
            curly_start = np.where(np.array([p[0] for p in pieces]) == '{')[0]
            curly_end = np.where(np.array([p[-1] for p in pieces]) == '}')[0]
            pieces_list = []
            sub_piece = []
            for i in range(len(pieces)):
                if curly_start[0] <= i <= curly_end[0] or curly_start[1] <= i <= curly_end[1]:
                    sub_piece.append(pieces[i])
                else:
                    pieces_list.append(pieces[i])
                if i in curly_end:
                    string = ','.join(sub_piece)
                    try:
                        s, e = string.index('<'), string.index('>')
                        string = string[:s] + "'exp_decreasing'" + string[e + 1:]
                    except Exception as e:
                        pass
                    pieces_list.append(eval(string))
                    sub_piece = []
        else:
            pieces_list = line2.split(',')
    info = dict(zip(line1.split(','), pieces_list))
    return info


def gen_data(file_paths, select_mouse=None, return_info=False):
    d = {}
    for f in file_paths:
        mouse = os.path.dirname(f)
        if select_mouse is not None and mouse not in select_mouse:
            continue

        path = os.path.join(data_dir, f)
        meta_data = read_pi_meta(path)

        if return_info:
            data = meta_data
        else:
            try:
                data = pd.read_csv(path, na_values=['None'], skiprows=3)
            except pd.errors.EmptyDataError:
                print(f'empty file at {path}')
                continue
            try:
                data = data_reduction(data)

                #port info as a row
                port_info_row = [{
                    'key': meta_data['port1_info']['distribution'],
                    'port': meta_data['port1_info']['port_num']
                    # 'phase': last_row_phase,
                },
                    {'key': meta_data['port2_info']['distribution'],
                     'port': meta_data['port2_info']['port_num']
                     # 'phase': last_row_phase,
                     }
                ]

                #Added port info at the end of the dataframe
                portinfo_rows_df = pd.DataFrame(port_info_row).reindex(columns=data.columns)
                data = pd.concat([data, portinfo_rows_df], ignore_index=True)

            except ValueError:
                file_name = f[6:]
                half_session_path = os.path.join(data_dir, 'half_sessions', file_name)
                if data.session_time.max() < 800:
                    print(f'moving {f} to half sessions, session time: {data.session_time.max():.2f} seconds')
                    shutil.move(path, half_session_path)
                else:
                    ans = input(f'remove broken file? (y/n)\n{path}\n???')
                    if ans == 'y':
                        shutil.move(path, half_session_path)
                continue

        if mouse in d.keys():
            d[mouse].append(data)
        else:
            d[mouse] = [data]
    return d


def remove(df, key, tolerance, port):
    on_times = df[(df.key == key) & (df.value == 1) & (df.port == port)].session_time.to_numpy()
    off_times = df[(df.key == key) & (df.value == 0) & (df.port == port)].session_time.to_numpy()
    if (on_times.size > 0) & (off_times.size > 0):
        forward = min_dif(on_times, off_times)
        forward_off = min_dif(on_times, off_times, rev=True)
        forward[np.isnan(forward)] = tolerance
        forward_off[np.isnan(forward_off)] = tolerance
        on_times = on_times[forward >= tolerance]
        off_times = off_times[forward_off >= tolerance]

        back = min_dif(off_times, on_times, rev=True)
        back_off = min_dif(off_times, on_times)
        back[np.isnan(back)] = tolerance
        back_off[np.isnan(back_off)] = tolerance
        on_times = on_times[back >= tolerance]
        off_times = off_times[back_off >= tolerance]

    df = df[((df.key != key) | (df.value != 1) | (df.port != port)) | (df.session_time.isin(on_times))]
    df = df[((df.key != key) | (df.value != 0) | (df.port != port)) | (df.session_time.isin(off_times))]
    return df


def data_reduction(df, lick_tol=.01, head_tol=.2):
    df = df[df.key != 'camera']
    df = df[df.phase != 'setup']
    df = remove(df, 'head', head_tol, port=1)
    df = remove(df, 'head', head_tol, port=2)
    df = remove(df, 'lick', lick_tol, port=1)
    df = remove(df, 'lick', lick_tol, port=2)
    return df


def consumption_time(df):
    bgportassignment = df.loc[df['key'] == 'background', 'port'].iloc[-1]
    expportassignment = df.loc[df['key'] == 'exp_decreasing', 'port'].iloc[-1]
    bg_end_times = df[(df.key == 'LED') & (df.port == bgportassignment) & (df.value == 1)]
    exp_entries = df[(df.key == 'head') & (df.port == expportassignment) & (df.value == 1)]

    dif = min_dif(bg_end_times.session_time, exp_entries.session_time)

    bg_consumption = dif[~np.isnan(dif)]
    if df.task.iloc[10] != 'single_reward':
        consumption_df = pd.DataFrame()
        consumption_df['consumption time'] = bg_consumption
        consumption_df['port'] = ['bg'] * len(bg_consumption)
        return consumption_df

    exp_end_times = df[(df.key == 'LED') & (df.port == expportassignment) & (df.value == 1)]
    bg_entries = df[(df.key == 'head') & (df.port == bgportassignment) & (df.value == 1)]
    dif = min_dif(exp_end_times.session_time, bg_entries.session_time)
    exp_consumption = dif[~np.isnan(dif)]
    consumption_df = pd.DataFrame()
    consumption_df['consumption time'] = np.concatenate([bg_consumption, exp_consumption])
    consumption_df['port'] = ['bg'] * len(bg_consumption) + ['exp'] * len(exp_consumption)
    return consumption_df


def calculate_premature_leave(df, threshold=1.0): #trials with premature leave
    bgportassignment = df.loc[df['key'] == 'background', 'port'].iloc[-1]
    premature_leave_trials = 0  # Counter for trials with premature leave
    blocks = df.phase.dropna().unique()
    blocks.sort()
    results = []
    for block in blocks:
        block_data = df[df.phase == block]
        block_total_trials = len(block_data.trial.unique())
        for trial in block_data.trial.unique():
            if pd.isna(trial):
                continue  # Skip invalid trials
            trial_data = df[df.trial == trial] # Filter data for the current trial
            bg_on_times = trial_data[(trial_data['key'] == 'trial') &
                                      (trial_data['value'] == 1)].session_time.values
            if len(bg_on_times) == 0:
                continue
            bg_start = bg_on_times[0]
            bg_off_times = trial_data[(trial_data['key'] == 'LED') &
                                      (trial_data['port'] == bgportassignment) &
                                      (trial_data['value'] == 1)].session_time.values
            if len(bg_off_times) == 0:  # Check if no BG ON recorded
                continue
            bg_end = bg_off_times[0]
            bg_head_out_times = trial_data[(trial_data['key'] == 'head') & # Extract head-out and head-in times while BG port is active
                                        (trial_data['port'] == bgportassignment) &
                                        (trial_data['value'] == 0) &
                                        (trial_data['session_time'] >= bg_start) &
                                        (trial_data['session_time'] < bg_end)].session_time.values
            bg_head_in_times = trial_data[(trial_data['key'] == 'head') &
                                       (trial_data['port'] == bgportassignment) &
                                       (trial_data['value'] == 1) &
                                       (trial_data['session_time'] >= bg_start) &
                                       (trial_data['session_time'] < bg_end)].session_time.values
            for head_out in bg_head_out_times: # Check for premature leave: head-out without a valid head-in within threshold
                if not any((head_in > head_out) and (head_in - head_out) <= threshold for head_in in bg_head_in_times):
                    premature_leave_trials += 1  # Flag this trial as a premature leave
                    break  # Stop checking further head-outs in this trial
        premature_leave_rate = (premature_leave_trials / block_total_trials)
        results.append({"block": block,"premature leave numbers":premature_leave_trials, "premature leave rate": premature_leave_rate})
    premature_leave_df = pd.DataFrame(results)
    return premature_leave_df


def block_leave_times(df):
    bgportassignment = df.loc[df['key'] == 'background', 'port'].iloc[-1]
    expportassignment = df.loc[df['key'] == 'exp_decreasing', 'port'].iloc[-1]
    reward_trials = df[(df.key == 'reward_initiate')].trial.to_numpy()
    non_reward = ~df.trial.isin(reward_trials)
    bg_end_times = df[(df.key == 'LED') & (df.port == bgportassignment) & (df.value == 1) & non_reward]
    exp_entries = df[(df.key == 'head') & (df.value == 1) & (df.port == expportassignment) & non_reward]
    exp_exits = df[(df.key == 'head') & (df.value == 0) & (df.port == expportassignment) & non_reward]
    bg_end_times = bg_end_times[bg_end_times.session_time < exp_entries.session_time.max()]
    ind, dif = min_dif(bg_end_times.session_time, exp_entries.session_time, return_index=True)
    exp_entries = exp_entries.iloc[np.unique(ind)]
    exp_entries = exp_entries.groupby('trial').session_time.max()
    exp_exits = exp_exits.groupby('trial').session_time.max()
    valid_trials = np.intersect1d(exp_exits.index.values, exp_entries.index.values)
    valid_trials = np.intersect1d(valid_trials, bg_end_times.trial.values)
    exp_exits = exp_exits.loc[valid_trials]
    exp_entries = exp_entries.loc[valid_trials]

    if len(exp_exits.to_numpy()) != len(exp_entries.to_numpy()):
        print(
            f"Mismatch in exp_entries and exp_exits. "
            f"exp_entries: {exp_entries}, exp_exits: {exp_exits}. "
            "Using clean_entries_exits to resolve."
        )
        exp_entries, exp_exits = clean_entries_exits(exp_entries, exp_exits)
    leave_times = exp_exits.to_numpy() - exp_entries.to_numpy()

    trial_blocks = bg_end_times[bg_end_times.trial.isin(exp_entries.index.values)].phase.to_numpy()
    block_leaves_df = pd.DataFrame()
    block_leaves_df['leave time'] = leave_times
    block_leaves_df['block'] = trial_blocks
    return block_leaves_df


def get_entry_exit(df, trial):
    is_trial = df.trial == trial
    start = df.value == 1
    end = df.value == 0
    bgport = df.port == df.loc[df['key'] == 'background', 'port'].iloc[-1]
    expport = df.port == df.loc[df['key'] == 'exp_decreasing', 'port'].iloc[-1]
    # port1 = df.port == 1
    # port2 = df.port == 2

    trial_start = df[is_trial & start & (df.key == 'trial')].session_time.values[0]
    trial_middle = df[is_trial & end & (df.key == 'LED') & bgport].session_time.values[0] #head in to EXP, bg LED off
    trial_end = df[is_trial & end & (df.key == 'trial')].session_time.values[0]

    bg_entries = df[is_trial & bgport & start & (df.key == 'head')].session_time.to_numpy()
    bg_exits = df[is_trial & bgport & end & (df.key == 'head')].session_time.to_numpy()

    if len(bg_entries) == 0 or len(bg_exits) == 0 or bg_entries[0] > bg_exits[0]:
        bg_entries = np.concatenate([[trial_start], bg_entries])
    if trial_end - bg_entries[-1] < .1:
        bg_entries = bg_entries[:-1]
    if len(bg_exits) == 0 or bg_entries[-1] > bg_exits[-1]:
        bg_exits = np.concatenate([bg_exits, [trial_middle]])

    exp_entries = df[is_trial & expport & start & (df.key == 'head') &
                     (df.session_time > trial_middle)].session_time.to_numpy()
    exp_exits = df[is_trial & expport & end & (df.key == 'head') &
                   (df.session_time > trial_middle)].session_time.to_numpy()

    if not (len(exp_entries) == 0 and len(exp_exits) == 0):
        if len(exp_entries) == 0: #only exp out
            exp_entries = np.concatenate([[trial_middle], exp_entries])
        if len(exp_exits) == 0: #only exp in
            exp_exits = np.concatenate([exp_exits, [trial_end]])

        if exp_entries[0] > exp_exits[0]:
            exp_entries = np.concatenate([[trial_middle], exp_entries])
        if exp_entries[-1] > exp_exits[-1]:
            exp_exits = np.concatenate([exp_exits, [trial_end]])

    early_exp_entries = df[is_trial & expport & start & (df.key == 'head') &
                           (df.session_time < trial_middle)].session_time.to_numpy()
    early_exp_exits = df[is_trial & expport & end & (df.key == 'head') &
                         (df.session_time < trial_middle)].session_time.to_numpy()

    if not (len(early_exp_entries) == 0 and len(early_exp_exits) == 0): #any early exp in/out
        if len(early_exp_entries) == 0:
            early_exp_entries = np.concatenate([[trial_start], early_exp_entries])
        if len(early_exp_exits) == 0:
            early_exp_exits = np.concatenate([early_exp_exits, [trial_middle]])

        if early_exp_entries[0] > early_exp_exits[0]:
            early_exp_entries = np.concatenate([[trial_start], early_exp_entries])
        if early_exp_entries[-1] > early_exp_exits[-1]:
            early_exp_exits = np.concatenate([early_exp_exits, [trial_middle]])

    if len(bg_entries) != len(bg_exits):
        print()
    if len(exp_entries) != len(exp_exits):
        print()
    if len(early_exp_entries) != len(early_exp_exits):
        print()

    if len(exp_entries):
        if len(exp_exits) != len(exp_entries):
            print(
                f"Mismatch in exp_entries and exp_exits in trial {trial}. "
                f"exp_entries: {exp_entries}, exp_exits: {exp_exits}. "
                "Using clean_entries_exits to resolve."
            )
            exp_entries, exp_exits = clean_entries_exits(exp_entries, exp_exits)

    if len(bg_entries) != len(bg_exits):
        print(
            f"Mismatch in bg_entries and bg_exits in trial {trial}. "
            f"bg_entries: {bg_entries}, bg_exits: {bg_exits}. "
            "Using clean_entries_exits to resolve."
        )
        bg_entries, bg_exits = clean_entries_exits(bg_entries, bg_exits)

    return bg_entries, bg_exits, exp_entries, exp_exits, early_exp_entries, early_exp_exits


def clean_entries_exits(entries, exits):
    """
    Cleans mismatched entries and exits such that each entry is paired with the nearest valid exit.
    """
    valid_entries = []
    valid_exits = []
    e_idx, x_idx = 0, 0

    while e_idx < len(entries) and x_idx < len(exits):
        if entries[e_idx] < exits[x_idx]:  # Valid entry-exit pair
            valid_entries.append(entries[e_idx])
            valid_exits.append(exits[x_idx])
            e_idx += 1
            x_idx += 1  # Move to the next entry and exit
        else:
            x_idx += 1  # Skip unmatched exits

    return valid_entries, valid_exits

def percent_engaged(df):
    try:
        travel_time = .5
        blocks = df.phase.dropna().unique()
        blocks.sort()
        time_engaged = []
        block_time = []
        block_rewards = []

        for block in blocks:
            engaged = []
            all_time = []
            rewards = []
            block_trials = df[(df.value == 0) & (df.key == 'trial') & (df.phase == block)].trial
            for trial in block_trials:
                bg_entries, bg_exits, exp_entries, exp_exits, _, _ = get_entry_exit(df, trial)
                is_trial = df.trial == trial
                start = df.value == 1
                end = df.value == 0
                # port1 = df.port == 1
                # port2 = df.port == 2

                #
                trial_start = df[is_trial & start & (df.key == 'trial')].session_time.values[0]
                # trial_middle = df[is_trial & start & (df.key == 'LED') & port2].session_time.values[0]
                trial_end = df[is_trial & end & (df.key == 'trial')].session_time.values[0]
                #
                # bg_entries = df[is_trial & port2 & start & (df.key == 'head')].session_time.to_numpy()
                # bg_exits = df[is_trial & port2 & end & (df.key == 'head')].session_time.to_numpy()
                #
                # if len(bg_entries) == 0 or bg_entries[0] > bg_exits[0]:
                #     bg_entries = np.concatenate([[trial_start], bg_entries])
                # if trial_end - bg_entries[-1] < .1:
                #     bg_entries = bg_entries[:-1]
                # if len(bg_exits) == 0 or bg_entries[-1] > bg_exits[-1]:
                #     bg_entries = np.concatenate([bg_exits, [trial_middle]])
                #
                # if not (len(bg_entries) == len(bg_exits) and np.all(bg_exits - bg_entries > 0)):
                #     print('stop')
                # bg_engaged = sum(bg_exits - bg_entries)
                #
                # exp_entries = df[is_trial & port1 & start & (df.key == 'head') &
                #                  (df.session_time > trial_middle)].session_time.to_numpy()
                # exp_exits = df[is_trial & port1 & end & (df.key == 'head') &
                #                (df.session_time > trial_middle)].session_time.to_numpy()
                #
                # if len(exp_entries) == 0 and len(exp_exits) == 0:
                #     exp_engaged = 0
                # else:
                #     if len(exp_entries) == 0:
                #         exp_entries = np.concatenate([[trial_middle], exp_entries])
                #     if len(exp_exits) == 0:
                #         exp_exits = np.concatenate([exp_exits, [trial_end]])
                #
                #     if exp_entries[0] > exp_exits[0]:
                #         exp_entries = np.concatenate([[trial_middle], exp_entries])
                #     if exp_entries[-1] > exp_exits[-1]:
                #         exp_exits = np.concatenate([exp_exits, [trial_end]])
                #     exp_engaged = sum(exp_exits - exp_entries)
                #
                #     # if not len(exp_entries) == len(exp_exits) and len(exp_entries):
                #     #     print('stop')
                #     # if len(exp_entries):

                if len(exp_entries):
                    exp_engaged = sum([exit - entry for entry, exit in zip(exp_entries, exp_exits)])
                else:
                    exp_engaged = 0

                bg_engaged = sum([exit - entry for entry, exit in zip(bg_entries, bg_exits)])

                all_time.append(trial_end - trial_start)
                engaged.append(bg_engaged + exp_engaged)
                rewards.append(len(df[is_trial & start & (df.key == 'reward')]))

            time_engaged.append(sum(engaged) + travel_time * 2 * len(block_trials))
            block_time.append(sum(all_time))
            block_rewards.append(sum(rewards))
        engaged_df = pd.DataFrame()
        engaged_df['percent engaged'] = np.array(time_engaged) / np.array(block_time)
        engaged_df['block'] = blocks
        engaged_df['time engaged'] = time_engaged
        engaged_df['rewards earned'] = block_rewards
        engaged_df['reward rate'] = np.array(block_rewards) / np.array(time_engaged)

        return engaged_df
    except Exception as e:
        print ("Error in function.")
        raise


def reentry_index(df):
    bgportassignment = df.loc[df['key'] == 'background', 'port'].iloc[-1]
    expportassignment = df.loc[df['key'] == 'exp_decreasing', 'port'].iloc[-1]
    is_bg_exit = (df.port == bgportassignment) & (df.key == 'head') & (df.value == 0)
    phase_mode = df.groupby('trial').phase.agg(
        lambda s: s.iloc[-1] if (s.value_counts().get('0.4', 0) == 1 and s.value_counts().get('0.8', 0) == 1)
        else pd.Series.mode(s).iloc[-1]
    )

    is_low_block = (phase_mode == '0.4')
    is_high_block = (phase_mode == '0.8')
    num_ideal_bg_entry_low = len(np.unique(df.trial.dropna())[is_low_block])  # gets number of low block trials
    num_bg_entry_low = len(df.index[is_bg_exit & df.trial.isin(
        np.unique(df.trial.dropna())[is_low_block])])
    num_ideal_bg_entry_high = len(np.unique(df.trial.dropna())[is_high_block])  # gets number of high block trials
    num_bg_entry_high = len(df.index[is_bg_exit & df.trial.isin(
        np.unique(df.trial.dropna())[is_high_block])])

    reentry_index_low = num_bg_entry_low / num_ideal_bg_entry_low if num_ideal_bg_entry_low > 0 else 0
    reentry_index_high = num_bg_entry_high / num_ideal_bg_entry_high if num_ideal_bg_entry_high > 0 else 0
    reentry_df = pd.DataFrame()
    reentry_df['block'] = ['0.4', '0.8']
    reentry_df['bg_reentry_index'] = [reentry_index_low, reentry_index_high]
    return reentry_df


def add_h_lines(data=None, x=None, y=None, hue=None, ax=None, palette=None, estimator='mean'):
    days_back = 4
    palette = sns.color_palette(palette)
    for i, hue_key in enumerate(data[hue].unique()):
        df = data[data[hue] == hue_key]
        if df[x].max() > days_back:
            if estimator == 'median':
                hue_mean = df[(df[x] > df[x].max() - days_back)][y].median()
            else:
                hue_mean = df[(df[x] > df[x].max() - days_back)][y].mean()
            ax.hlines(hue_mean, df[x].max() - days_back, df[x].max(), palette[i], alpha=.5)


def merge_old_trials(session):
    print()
    return session


def simple_plots(select_mouse=None):
    plot_single_mouse_plots = True
    save_folder = "C:\\Users\\Shichen\\OneDrive - Johns Hopkins\\ShulerLab\\Rie_behavior\\summary_graphs"
    if select_mouse is None:
        dif = date.today() - start_date
        data = gen_data(get_today_filepaths(days_back=dif.days), select_mouse=select_mouse)
        info = gen_data(get_today_filepaths(days_back=dif.days), select_mouse=select_mouse, return_info=True)
    else:
        data = gen_data(get_today_filepaths(days_back=1000), select_mouse=select_mouse)
        info = gen_data(get_today_filepaths(days_back=1000), select_mouse=select_mouse, return_info=True)
    block_leaves_last10 = pd.DataFrame()
    for mouse in data.keys():
        if select_mouse is not None and mouse not in select_mouse:
            continue
        engaged = pd.DataFrame()
        consumption = pd.DataFrame()
        block_leaves = pd.DataFrame()
        reentry = pd.DataFrame()
        premature_leave = pd.DataFrame()

        for i, session in enumerate(data[mouse]):
            # if info[mouse][i]['task'] == 'multi_reward':
            #     continue
            try:
                session = merge_old_trials(session)

                engaged_df = percent_engaged(session)
                engaged_df['session'] = [i] * len(engaged_df)
                engaged = pd.concat([engaged, engaged_df])

                consumption_df = consumption_time(session)
                consumption_df['session'] = [i] * len(consumption_df)
                consumption = pd.concat([consumption, consumption_df])

                block_leaves_df = block_leave_times(session)
                block_leaves_df['session'] = [i] * len(block_leaves_df)
                block_leaves = pd.concat([block_leaves, block_leaves_df])

                reentry_df = reentry_index(session)
                reentry_df['session'] = [i] * len(reentry_df)
                reentry = pd.concat([reentry, reentry_df])

                premature_leave_df= calculate_premature_leave(session)
                premature_leave_df['session'] = [i] * len(premature_leave_df)
                premature_leave = pd.concat([premature_leave,premature_leave_df])

            except Exception as e:
                print(f"Error processing session {i} for mouse {mouse}: {e}")
                raise

        engaged.sort_values('block', inplace=True)
        block_leaves.sort_values('block', inplace=True)
        if plot_single_mouse_plots:
            fig, axes = plt.subplots(3, 2, figsize=[11, 8], layout="constrained")
            sns.lineplot(data=block_leaves.reset_index(), x='session', y='leave time', hue='block', style = 'block',markers=True, ax=axes[0, 0],
                         palette='Set2')
            add_h_lines(data=block_leaves.reset_index(), x='session', y='leave time', hue='block', ax=axes[0, 0],
                        palette='Set2')
            sns.lineplot(data=consumption.reset_index(), x='session', y='consumption time', hue='port', style = 'port', markers=True, ax=axes[0, 1],
                         palette='Set1', estimator=np.median)
            add_h_lines(data=consumption.reset_index(), x='session', y='consumption time', hue='port', ax=axes[0, 1],
                        palette='Set1', estimator='median')
            sns.lineplot(data=engaged.reset_index(), x='session', y='reward rate', hue='block', style = 'block', markers=True,ax=axes[1, 0],
                         palette='Set2')
            add_h_lines(data=engaged.reset_index(), x='session', y='reward rate', hue='block', ax=axes[1, 0],
                        palette='Set2')
            sns.lineplot(data=engaged.reset_index(), x='session', y='percent engaged', hue='block',style = 'block', markers=True, ax=axes[1, 1],
                         palette='Set2')
            add_h_lines(data=engaged.reset_index(), x='session', y='percent engaged', hue='block', ax=axes[1, 1],
                        palette='Set2')
            sns.lineplot(data=premature_leave.reset_index(), x='session', y='premature leave rate', hue='block', style = 'block',markers=True,ax=axes[2, 0],
                         palette='Set2')
            add_h_lines(data=premature_leave.reset_index(), x='session', y='premature leave rate', hue='block', ax=axes[2, 0],
                        palette='Set2')

            axes[2, 0].axhline(y=0.2, color='red', linestyle='--', linewidth=1.5, label='Threshold = 0.2')

            # Add legend to show the line label
            axes[2, 0].legend()

            axes[0, 0].set_title('Leave Time by Block')
            axes[0, 1].set_title('Consumption Time by Port')
            axes[1, 0].set_title('Reward Rate by Block')
            axes[1, 1].set_title('Percent Time Engaged by Block')
            axes[2, 0].set_title('Premature leave from BG port by Block')

            axes[0, 0].set_ylim([0, 20])
            axes[0, 1].set_ylim([0, 20])
            axes[1, 0].set_ylim([0, .65])
            axes[1, 1].set_ylim([0, 1])
            axes[2, 0].set_ylim([0, 1])
            plt.suptitle(mouse, fontsize=20)
            os.makedirs(save_folder, exist_ok=True)
            # Construct the filename
            filename = f'{mouse}_session_summary.png'
            save_path = os.path.join(save_folder, filename)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Graph saved to: {save_path}")
            plt.show()

        block_leaves_last10_df = block_leaves[(block_leaves.session >= block_leaves.session.max() - 10)].groupby('block')[
            'leave time'].mean().reset_index()
        block_leaves_last10_df['animal'] = mouse
        block_leaves_last10 = pd.concat([block_leaves_last10, block_leaves_last10_df])

    fig, axes = plt.subplots(1, 1)
    sns.boxplot(data=block_leaves_last10.reset_index(), x='block', y='leave time')

    plt.show()


def single_session(select_mouse=None, num_back=2):
    if select_mouse is None:
        dif = date.today() - start_date
        data = gen_data(get_today_filepaths(days_back=dif.days), select_mouse=select_mouse)
        info = gen_data(get_today_filepaths(days_back=dif.days), select_mouse=select_mouse, return_info=True)
    else:
        data = gen_data(get_today_filepaths(days_back=1000), select_mouse=select_mouse)
        info = gen_data(get_today_filepaths(days_back=1000), select_mouse=select_mouse, return_info=True)
    for mouse in data.keys():
        if select_mouse is not None and mouse not in select_mouse:
            continue
        for i in range(1, num_back + 1):
            last_session = data[mouse][-i]
            last_info = info[mouse][-i]
            session_summary(last_session, mouse, last_info)


# def session_summary(data, mouse, info):
#     base_save_folder= "C:\\Users\\riepo\\Experiment1\\graphs\\each_session"
#     save_folder = os.path.join(base_save_folder, mouse)
#     os.makedirs(save_folder, exist_ok=True)
#     fig, [ax1, ax2] = plt.subplots(1, 2, figsize=[10, 10])
#     port_palette = sns.color_palette('Set1')
#     block_palette = sns.color_palette('Set2')
#     start = data.value == 1
#     end = data.value == 0
#     head = data.key == 'head'
#     lick = data.key == 'lick'
#     reward = data.key == 'reward'
#     bgport = data.port == data.loc[data['key'] == 'background', 'port'].iloc[-1]
#     expport = data.port == data.loc[data['key'] == 'exp_decreasing', 'port'].iloc[-1]
#     # port1 = data.port == 1
#     # port2 = data.port == 2
#     # print(f"port2 is {port2}")
#     # print(f"bgport is {bgport}")
#     max_trial = data.trial.max()
#
#     bg_rectangles = []
#     exp_rectangles_in_bg = []
#     exp_rectangles = []
#     block1_rectangles = []
#     block2_rectangles = []
#     bg_reward_events = []
#     exp_reward_events = []
#     bg_lick_events = []
#     exp_lick_events = []
#     bg_lengths = []
#     exp_lengths = []
#     trial_blocks = data.groupby(['trial'])['phase'].agg(pd.Series.mode)
#     blocks = data.phase.dropna().unique()
#     blocks.sort()
#     for trial in data.trial.unique():
#         if np.isnan(trial):
#             continue
#         is_trial = data.trial == trial
#         try:
#             trial_start = data[is_trial & start & (data.key == 'trial')].session_time.values[0]
#             trial_middle = data[is_trial & end & (data.key == 'LED') & bgport].session_time.values[0]
#             trial_end = data[is_trial & end & (data.key == 'trial')].session_time.values[0]
#         except IndexError:
#             continue
#
#         bg_rewards = data[is_trial & start & bgport & reward].session_time.values
#         exp_rewards = data[is_trial & start & expport & reward].session_time.values
#         bg_licks = data[is_trial & start & lick & (data.session_time < trial_middle)].session_time.values
#         exp_licks = data[is_trial & start & lick & (data.session_time > trial_middle)].session_time.values
#
#         bg_lengths.append(trial_middle - trial_start)
#         exp_lengths.append(trial_end - trial_middle)
#
#         bg_entries, bg_exits, exp_entries, exp_exits, early_exp_entries, early_exp_exits = get_entry_exit(data, trial)
#         bg_intervals = list(zip(bg_entries, bg_exits))
#         exp_intervals = list(zip(exp_entries, exp_exits))
#         early_exp_intervals = list(zip(early_exp_entries, early_exp_exits))
#         for [s, e] in bg_intervals:
#             bg_rectangles.append(Rectangle((s - trial_start, trial), e - s, .7))
#         for [s, e] in early_exp_intervals:
#             exp_rectangles_in_bg.append(Rectangle((s - trial_start, trial), e - s, .7))
#         for [s, e] in exp_intervals:
#             exp_rectangles.append(Rectangle((s - trial_middle, trial), e - s, .7))
#         if np.where(blocks == trial_blocks.loc[trial])[0][0] == 0:
#             block1_rectangles.append(Rectangle((0, trial), 100, 1))
#         else:
#             block2_rectangles.append(Rectangle((0, trial), 100, 1))
#         bg_reward_events.append(bg_rewards - trial_start)
#         exp_reward_events.append(exp_rewards - trial_middle)
#         bg_lick_events.append(bg_licks - trial_start)
#         exp_lick_events.append(exp_licks - trial_middle)
#
#     alpha = .5
#     pc_b1 = PatchCollection(block1_rectangles, facecolors=block_palette[0], alpha=alpha)
#     pc_b2 = PatchCollection(block2_rectangles, facecolors=block_palette[1], alpha=alpha)
#     ax1.add_collection(pc_b1)
#     ax1.add_collection(pc_b2)
#     pc_b12 = PatchCollection(block1_rectangles, facecolors=block_palette[0], alpha=alpha)
#     pc_b22 = PatchCollection(block2_rectangles, facecolors=block_palette[1], alpha=alpha)
#     ax2.add_collection(pc_b12)
#     ax2.add_collection(pc_b22)
#
#     pc_bg = PatchCollection(bg_rectangles, edgecolor=port_palette[0], facecolor='w', alpha=1)
#     ax1.add_collection(pc_bg)
#
#     pc_exp_bg = PatchCollection(exp_rectangles_in_bg, edgecolor=port_palette[1], facecolor='w', alpha=1)
#     ax1.add_collection(pc_exp_bg)
#
#     pc_exp = PatchCollection(exp_rectangles, edgecolor=port_palette[1], facecolor='w', alpha=1)
#     ax2.add_collection(pc_exp)
#
#     offsets = np.array(list(range(len(bg_reward_events)))) + 1.4
#     ax1.eventplot(bg_reward_events, color='purple', linelengths=.62, lineoffsets=offsets)
#     offsets = np.array(list(range(len(exp_reward_events)))) + 1.4
#     ax2.eventplot(exp_reward_events, color='purple', linelengths=.62, lineoffsets=offsets)
#
#     light = [.8, .7, .8]
#     dark = [.2, .2, .2]
#     offsets = np.array(list(range(len(bg_lick_events)))) + 1.4
#     ax1.eventplot(bg_lick_events, color=light, linelengths=.25, lineoffsets=offsets)
#     offsets = np.array(list(range(len(exp_lick_events)))) + 1.4
#     ax2.eventplot(exp_lick_events, color=light, linelengths=.25, lineoffsets=offsets)
#
#     session_summary_axis_settings([ax1, ax2], max_trial)
#     plt.suptitle(f'{mouse}: {info["date"]} {info["time"]}')
#
#     # Construct the filename
#     filename = f'{mouse}_{info["date"]}_{info["time"]}.png'
#     save_path = os.path.join(save_folder, filename)
#
#     # Save the plot
#     plt.savefig(save_path, dpi=300, bbox_inches='tight')
#     print(f"Graph saved to: {save_path}")
#     plt.show()

def session_summary(data, mouse, info):
    base_save_folder= save_folder = "C:\\Users\\Shichen\\OneDrive - Johns Hopkins\\ShulerLab\\Rie_behavior\\each_session"
    save_folder = os.path.join(base_save_folder, mouse)
    os.makedirs(save_folder, exist_ok=True)
    fig, [ax1, ax2] = plt.subplots(1, 2, figsize=[10, 10])
    port_palette = sns.color_palette('Set1')
    block_palette = sns.color_palette('Set2')
    start = data.value == 1
    end = data.value == 0
    head = data.key == 'head'
    lick = data.key == 'lick'
    reward = data.key == 'reward'
    bgport = data.port == data.loc[data['key'] == 'background', 'port'].iloc[-1]
    expport = data.port == data.loc[data['key'] == 'exp_decreasing', 'port'].iloc[-1]
    max_trial = data.trial.max()

    bg_rectangles = []
    exp_rectangles_in_bg = []
    exp_rectangles = []
    block1_rectangles = []
    block2_rectangles = []
    bg_reward_events = []
    exp_reward_events = []
    bg_lick_events = []
    exp_lick_events = []
    bg_lengths = []
    exp_lengths = []
    trial_blocks = data.groupby(['trial'])['phase'].agg(pd.Series.mode)
    blocks = data.phase.dropna().unique()
    blocks.sort()
    for trial in data.trial.unique():
        if np.isnan(trial):
            continue
        is_trial = data.trial == trial
        try:
            trial_start = data[is_trial & start & (data.key == 'trial')].session_time.values[0]
            trial_middle = data[is_trial & end & (data.key == 'LED') & bgport].session_time.values[0]
            trial_end = data[is_trial & end & (data.key == 'trial')].session_time.values[0]
        except IndexError:
            continue

        bg_rewards = data[is_trial & start & bgport & reward].session_time.values
        exp_rewards = data[is_trial & start & expport & reward].session_time.values
        bg_licks = data[is_trial & start & lick & (data.session_time < trial_middle)].session_time.values
        exp_licks = data[is_trial & start & lick & (data.session_time > trial_middle)].session_time.values

        bg_lengths.append(trial_middle - trial_start)
        exp_lengths.append(trial_end - trial_middle)

        bg_entries, bg_exits, exp_entries, exp_exits, early_exp_entries, early_exp_exits = get_entry_exit(data, trial)
        bg_intervals = list(zip(bg_entries, bg_exits))
        exp_intervals = list(zip(exp_entries, exp_exits))
        early_exp_intervals = list(zip(early_exp_entries, early_exp_exits))
        for [s, e] in bg_intervals:
            bg_rectangles.append(Rectangle((s - trial_start, trial), e - s, .7))
        for [s, e] in early_exp_intervals:
            exp_rectangles_in_bg.append(Rectangle((s - trial_start, trial), e - s, .7))
        for [s, e] in exp_intervals:
            exp_rectangles.append(Rectangle((s - trial_middle, trial), e - s, .7))

        block_value = trial_blocks.loc[trial]
        if block_value == "0.4":
            block1_rectangles.append(Rectangle((0, trial), 100, 1))
        else:
            block2_rectangles.append(Rectangle((0, trial), 100, 1))

        bg_reward_events.append(bg_rewards - trial_start)
        exp_reward_events.append(exp_rewards - trial_middle)
        bg_lick_events.append(bg_licks - trial_start)
        exp_lick_events.append(exp_licks - trial_middle)

    alpha = .5
    pc_b1 = PatchCollection(block1_rectangles, facecolors=block_palette[0], alpha=alpha)
    pc_b2 = PatchCollection(block2_rectangles, facecolors=block_palette[1], alpha=alpha)
    ax1.add_collection(pc_b1)
    ax1.add_collection(pc_b2)
    pc_b12 = PatchCollection(block1_rectangles, facecolors=block_palette[0], alpha=alpha)
    pc_b22 = PatchCollection(block2_rectangles, facecolors=block_palette[1], alpha=alpha)
    ax2.add_collection(pc_b12)
    ax2.add_collection(pc_b22)

    pc_bg = PatchCollection(bg_rectangles, edgecolor=port_palette[0], facecolor='w', alpha=1)
    ax1.add_collection(pc_bg)

    pc_exp_bg = PatchCollection(exp_rectangles_in_bg, edgecolor=port_palette[1], facecolor='w', alpha=1)
    ax1.add_collection(pc_exp_bg)

    pc_exp = PatchCollection(exp_rectangles, edgecolor=port_palette[1], facecolor='w', alpha=1)
    ax2.add_collection(pc_exp)

    offsets = np.array(list(range(len(bg_reward_events)))) + 1.4
    ax1.eventplot(bg_reward_events, color='purple', linelengths=.62, lineoffsets=offsets)
    offsets = np.array(list(range(len(exp_reward_events)))) + 1.4
    ax2.eventplot(exp_reward_events, color='purple', linelengths=.62, lineoffsets=offsets)

    light = [.8, .7, .8]
    dark = [.2, .2, .2]
    offsets = np.array(list(range(len(bg_lick_events)))) + 1.4
    ax1.eventplot(bg_lick_events, color=light, linelengths=.25, lineoffsets=offsets)
    offsets = np.array(list(range(len(exp_lick_events)))) + 1.4
    ax2.eventplot(exp_lick_events, color=light, linelengths=.25, lineoffsets=offsets)

    session_summary_axis_settings([ax1, ax2], max_trial)
    plt.suptitle(f'{mouse}: {info["date"]} {info["time"]}')

    # Construct the filename
    filename = f'{mouse}_{info["date"]}_{info["time"]}.png'
    save_path = os.path.join(save_folder, filename)

    # Save the plot
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Graph saved to: {save_path}")
    plt.show()

def session_summary_axis_settings(axes, max_trial):
    for ax in axes:
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
        ax.get_yaxis().set_visible(False)
        ax.set_ylim([-1, max_trial + 1])
        ax.set_xlim([0, 30])
        ax.invert_yaxis()
        ax.set_ylabel('Trial')
        ax.set_xlabel('Time (sec)')



def simple_plots2(select_mouse=None):
    plot_single_mouse_plots = True
    save_folder = "C:\\Users\\Shichen\\OneDrive - Johns Hopkins\\ShulerLab\\Rie_behavior\\summary_graphs"

    #insert vertical line between stages or pre/post surgery
    stage_changes = {
        # "RK001": {"1->2": "2025-01-22", "2->3": "2025-01-31"},
        # "RK002": {"1->2": "2025-01-03", "2->3": "2025-03-14"},
        # "RK003": {"1->2": "2025-01-03", "2->3": "2025-01-22"},
        # "RK004": {"1->2": "2025-02-24", "2->3": "2025-03-05"},
        # "RK005": {"1->2": "2025-01-27", "2->3": "2025-01-31"},
        # "RK006": {"1->2": "2024-12-20", "2->3": "2025-02-26"},
        # "ES039": {"1->2": "2024-02-14", "2->3": None},
        # "ES045": {"1->2": "2024-04-24", "2->3": None},
        # "ES046": {"1->2": "2024-05-02", "2->3": None},
        # "ES047": {"1->2": "2024-04-24", "2->3": None},
        "RK001": {"1->2": "2025-04-13", "2->3": None}, #surgery date
        "RK002": {"1->2": "2025-04-13", "2->3": None},
        "RK003": {"1->2": "2025-04-13", "2->3": None},
        "RK004": {"1->2": "2025-03-30", "2->3": None},
        "RK005": {"1->2": "2025-03-30", "2->3": None},
        "RK006": {"1->2": "2025-03-30", "2->3": None}
    }

    if select_mouse is None:
        dif = date.today() - start_date
        data = gen_data(get_today_filepaths(days_back=dif.days), select_mouse=select_mouse)
        info = gen_data(get_today_filepaths(days_back=dif.days), select_mouse=select_mouse, return_info=True)
    else:
        data = gen_data(get_today_filepaths(days_back=1000), select_mouse=select_mouse)
        info = gen_data(get_today_filepaths(days_back=1000), select_mouse=select_mouse, return_info=True)
    block_leaves_last10 = pd.DataFrame()

    for mouse in data.keys():
        if select_mouse is not None and mouse not in select_mouse:
            continue

        # Initialize empty dataframes for aggregated data.
        engaged = pd.DataFrame()
        consumption = pd.DataFrame()
        block_leaves = pd.DataFrame()
        reentry = pd.DataFrame()
        premature_leave = pd.DataFrame()

        # Extract session dates
        session_dates = []
        for sess_info in info[mouse]:
            try:
                dt = datetime.strptime(sess_info['date'], "%Y-%m-%d")
                session_dates.append(dt)
            except Exception as e:
                print(f"Error parsing date in session info: {sess_info.get('date', None)}: {e}")

        for i, session in enumerate(data[mouse]):
            # if info[mouse][i]['task'] == 'multi_reward':
            #     continue
            try:
                session = merge_old_trials(session)

                engaged_df = percent_engaged(session)
                engaged_df['session'] = [i] * len(engaged_df)
                engaged = pd.concat([engaged, engaged_df])

                consumption_df = consumption_time(session)
                consumption_df['session'] = [i] * len(consumption_df)
                consumption = pd.concat([consumption, consumption_df])

                block_leaves_df = block_leave_times(session)
                block_leaves_df['session'] = [i] * len(block_leaves_df)
                block_leaves = pd.concat([block_leaves, block_leaves_df])

                reentry_df = reentry_index(session)
                reentry_df['session'] = [i] * len(reentry_df)
                reentry = pd.concat([reentry, reentry_df])

                premature_leave_df = calculate_premature_leave(session)
                premature_leave_df['session'] = [i] * len(premature_leave_df)
                premature_leave = pd.concat([premature_leave, premature_leave_df])

            except Exception as e:
                print(f"Error processing session {i} for mouse {mouse}: {e}")
                raise

        engaged.sort_values('block', inplace=True)
        block_leaves.sort_values('block', inplace=True)

        if plot_single_mouse_plots:
            fig, axes = plt.subplots(3, 2, figsize=[11, 8], layout="constrained")

            sns.lineplot(data=block_leaves.reset_index(), x='session', y='leave time',
                         hue='block', style='block', markers=True, ax=axes[0, 0], palette='Set2')
            add_h_lines(data=block_leaves.reset_index(), x='session', y='leave time',
                        hue='block', ax=axes[0, 0], palette='Set2')

            sns.lineplot(data=consumption.reset_index(), x='session', y='consumption time',
                         hue='port', style='port', markers=True, ax=axes[0, 1],
                         palette='Set1', estimator=np.median)
            add_h_lines(data=consumption.reset_index(), x='session', y='consumption time',
                        hue='port', ax=axes[0, 1], palette='Set1', estimator='median')

            sns.lineplot(data=engaged.reset_index(), x='session', y='reward rate',
                         hue='block', style='block', markers=True, ax=axes[1, 0], palette='Set2')
            add_h_lines(data=engaged.reset_index(), x='session', y='reward rate',
                        hue='block', ax=axes[1, 0], palette='Set2')

            sns.lineplot(data=engaged.reset_index(), x='session', y='percent engaged',
                         hue='block', style='block', markers=True, ax=axes[1, 1], palette='Set2')
            add_h_lines(data=engaged.reset_index(), x='session', y='percent engaged',
                        hue='block', ax=axes[1, 1], palette='Set2')

            sns.lineplot(data=premature_leave.reset_index(), x='session', y='premature leave rate',
                         hue='block', style='block', markers=True, ax=axes[2, 0], palette='Set2')
            add_h_lines(data=premature_leave.reset_index(), x='session', y='premature leave rate',
                        hue='block', ax=axes[2, 0], palette='Set2')

            axes[2, 0].axhline(y=0.2, color='red', linestyle='--', linewidth=1.5, label='Threshold = 0.2')
            axes[2, 0].legend()

            # Add vertical lines for stage changes (blue dashed lines)
            if mouse in stage_changes:
                for change, change_date_str in stage_changes[mouse].items():
                    if change_date_str is not None:
                        try:
                            change_date = datetime.strptime(change_date_str, "%Y-%m-%d")
                            idx = next((j for j, d in enumerate(session_dates) if d >= change_date), None)
                            if idx is not None and idx > 0:
                                pos = idx - 0.5
                                for ax in axes.flatten():
                                    ax.axvline(x=pos, color='blue', linestyle='--', linewidth=1.5)
                        except Exception as e:
                            print(f"Error processing stage change date {change_date_str} for mouse {mouse}: {e}")

            axes[0, 0].set_title('Leave Time by Block')
            axes[0, 1].set_title('Consumption Time by Port')
            axes[1, 0].set_title('Reward Rate by Block')
            axes[1, 1].set_title('Percent Time Engaged by Block')
            axes[2, 0].set_title('Premature leave from BG port by Block')

            axes[0, 0].set_ylim([0, 20])
            axes[0, 1].set_ylim([0, 20])
            axes[1, 0].set_ylim([0, 0.65])
            axes[1, 1].set_ylim([0, 1])
            axes[2, 0].set_ylim([0, 1])

            plt.suptitle(f"{mouse}", fontsize=20)
            os.makedirs(save_folder, exist_ok=True)
            filename = f'{mouse}_session_summary.png'
            save_path = os.path.join(save_folder, filename)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Graph saved to: {save_path}")
            plt.show()

            block_leaves_last10_df = block_leaves[(block_leaves.session >= block_leaves.session.max() - 10)]\
                .groupby('block')['leave time'].mean().reset_index()
            block_leaves_last10_df['animal'] = mouse
            block_leaves_last10 = pd.concat([block_leaves_last10, block_leaves_last10_df])

    fig, axes = plt.subplots(1, 1)
    sns.boxplot(data=block_leaves_last10.reset_index(), x='block', y='leave time')
    plt.show()

if __name__ == '__main__':
    mice = ['RK007','RK008','RK009','RK010']
    # mice = ['RK004']
    # mice = ['RK001', 'RK002','RK003','RK004','RK005','RK006','ES039', 'ES045','ES046','ES047','ES051', 'ES052', 'ES053']
    simple_plots2(mice) #history day by day summary statistics
    single_session(mice)  # most recent session when num_back = 0

