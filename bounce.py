## get those drones bouncing to the beat ##

import threading
import time
from collections import namedtuple
from multiprocessing import Queue

import cflib.crtp
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie.syncLogger import SyncLogger

# Time for one step in a tenth of a second (won't do beats that are shorter)
STEP_TIME = 0.1

# generated using the beats from the specific spotify song
sequence = []

# Possible commands, all times are in seconds
Takeoff = namedtuple('Takeoff', ['height', 'time'])
Land = namedtuple('Land', ['time'])
Goto = namedtuple('Goto', ['x', 'y', 'z', 'time'])
# Reserved for the control loop, do not use in sequence
Quit = namedtuple('Quit', [])

# URIs of each of the drones. Add more if desired
uris = [
    'radio://0/10/2M/E7E7E7E701',  # cf_id 0, startup position [-0.5, -0.5]
    'radio://0/10/2M/E7E7E7E702',  # cf_id 1, startup position [ 0, 0]
    'radio://0/10/2M/E7E7E7E703',  # cf_id 3, startup position [0.5, 0.5]
]

def generate_sequence(beats):
    for beat in beats:
        print(beat["start"], beat["duration"])

        timestep = beat["duration"] / 2
        # rise for half the beat
        for uri in uris:
            step = (beat["start"], uri, Goto(.1, .1, .5, timestep))
            sequence.append(step)

        # descend for other half of the beat
        for uri in uris:
            step = (beat["start"] + timestep, uri, Goto(.1, .1, .3, timestep))

        # print beats
        print(beat["start"], beat["duration"])

    # print(sequence)


if __name__ == '__main__':
    controlQueues = [Queue() for _ in range(len(uris))]

    cflib.crtp.init_drivers(enable_debug_driver=False)
    factory = CachedCfFactory(rw_cache='./cache')
    with Swarm(uris, factory=factory) as swarm:
        swarm.parallel_safe(activate_high_level_commander)
        swarm.parallel_safe(reset_estimator)

        print('Starting sequence!')

        threading.Thread(target=control_thread).start()

        swarm.parallel_safe(crazyflie_control)

        time.sleep(1)
