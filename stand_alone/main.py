from support_classes import *
from tasks import *
from timescapes import *
import random


def give_up(session, reward_level, peak_time, session_length):
    print(reward_level)
    print(peak_time)
    print(session_length)
    exp_dist = {'distribution': lin_over_ex,
                'cumulative': reward_level,
                'peak_time': peak_time}
    port_1 = Port(1, dist_info=exp_dist)
    port_2 = Port(2, dist_info=exp_dist)
    ports = [port_1, port_2]
    task1 = Task(session, name='give_up', structure=give_up_task, ports=ports, maximum=session_length, limit='time')
    session.start([task1])


def give_up_forgo(session, reward_level, starting_prob, session_length, fixed_times):
    print(reward_level)
    print(starting_prob)
    print(session_length)
    exp_dist = {'distribution': exp_decreasing,
                'cumulative': reward_level,
                'staring_probability': starting_prob}
    background_dist = {'distribution': fixed_single,
                       'delays': fixed_times}
    dists = [exp_dist, background_dist]
    # dists = [background_dist, exp_dist]
    port_1 = Port(1, dist_info=dists[0])
    port_2 = Port(2, dist_info=dists[1])
    task1 = Task(session, name='give_up_forgo', structure=give_up_forgo_task, ports=[port_1, port_2],
                 maximum=session_length, limit='time')
    session.start([task1])


def cued_forgo(session, reward_level, starting_prob, session_length, training=False, forced_trials=False):
    print(reward_level)
    print(starting_prob)
    print(session_length)
    task_structure = cued_forgo_task

    if training:
        task_name = 'training_cued_forgo'
        print('cued forgo training')
    else:
        task_name = 'cued_forgo'
        print('cued forgo')

    if forced_trials:
        task_name = task_name + '_forced'
        print('forced trials included')

    rates = [.4, .8, .4, .8, .4, .8]
    if np.random.random() > .5:
        rates.reverse()
    background_dist = {'distribution': 'background',
                       'rates': rates,
                       'duration': 5,
                       'port_num': 2}
    print(background_dist['rates'])
    exp_dist = {'distribution': exp_decreasing,
                'cumulative': reward_level,
                'starting_probability': starting_prob,
                'port_num': 1}
    ports = {'exp': Port(exp_dist['port_num'], dist_info=exp_dist),
             'background': Port(background_dist['port_num'], dist_info=background_dist)}
    task1 = Task(session, name=task_name, structure=task_structure, ports=ports,
                 maximum=session_length, limit='time', training=training, forced_trials=forced_trials)
    session.start([task1])


def give_up_blocked(session, reward_level, starting_prob, session_length, training=False, forced_trials=False):
    task_structure = give_up_blocked_task
    task_name = 'give_up_blocked'

    blocks = ['hi_hi', 'hi_lo', 'lo_hi', 'lo_lo']
    # order = [1, 0, 2, 3]
    # blocks = [blocks[i] for i in order]
    random.shuffle(blocks)
    print(blocks)
    exp_dist = {'distribution': exp_decreasing,
                'blocks': blocks,
                'cumulative': 4,
                'starting': 1,
                'hi': 1,
                'lo': .8}
    ports = {'right': Port(1, dist_info=exp_dist),
             'left': Port(2, dist_info=exp_dist)}
    task1 = Task(session, name=task_name, structure=task_structure, ports=ports,
                 maximum=session_length, limit='time', training=training, forced_trials=forced_trials)
    session.start([task1])


def main(mouse, to_run, training=False, forced_trials=False):
    cumulative = 3
    start_prob = 1
    session_time = 18
    mouse_settings = {
        'testmouse': [cumulative, start_prob, session_time],
        'ES024': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
        'ES025': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
        'ES026': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
        'ES027': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
        'ES028': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
        'ES029': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
        # 'ES021': [0, 0, session_time],  # skip, skip, session time
        # 'ES022': [0, 0, session_time],  # skip, skip, session time
        # 'ES023': [0, 0, session_time],  # skip, skip, session time
    }

    if mouse not in mouse_settings.keys():
        raise MouseSettingsError('This mouse isn\'t defined in the settings')
    session = Session(mouse)  # Start a new session for the mouse

    try:
        to_run(session, *mouse_settings[mouse], training=training, forced_trials=forced_trials)  # Run the task
        session.smooth_finish = True
        print('smooth finish')
    except KeyboardInterrupt:  # Catch if the task is stopped via ctrl-C or the stop button
        session.halted = True
    finally:
        session.end()


if __name__ == "__main__":
    # main('testmouse', cued_forgo, training=False, forced_trials=True)
    # main('ES024', cued_forgo, training=False, forced_trials=True)
    main('ES027', cued_forgo, training=False, forced_trials=True)
    # main('testmouse', give_up_blocked)

    # scp -r C:\Users\Elissa\GoogleDrive\Code\Python\behavior_code\stand_alone pi@rebekahpi:\home\pi
    # sudo chmod u+w -r stand_alone
