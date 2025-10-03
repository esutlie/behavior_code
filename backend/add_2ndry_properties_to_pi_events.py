import numpy as np
import pandas as pd
from .get_interlocked_arrays import get_interlocked_arrays


def identify_event_order(pi_events, col_name_to_add, condition):
    pi_events[col_name_to_add] = np.NaN
    for tr in range(1, pi_events.total_trial + 1):
        all_condition_bg = (pi_events.trial == tr) & condition & (pi_events.port == pi_events.loc[pi_events['key'] == 'background', 'port'].iloc[-1])
        all_condition_exp = (pi_events.trial == tr) & condition & (pi_events.port == pi_events.loc[pi_events['key'] == 'exp_decreasing', 'port'].iloc[-1])
        pi_events[col_name_to_add].loc[all_condition_bg] = range(1, len(pi_events.index[all_condition_bg]) + 1)
        pi_events[col_name_to_add].loc[all_condition_exp] = range(1, len(pi_events.index[all_condition_exp]) + 1)


def get_valid_entry_exit(pi_events):
    def update_trial_validity(valid_trials):
        nonlocal exp_entries, exp_exits, bg_entries, bg_exits
        exp_entries = exp_entries[exp_entries.trial.isin(valid_trials)]
        exp_exits = exp_exits[exp_exits.trial.isin(valid_trials)]
        bg_entries = bg_entries[bg_entries.trial.isin(valid_trials)]
        bg_exits = bg_exits[bg_exits.trial.isin(valid_trials)]

    pi_events['is_valid_trial'] = True
    reward_trials = pi_events[(pi_events.key == 'reward_initiate')].trial.to_numpy()
    non_reward = ~pi_events.trial.isin(reward_trials)
    bg_end_times = pi_events[(pi_events.key == 'LED') & (pi_events.port == pi_events.loc[pi_events['key'] == 'background', 'port'].iloc[-1]) & (pi_events.value == 1)]

    exp_entries = pi_events[(pi_events.key == 'head') & (pi_events.value == 1) & (pi_events.port == pi_events.loc[pi_events['key'] == 'exp_decreasing', 'port'].iloc[-1])]
    exp_exits = pi_events[(pi_events.key == 'head') & (pi_events.value == 0) & (pi_events.port == pi_events.loc[pi_events['key'] == 'exp_decreasing', 'port'].iloc[-1])]
    bg_entries = pi_events[(pi_events.key == 'trial') & (pi_events.value == 1)]
    bg_exits = pi_events[(pi_events.key == 'head') & (pi_events.value == 0) & (pi_events.port == pi_events.loc[pi_events['key'] == 'background', 'port'].iloc[-1])]

    vid_bg_entries, vid_exp_exits = get_interlocked_arrays(bg_entries.index.to_numpy(), exp_exits.index.to_numpy(),
                                                           direction='widest')

    # find the latest bg_exits in between each pair of bg_entry and exp_exit
    bgx_bgn = np.subtract.outer(bg_exits.index.to_numpy(), vid_bg_entries)
    expx_bgx = np.subtract.outer(vid_exp_exits, bg_exits.index.to_numpy())
    vid_bg_exits = np.empty(np.shape(vid_bg_entries))
    for i in range(len(vid_bg_entries)):
        interval_l = bgx_bgn[:, i]
        interval_r = expx_bgx[i, :]
        bgx_element_avail = np.where(np.multiply(interval_l > 0, interval_r > 0) > 0)[0]
        if bgx_element_avail.size == 0:
            vid_bg_exit_to_take = np.nan
        else:
            bgx_element_to_take = bgx_element_avail.max()
            vid_bg_exit_to_take = bg_exits.index.to_numpy()[bgx_element_to_take]
        vid_bg_exits[i] = vid_bg_exit_to_take
    vid_bg_entries = np.delete(vid_bg_entries, np.isnan(vid_bg_exits))
    vid_exp_exits = np.delete(vid_exp_exits, np.isnan(vid_bg_exits))
    vid_bg_exits = np.delete(vid_bg_exits, np.isnan(vid_bg_exits))

    # find the exp_entries in between each pair of bg_exit and exp_exit
    expn_bgx = np.subtract.outer(exp_entries.index.to_numpy(), vid_bg_exits)
    expx_expn = np.subtract.outer(vid_exp_exits, exp_entries.index.to_numpy())
    vid_exp_entries = np.empty(np.shape(vid_bg_exits))
    for i in range(len(vid_bg_exits)):
        interval_l = expn_bgx[:, i]
        interval_r = expx_expn[i, :]
        expn_element_avail = np.where(np.multiply(interval_l > 0, interval_r > 0))[0]
        if expn_element_avail.size == 0:
            vid_exp_entry_to_take = np.nan
        else:
            expn_element_to_take = expn_element_avail.min()
            vid_exp_entry_to_take = exp_entries.index.to_numpy()[expn_element_to_take]
        vid_exp_entries[i] = vid_exp_entry_to_take
    vid_bg_entries = np.delete(vid_bg_entries, np.isnan(vid_exp_entries))
    vid_bg_exits = np.delete(vid_bg_exits, np.isnan(vid_exp_entries))
    vid_exp_exits = np.delete(vid_exp_exits, np.isnan(vid_exp_entries))
    vid_exp_entries = np.delete(vid_exp_entries, np.isnan(vid_exp_entries))

    pi_events['is_valid'] = False
    pi_events.loc[vid_exp_entries, 'is_valid'] = True
    pi_events.loc[vid_exp_exits, 'is_valid'] = True
    pi_events.loc[vid_bg_entries, 'is_valid'] = True
    pi_events.loc[vid_bg_exits, 'is_valid'] = True
    # region only get the trials where there are both an exp_entry and an exp_exit
    complete_trials = set(exp_entries.trial) & set(exp_exits.trial) & set(bg_entries.trial) & set(bg_exits.trial)
    update_trial_validity(complete_trials)
    # endregion
    # region valid trial condition 1: toss trials with multiple re-entry into the exponential port
    # # but skip this step when it's a single-reward task
    # if (pi_events['task'].iloc[0] != 'single_reward'):
    #     is_minimal_reentry = exp_entries.groupby('trial').entry_order_in_trial.max() <= 2
    #     single_entry_trials = is_minimal_reentry[is_minimal_reentry].index
    #     update_trial_validity(single_entry_trials)
    #     pi_events.is_valid_trial[~pi_events['trial'].isin(single_entry_trials)] = False
    # endregion
    # region valid trial condition 2: toss trials with background stay too long
    bg_stay = bg_exits.groupby('trial').trial_time.max()
    trial_phase = bg_exits.groupby('trial').phase.max()
    good_for_long_block = (trial_phase == '0.4') & (bg_stay < 25)
    good_for_short_block = (trial_phase == '0.8') & (bg_stay < 12.5)
    good_bg_stay = good_for_long_block | good_for_short_block
    good_bg_trials = good_bg_stay[good_bg_stay].index
    update_trial_validity(good_bg_trials)
    pi_events.loc[~pi_events['trial'].isin(good_bg_trials), 'is_valid_trial'] = False
    for trial in trial_phase.index.to_list():
        pi_events.loc[pi_events.trial == trial, 'phase'] = trial_phase.loc[trial]
    # endregion
    valid_trials = np.unique(pi_events.trial[pi_events.is_valid_trial])
    bg_entries_idx = [bg_entries.groupby('trial').groups[i].max() for i in valid_trials]
    bg_exits_idx = [bg_exits.groupby('trial').groups[i].max() for i in valid_trials]
    exp_entries_idx = [exp_entries.groupby('trial').groups[i].max() for i in valid_trials]
    exp_exits_idx = [exp_exits.groupby('trial').groups[i].max() for i in valid_trials]
    bg_entries = bg_entries.session_time.to_numpy()
    bg_exits = bg_exits.groupby('trial').session_time.max().to_numpy()
    exp_entries = exp_entries.session_time.to_numpy()
    exp_exits = exp_exits.session_time.to_numpy()

    return pi_events, valid_trials, exp_entries, exp_exits, bg_entries, bg_exits


def add_2ndry_properties_to_pi_events(pi_events):
    pd.options.mode.chained_assignment = None  # default='warn'
    pi_events.total_trial = int(pi_events.trial.max())
    # region Identify the order of rewards, entries, and exits in each trial
    identify_event_order(pi_events, 'reward_order_in_trial',
                         condition=(pi_events.key == 'reward') & (pi_events.value == 1))
    identify_event_order(pi_events, 'entry_order_in_trial',
                         condition=(pi_events.key == 'head') & (pi_events.value == 1))
    identify_event_order(pi_events, 'exit_order_in_trial',
                         condition=(pi_events.key == 'head') & (pi_events.value == 0))
    # endregion

    # region Identify the animal's first encounters of each reward
    pi_events['is_1st_lick'] = 0
    pi_events['is_1st_encounter'] = 0
    reward_idx = pi_events.index[(pi_events.key == 'reward') & (pi_events.value == 1)]
    for i in range(len(reward_idx)):
        idx = reward_idx[i]
        if i + 1 >= len(reward_idx):
            next_idx = max(pi_events.index)
        else:
            next_idx = reward_idx[i + 1]
        isafter = pi_events.index > idx
        islick = pi_events.key == 'lick'
        if pi_events[isafter & islick & (pi_events.value == 1)].empty:
            print('')
        else:
            first_lick_idx = pi_events[isafter & islick & (pi_events.value == 1)].index[0]
            pi_events.is_1st_lick[first_lick_idx] = 1

        if pi_events[isafter & islick].empty:
            print('')
        elif (pi_events.value[isafter & islick].iloc[0] == 0) & (pi_events.index[isafter & islick].min() < next_idx):
            pi_events.is_1st_encounter[idx] = 1
        elif pi_events.value[isafter & islick].iloc[0] == 1:
            idx_to_change = pi_events[isafter & islick].index[0]
            pi_events.is_1st_encounter[idx_to_change] = 1
    pi_events['is_1st_lick'] = pi_events['is_1st_lick'].astype(bool)
    pi_events['is_1st_encounter'] = pi_events['is_1st_encounter'].astype(bool)
    # endregion
    pi_events, valid_trials, exp_entries, exp_exits, bg_entries, bg_exits = get_valid_entry_exit(pi_events)

    pi_events.reset_index(drop=True, inplace=True)

    # region Identify interval from last entry (time they are in the port)
    pi_events['time_in_port'] = np.nan
    condition_entering_bg = (pi_events['key'] == 'trial') & (pi_events['value'] == 1)
    condition_exiting_bg = (pi_events['key'] == 'head') & (pi_events['value'] == 0) & (pi_events.port == pi_events.loc[pi_events['key'] == 'background', 'port'].iloc[-1])
    condition_entering_exp = (pi_events['key'] == 'head') & (pi_events['value'] == 1) & (pi_events.port == pi_events.loc[pi_events['key'] == 'exp_decreasing', 'port'].iloc[-1])
    condition_exiting_exp = (pi_events['key'] == 'head') & (pi_events['value'] == 0) & (pi_events.port == pi_events.loc[pi_events['key'] == 'exp_decreasing', 'port'].iloc[-1])
    for i in range(1, pi_events.total_trial+1):
        is_in_trial = pi_events.trial == i
        time_entering_bg = pi_events.loc[is_in_trial & pi_events.is_valid & condition_entering_bg, 'session_time']
        time_exiting_bg = pi_events.loc[is_in_trial & pi_events.is_valid & condition_exiting_bg, 'session_time']
        if (time_entering_bg.size > 0) & (time_exiting_bg.size > 0):
            idx_list_bg = range(time_entering_bg.index[0], time_exiting_bg.index[0]+1)
            time_in_bg = [pi_events.loc[idx, 'session_time'] - time_entering_bg.values[0] for idx in idx_list_bg]
            pi_events.loc[idx_list_bg, 'time_in_port'] = time_in_bg
        time_entering_exp = pi_events.loc[is_in_trial & pi_events.is_valid & condition_entering_exp, 'session_time']
        time_exiting_exp = pi_events.loc[is_in_trial & pi_events.is_valid & condition_exiting_exp, 'session_time']
        if (time_entering_exp.size > 0) & (time_exiting_exp.size > 0):
            idx_list_exp = range(time_entering_exp.index[0], time_exiting_exp.index[0]+1)
            time_in_exp = [pi_events.loc[idx, 'session_time'] - time_entering_exp.values[0] for idx in idx_list_exp]
            pi_events.loc[idx_list_exp, 'time_in_port'] = time_in_exp
    # endregion
    return pi_events
