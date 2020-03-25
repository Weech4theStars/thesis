# driver for the Crazyflie choreo
# uses the spotipy client and primitives script to generate choreo

import primitives

import threading
import time
import json
from collections import namedtuple
from queue import Queue

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie.syncLogger import SyncLogger

# Time for one step in second
STEP_TIME = 1

# Possible commands, all times are in seconds
Takeoff = namedtuple('Takeoff', ['height', 'time'])
Land = namedtuple('Land', ['time'])
Goto = namedtuple('Goto', ['x', 'y', 'z', 'time'])
# Note: removed for now, since we don't have LEDs
# Ring = namedtuple('Ring', ['r', 'g', 'b', 'intensity', 'time'])
# RGB [0-255], Intensity [0.0-1.0]

# Reserved for the control loop, do not use in sequence
Quit = namedtuple('Quit', [])

uris = [
    'radio://0/10/2M/E7E7E7E701',  # cf_id 0
    'radio://0/10/2M/E7E7E7E702',  # cf_id 1
    'radio://0/10/2M/E7E7E7E703',  # cf_id 3
    'radio://0/10/2M/E7E7E7E704',  # cf_id 4
    'radio://0/10/2M/E7E7E7E705',  # cf_id 5
    'radio://0/10/2M/E7E7E7E706',  # cf_id 6
    'radio://0/10/2M/E7E7E7E707',  # cf_id 7
    'radio://0/10/2M/E7E7E7E708',  # cf_id 8
    'radio://0/10/2M/E7E7E7E709',  # cf_id 9
]

# populated in generate_sequence
sequence = []

def wait_for_position_estimator(scf):
    print('Waiting for estimator to find position...')

    # see: https://en.wikipedia.org/wiki/Kalman_filter
    log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
    log_config.add_variable('kalman.varPX', 'float')
    log_config.add_variable('kalman.varPY', 'float')
    log_config.add_variable('kalman.varPZ', 'float')

    var_y_history = [1000] * 10
    var_x_history = [1000] * 10
    var_z_history = [1000] * 10

    threshold = 0.001

    with SyncLogger(scf, log_config) as logger:
        for log_entry in logger:
            data = log_entry[1]

            var_x_history.append(data['kalman.varPX'])
            var_x_history.pop(0)
            var_y_history.append(data['kalman.varPY'])
            var_y_history.pop(0)
            var_z_history.append(data['kalman.varPZ'])
            var_z_history.pop(0)

            min_x = min(var_x_history)
            max_x = max(var_x_history)
            min_y = min(var_y_history)
            max_y = max(var_y_history)
            min_z = min(var_z_history)
            max_z = max(var_z_history)

            # print("{} {} {}".
            #       format(max_x - min_x, max_y - min_y, max_z - min_z))

            if (max_x - min_x) < threshold and (
                    max_y - min_y) < threshold and (
                    max_z - min_z) < threshold:
                break


def reset_estimator(scf):
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')
    wait_for_position_estimator(scf)


def activate_high_level_commander(scf):
    scf.cf.param.set_value('commander.enHighLevel', '1')


def activate_mellinger_controller(scf, use_mellinger):
    controller = 1
    if use_mellinger:
        controller = 2
    scf.cf.param.set_value('stabilizer.controller', str(controller))


def set_ring_color(cf, r, g, b, intensity, time):
    cf.param.set_value('ring.fadeTime', str(time))

    r *= intensity
    g *= intensity
    b *= intensity

    color = (int(r) << 16) | (int(g) << 8) | int(b)

    cf.param.set_value('ring.fadeColor', str(color))


def crazyflie_control(scf):
    cf = scf.cf
    control = controlQueues[uris.index(cf.link_uri)]

    activate_mellinger_controller(scf, True)

    commander = scf.cf.high_level_commander

    # Set fade to color effect and reset to Led-ring OFF
    # set_ring_color(cf, 0, 0, 0, 0, 0)
    # cf.param.set_value('ring.effect', '14')

    while True:
        command = control.get()
        if type(command) is Quit:
            return
        elif type(command) is Takeoff:
            commander.takeoff(command.height, command.time)
        elif type(command) is Land:
            commander.land(0.0, command.time)
        elif type(command) is Goto:
            commander.go_to(command.x, command.y, command.z, 0, command.time)
        elif type(command) is Ring:
            set_ring_color(cf, command.r, command.g, command.b,
                           command.intensity, command.time)
            pass
        else:
            print('Warning! unknown command {} for uri {}'.format(command,
                                                                  cf.uri))

def control_thread():
    pointer = 0
    step = 0
    stop = False

    while not stop:
        print('Step {}:'.format(step))
        while sequence[pointer][0] <= step:
            cf_id = sequence[pointer][1]
            command = sequence[pointer][2]

            print(' - Running: {} on {}'.format(command, cf_id))
            controlQueues[cf_id].put(command)
            pointer += 1

            if pointer >= len(sequence):
                print('Reaching the end of the sequence, stopping!')
                stop = True
                break

        step += 1
        time.sleep(STEP_TIME)

    for ctrl in controlQueues:
        ctrl.put(Quit())


def add_primitive(step, start, duration):
    # TODO: add logic for selecting primitives based off audio analysis
    primitive = primitives.kickline
    basic_duration = primitive[-1][0]
    incr = primitive[0][0] * (duration / basic_duration)
    for movement in primitive:
        # TODO: add clause to make sure crazyflie isn't moving faster
        # than its max speed
        if (movement[0] * duration) / basic_duration > incr:
            incr = movement[0] * (duration / basic_duration)
        goto = (movement[2][0], movement[2][1], movement[2][2], movement[2][3] * (duration / basic_duration))
        move = (step + incr, movement[1], goto)
        sequence.append(move)
    step += incr
    return step

# uses "Section" information in the audio analysis to transition primitives
def generate_sequence(analysis):
    sections = analysis['sections']
    step = 0
    for section in sections:
        step = add_primitive(step, section['start'], section['duration'])
    for move in sequence:
        print(move)
        print('\n')


if __name__ == '__main__':
    # read in audio_analysis
    analysis_file = open('audio_analysis.json', 'r')
    analysis = json.load(analysis_file)

    # TODO: no collision avoidance in this sequence generation
    generate_sequence(analysis)

    controlQueues = [Queue() for _ in range(len(uris))]


    # control sequence commented out to test non-flight code

    # cflib.crtp.init_drivers(enable_debug_driver=False)
    # factory = CachedCfFactory(rw_cache='./cache')
    # with Swarm(uris, factory=factory) as swarm:
    #    swarm.parallel_safe(activate_high_level_commander)
    #    swarm.parallel_safe(reset_estimator)

    #    print('Starting sequence!')

    #    threading.Thread(target=control_thread).start()

    #    swarm.parallel_safe(crazyflie_control)

    #    time.sleep(1)
