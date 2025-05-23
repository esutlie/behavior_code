from support_classes import *
# from tasks import *
from tasks_RK import multireward_task
from timescapes import *
import random


# def give_up(session, reward_level, peak_time, session_length):
#     print(reward_level)
#     print(peak_time)
#     print(session_length)
#     exp_dist = {'distribution': lin_over_ex,
#                 'cumulative': reward_level,
#                 'peak_time': peak_time}
#     port_1 = Port(1, dist_info=exp_dist)
#     port_2 = Port(2, dist_info=exp_dist)
#     ports = [port_1, port_2]
#     task1 = Task(session, name='give_up', structure=give_up_task, ports=ports, maximum=session_length, limit='time')
#     session.start([task1])


# def give_up_forgo(session, reward_level, starting_prob, session_length, fixed_times):
#     print(reward_level)
#     print(starting_prob)
#     print(session_length)
#     exp_dist = {'distribution': exp_decreasing,
#                 'cumulative': reward_level,
#                 'staring_probability': starting_prob}
#     background_dist = {'distribution': fixed_single,
#                        'delays': fixed_times}
#     dists = [exp_dist, background_dist]
#     # dists = [background_dist, exp_dist]
#     port_1 = Port(1, dist_info=dists[0])
#     port_2 = Port(2, dist_info=dists[1])
#     task1 = Task(session, name='give_up_forgo', structure=give_up_forgo_task, ports=[port_1, port_2],
#                  maximum=session_length, limit='time')
#     session.start([task1])


def multi_reward(session, reward_level, starting_prob, session_length, swap_port=False, swap_block = False):
    print(reward_level)
    print(starting_prob)
    print(session_length)
    task_structure = multireward_task

    # rates = [.4, .8, .4, .8, .4, .8]
    # if np.random.random() > .5:
    #     rates.reverse()

    # rates = [.4, .8] #swap_block random is session by session change, swap block trial is trial by trial change
    if swap_block == "random":
        rates = [random.choice([0.4, 0.8])]
        print (rates)
    elif swap_block == "trial":
        rates = [.4, .8, .4, .8, .4, .8]
        if np.random.random() > .5:
            rates.reverse()
    else:
        rates = [0.4] if not swap_block else [0.8] #0.4 if swap_block is false, 0.8 if true
    #     rates.reverse()

    exp_port = 1 if not swap_port else 2
    bg_port = 2 if not swap_port else 1
    print(f'exp_port = {exp_port}')
    print(f'bg_port = {bg_port}')
    background_dist = {'distribution': 'background',
                       'rates': rates,
                       'duration': 5,
                       'port_num': bg_port}
    print(background_dist['rates'])
    exp_dist = {'distribution': exp_decreasing,
                'cumulative': reward_level,
                'starting_probability': starting_prob,
                'port_num': exp_port}
    ports = {'exp': Port(exp_dist['port_num'], dist_info=exp_dist),
             'background': Port(background_dist['port_num'], dist_info=background_dist)}
    task1 = Task(session, name='multi_reward', structure=task_structure, ports=ports,
                 maximum=session_length, limit='time')
    session.start([task1])


def single_reward(session, reward_level, starting_prob, session_length, swap_port=False, swap_block= False):
    reward_level = 0.5994974874371859  # cumulative for an 8 reward version
    starting_prob = 0.1301005025125628
    print(reward_level)
    print(starting_prob)
    print(session_length)
    task_structure = single_reward_task
    
    task_name = 'single_reward'
    
    rates = [.4, .8, .4, .8, .4, .8]
    if np.random.random() > .5:
        rates.reverse()
    exp_port = 1 if not swap_port else 2
    bg_port = 2 if not swap_port else 1
    background_dist = {'distribution': 'background',
                   'rates': rates,
                   'duration': 5,
                   'port_num': bg_port}
    print(background_dist['rates'])
    exp_dist = {'distribution': exp_decreasing,
            'cumulative': reward_level,
            'starting_probability': starting_prob,
            'port_num': exp_port}
    ports = {'exp': Port(exp_dist['port_num'], dist_info=exp_dist),
         'background': Port(background_dist['port_num'], dist_info=background_dist)}
    task1 = Task(session, name=task_name, structure=task_structure, ports=ports,
             maximum=session_length, limit='time')
    session.start([task1])

# def give_up_blocked(session, reward_level, starting_prob, session_length, forgo=True, forced_trials=False):
#     task_structure = give_up_blocked_task
#     task_name = 'give_up_blocked'
#
#     blocks = ['hi_hi', 'hi_lo', 'lo_hi', 'lo_lo']
#     # order = [1, 0, 2, 3]
#     # blocks = [blocks[i] for i in order]
#     random.shuffle(blocks)
#     print(blocks)
#     exp_dist = {'distribution': exp_decreasing,
#                 'blocks': blocks,
#                 'cumulative': 4,
#                 'starting': 1,
#                 'hi': 1,
#                 'lo': .8}
#     ports = {'right': Port(1, dist_info=exp_dist),
#              'left': Port(2, dist_info=exp_dist)}
#     task1 = Task(session, name=task_name, structure=task_structure, ports=ports,
#                  maximum=session_length, limit='time', forgo=forgo, forced_trials=forced_trials)
#     session.start([task1])


# def main(mouse, to_run, forgo=False, forced_trials=False, swap_port=False):
def main(mouse, to_run, swap_port=False, swap_block = False): #swap port swaps BG/EXP, swap_block is the stage
    cumulative = 8
    start_prob = 1
    session_time = 18
    mouse_settings = {
        'testmouse': [cumulative, start_prob, session_time],
        'default': [cumulative, start_prob, session_time],  # reward level, starting prop, session time, [intervals].
    }

    session = Session(mouse)  # Start a new session for the mouse

    try:
        if mouse not in mouse_settings.keys():
            to_run(session, *mouse_settings['default'], swap_port=swap_port, swap_block=swap_block)  # Run the task
        else:
            to_run(session, *mouse_settings[mouse], swap_port=swap_port, swap_block=swap_block)  # Run the task
        session.smooth_finish = True
        print('smooth finish')
    except KeyboardInterrupt:  # Catch if the task is stopped via ctrl-C or the stop button
        session.halted = True
    finally:
        session.end()


if __name__ == "__main__":
    # main('testmouse', cued_forgo, forgo=False, forced_trials=True)
    # main('ES024', cued_forgo, forgo=False, forced_trials=True)
    main('ES030', multi_reward)
    # main('testmouse', give_up_blocked)

