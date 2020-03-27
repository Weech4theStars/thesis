# all 10 motion primitives are contained in this file
# each sequence takes a variable amount of time
# each sequence assumes flying nine Crazyflie 2.1s

import threading
import time
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

    ##### PRIMITIVES #####

#### ROTATING TOWER
# tower comprised of a square base, a smaller square above the square base,
# and a crowning drone. The two squares rotate as the crowning drone remains
# still
x_mid = 0.4
x_base = 0.8
z_top = 1.5
z_mid = 1
z_base = 0.5
rotating_tower = [
    ( 0,    8,      Goto(0, 0, z_top, 2.5)),

    ( 0,    0,      Goto(x_base, -x_base, z_base, 2.5)),
    ( 0,    1,      Goto(-x_base, -x_base, z_base, 2.5)),
    ( 0,    2,      Goto(-x_base, x_base, z_base, 2.5)),
    ( 0,    3,      Goto(x_base, x_base, z_base, 2.5)),

    ( 0,    4,      Goto(x_mid, -x_mid, z_mid, 2.5)),
    ( 0,    5,      Goto(-x_mid, -x_mid, z_mid, 2.5)),
    ( 0,    6,      Goto(-x_mid, x_mid, z_mid, 2.5)),
    ( 0,    7,      Goto(x_mid, x_mid, z_mid, 2.5)),


    ( 2.5,    0,      Goto(-x_base, -x_base, z_base, 2.5)),
    ( 2.5,    1,      Goto(-x_base, x_base, z_base, 2.5)),
    ( 2.5,    2,      Goto(x_base, x_base, z_base, 2.5)),
    ( 2.5,    3,      Goto(x_base, -x_base, z_base, 2.5)),

    ( 2.5,    4,      Goto(-x_mid, -x_mid, z_mid, 2.5)),
    ( 2.5,    5,      Goto(-x_mid, x_mid, z_mid, 2.5)),
    ( 2.5,    6,      Goto(x_mid, x_mid, z_mid, 2.5)),
    ( 2.5,    7,      Goto(x_mid, -x_mid, z_mid, 2.5)),


    ( 5,    0,      Goto(-x_base, x_base, z_base, 2.5)),
    ( 5,    1,      Goto(x_base, x_base, z_base, 2.5)),
    ( 5,    2,      Goto(x_base, -x_base, z_base, 2.5)),
    ( 5,    3,      Goto(-x_base, -x_base, z_base, 2.5)),

    ( 5,    4,      Goto(-x_mid, x_mid, z_mid, 2.5)),
    ( 5,    5,      Goto(x_mid, x_mid, z_mid, 2.5)),
    ( 5,    6,      Goto(x_mid, -x_mid, z_mid, 2.5)),
    ( 5,    7,      Goto(-x_mid, -x_mid, z_mid, 2.5)),


    ( 7.5,    0,      Goto(x_base, x_base, z_base, 2.5)),
    ( 7.5,    1,      Goto(x_base, -x_base, z_base, 2.5)),
    ( 7.5,    2,      Goto(-x_base, -x_base, z_base, 2.5)),
    ( 7.5,    3,      Goto(-x_base, x_base, z_base, 2.5)),

    ( 7.5,    4,      Goto(x_mid, x_mid, z_mid, 2.5)),
    ( 7.5,    5,      Goto(x_mid, -x_mid, z_mid, 2.5)),
    ( 7.5,    6,      Goto(-x_mid, -x_mid, z_mid, 2.5)),
    ( 7.5,    7,      Goto(-x_mid, x_mid, z_mid, 2.5)),
]

#### KICKLINE
# all 9 crazyflies form a line and go up and down alternatingly (think oompa
# loompas in a line from charlie and the chocolate factory)
x_0 = -1.5
x_1 = -1.125
x_2 = -.75
x_3 = -.375
x_4 = 0
x_5 = .375
x_6 = .75
x_7 = 1.125
x_8 = 1.5

z_base = 1
z_low = 0.75

kickline = [
    ( 0,    0,      Goto(x_0, 0, z_base, 1)),
    ( 0,    1,      Goto(x_1, 0, z_base, 1)),
    ( 0,    2,      Goto(x_2, 0, z_base, 1)),
    ( 0,    3,      Goto(x_3, 0, z_base, 1)),
    ( 0,    4,      Goto(x_4, 0, z_base, 1)),
    ( 0,    5,      Goto(x_5, 0, z_base, 1)),
    ( 0,    6,      Goto(x_6, 0, z_base, 1)),
    ( 0,    7,      Goto(x_7, 0, z_base, 1)),
    ( 0,    8,      Goto(x_8, 0, z_base, 1)),

    ( 1,    0,      Goto(x_0, 0, z_low, 1)),
    ( 1,    1,      Goto(x_1, 0, z_base, 1)),
    ( 1,    2,      Goto(x_2, 0, z_low, 1)),
    ( 1,    3,      Goto(x_3, 0, z_base, 1)),
    ( 1,    4,      Goto(x_4, 0, z_low, 1)),
    ( 1,    5,      Goto(x_5, 0, z_base, 1)),
    ( 1,    6,      Goto(x_6, 0, z_low, 1)),
    ( 1,    7,      Goto(x_7, 0, z_base, 1)),
    ( 1,    8,      Goto(x_8, 0, z_low, 1)),

    ( 2,    0,      Goto(x_0, 0, z_base, 1)),
    ( 2,    1,      Goto(x_1, 0, z_low, 1)),
    ( 2,    2,      Goto(x_2, 0, z_base, 1)),
    ( 2,    3,      Goto(x_3, 0, z_low, 1)),
    ( 2,    4,      Goto(x_4, 0, z_base, 1)),
    ( 2,    5,      Goto(x_5, 0, z_low, 1)),
    ( 2,    6,      Goto(x_6, 0, z_base, 1)),
    ( 2,    7,      Goto(x_7, 0, z_low, 1)),
    ( 2,    8,      Goto(x_8, 0, z_base, 1)),

    ( 3,    0,      Goto(x_0, 0, z_low, 1)),
    ( 3,    1,      Goto(x_1, 0, z_base, 1)),
    ( 3,    2,      Goto(x_2, 0, z_low, 1)),
    ( 3,    3,      Goto(x_3, 0, z_base, 1)),
    ( 3,    4,      Goto(x_4, 0, z_low, 1)),
    ( 3,    5,      Goto(x_5, 0, z_base, 1)),
    ( 3,    6,      Goto(x_6, 0, z_low, 1)),
    ( 3,    7,      Goto(x_7, 0, z_base, 1)),
    ( 3,    8,      Goto(x_8, 0, z_low, 1)),

    ( 4,    0,      Goto(x_0, 0, z_base, 1)),
    ( 4,    1,      Goto(x_1, 0, z_low, 1)),
    ( 4,    2,      Goto(x_2, 0, z_base, 1)),
    ( 4,    3,      Goto(x_3, 0, z_low, 1)),
    ( 4,    4,      Goto(x_4, 0, z_base, 1)),
    ( 4,    5,      Goto(x_5, 0, z_low, 1)),
    ( 4,    6,      Goto(x_6, 0, z_base, 1)),
    ( 4,    7,      Goto(x_7, 0, z_low, 1)),
    ( 4,    8,      Goto(x_8, 0, z_base, 1)),

    ( 5,    0,      Goto(x_0, 0, z_low, 1)),
    ( 5,    1,      Goto(x_1, 0, z_base, 1)),
    ( 5,    2,      Goto(x_2, 0, z_low, 1)),
    ( 5,    3,      Goto(x_3, 0, z_base, 1)),
    ( 5,    4,      Goto(x_4, 0, z_low, 1)),
    ( 5,    5,      Goto(x_5, 0, z_base, 1)),
    ( 5,    6,      Goto(x_6, 0, z_low, 1)),
    ( 5,    7,      Goto(x_7, 0, z_base, 1)),
    ( 5,    8,      Goto(x_8, 0, z_low, 1)),

    ( 6,    0,      Goto(x_0, 0, z_base, 1)),
    ( 6,    1,      Goto(x_1, 0, z_low, 1)),
    ( 6,    2,      Goto(x_2, 0, z_base, 1)),
    ( 6,    3,      Goto(x_3, 0, z_low, 1)),
    ( 6,    4,      Goto(x_4, 0, z_base, 1)),
    ( 6,    5,      Goto(x_5, 0, z_low, 1)),
    ( 6,    6,      Goto(x_6, 0, z_base, 1)),
    ( 6,    7,      Goto(x_7, 0, z_low, 1)),
    ( 6,    8,      Goto(x_8, 0, z_base, 1)),

    ( 7,    0,      Goto(x_0, 0, z_base, 1)),
    ( 7,    1,      Goto(x_1, 0, z_base, 1)),
    ( 7,    2,      Goto(x_2, 0, z_base, 1)),
    ( 7,    3,      Goto(x_3, 0, z_base, 1)),
    ( 7,    4,      Goto(x_4, 0, z_base, 1)),
    ( 7,    5,      Goto(x_5, 0, z_base, 1)),
    ( 7,    6,      Goto(x_6, 0, z_base, 1)),
    ( 7,    7,      Goto(x_7, 0, z_base, 1)),
    ( 7,    8,      Goto(x_8, 0, z_base, 1)),
]

#### WAVE
# all 9 crazyflies form a wave (sine curve sort of shape) and do a wave motion
z_top = 1.5
z_up = 1.25
z_base = 1
z_low = 0.75
z_bot = 0.5
wave = [
    ( 0,    0,      Goto(x_0, 0, z_up, 1)),
    ( 0,    1,      Goto(x_1, 0, z_top, 1)),
    ( 0,    2,      Goto(x_2, 0, z_top, 1)),
    ( 0,    3,      Goto(x_3, 0, z_up, 1)),
    ( 0,    4,      Goto(x_4, 0, z_base, 1)),
    ( 0,    5,      Goto(x_5, 0, z_low, 1)),
    ( 0,    6,      Goto(x_6, 0, z_bot, 1)),
    ( 0,    7,      Goto(x_7, 0, z_bot, 1)),
    ( 0,    8,      Goto(x_8, 0, z_low, 1)),

    ( 1,    0,      Goto(x_0, 0, z_top, 1)),
    ( 1,    1,      Goto(x_1, 0, z_top, 1)),
    ( 1,    2,      Goto(x_2, 0, z_up, 1)),
    ( 1,    3,      Goto(x_3, 0, z_base, 1)),
    ( 1,    4,      Goto(x_4, 0, z_low, 1)),
    ( 1,    5,      Goto(x_5, 0, z_bot, 1)),
    ( 1,    6,      Goto(x_6, 0, z_bot, 1)),
    ( 1,    7,      Goto(x_7, 0, z_low, 1)),
    ( 1,    8,      Goto(x_8, 0, z_up, 1)),

    ( 2,    0,      Goto(x_0, 0, z_top, 1)),
    ( 2,    1,      Goto(x_1, 0, z_up, 1)),
    ( 2,    2,      Goto(x_2, 0, z_base, 1)),
    ( 2,    3,      Goto(x_3, 0, z_low, 1)),
    ( 2,    4,      Goto(x_4, 0, z_bot, 1)),
    ( 2,    5,      Goto(x_5, 0, z_bot, 1)),
    ( 2,    6,      Goto(x_6, 0, z_low, 1)),
    ( 2,    7,      Goto(x_7, 0, z_up, 1)),
    ( 2,    8,      Goto(x_8, 0, z_top, 1)),

    ( 3,    0,      Goto(x_0, 0, z_up, 1)),
    ( 3,    1,      Goto(x_1, 0, z_base, 1)),
    ( 3,    2,      Goto(x_2, 0, z_low, 1)),
    ( 3,    3,      Goto(x_3, 0, z_bot, 1)),
    ( 3,    4,      Goto(x_4, 0, z_bot, 1)),
    ( 3,    5,      Goto(x_5, 0, z_low, 1)),
    ( 3,    6,      Goto(x_6, 0, z_up, 1)),
    ( 3,    7,      Goto(x_7, 0, z_top, 1)),
    ( 3,    8,      Goto(x_8, 0, z_top, 1)),

    ( 4,    0,      Goto(x_0, 0, z_base, 1)),
    ( 4,    1,      Goto(x_1, 0, z_low, 1)),
    ( 4,    2,      Goto(x_2, 0, z_bot, 1)),
    ( 4,    3,      Goto(x_3, 0, z_bot, 1)),
    ( 4,    4,      Goto(x_4, 0, z_low, 1)),
    ( 4,    5,      Goto(x_5, 0, z_up, 1)),
    ( 4,    6,      Goto(x_6, 0, z_top, 1)),
    ( 4,    7,      Goto(x_7, 0, z_top, 1)),
    ( 4,    8,      Goto(x_8, 0, z_up, 1)),

    ( 5,    0,      Goto(x_0, 0, z_low, 1)),
    ( 5,    1,      Goto(x_1, 0, z_bot, 1)),
    ( 5,    2,      Goto(x_2, 0, z_bot, 1)),
    ( 5,    3,      Goto(x_3, 0, z_low, 1)),
    ( 5,    4,      Goto(x_4, 0, z_up, 1)),
    ( 5,    5,      Goto(x_5, 0, z_top, 1)),
    ( 5,    6,      Goto(x_6, 0, z_top, 1)),
    ( 5,    7,      Goto(x_7, 0, z_up, 1)),
    ( 5,    8,      Goto(x_8, 0, z_base, 1)),

    ( 6,    0,      Goto(x_0, 0, z_bot, 1)),
    ( 6,    1,      Goto(x_1, 0, z_bot, 1)),
    ( 6,    2,      Goto(x_2, 0, z_low, 1)),
    ( 6,    3,      Goto(x_3, 0, z_up, 1)),
    ( 6,    4,      Goto(x_4, 0, z_top, 1)),
    ( 6,    5,      Goto(x_5, 0, z_top, 1)),
    ( 6,    6,      Goto(x_6, 0, z_up, 1)),
    ( 6,    7,      Goto(x_7, 0, z_base, 1)),
    ( 6,    8,      Goto(x_8, 0, z_low, 1)),

    ( 7,    0,      Goto(x_0, 0, z_bot, 1)),
    ( 7,    1,      Goto(x_1, 0, z_low, 1)),
    ( 7,    2,      Goto(x_2, 0, z_up, 1)),
    ( 7,    3,      Goto(x_3, 0, z_top, 1)),
    ( 7,    4,      Goto(x_4, 0, z_top, 1)),
    ( 7,    5,      Goto(x_5, 0, z_up, 1)),
    ( 7,    6,      Goto(x_6, 0, z_base, 1)),
    ( 7,    7,      Goto(x_7, 0, z_low, 1)),
    ( 7,    8,      Goto(x_8, 0, z_bot, 1)),
]

#### SOLOIST
# 8 crazyflies land, and ninth flies erratically in the middle
soloist = [
    ( 0,    0,      Land(3)),
    ( 0,    1,      Land(3)),
    ( 0,    2,      Land(3)),
    ( 0,    3,      Land(3)),
    ( 0,    4,      Land(3)),
    ( 0,    5,      Land(3)),
    ( 0,    6,      Land(3)),
    ( 0,    7,      Land(3)),

    ( 0,    8,      Goto(0, 0, 0.75, 1)),
    ( 1,    8,      Goto(-0.25, 0, 0.85, 0.75)),
    ( 1.75,    8,      Goto(0.25, 0, 0.95, 0.75)),
    ( 2.5,    8,      Goto(-0.25, 0, 1.05, 0.75)),
    ( 3.25,    8,      Goto(0.25, 0, 1.15, 0.75)),
    ( 4,    8,      Goto(0, 0, 0.75, 0.75)),
    ( 4.75,    8,      Goto(0, .75, 1.15, 0.75)),
    ( 5.5,    8,      Goto(0, -.75, 1.15, 1)),
    ( 6.5,    8,      Goto(0.25, 0.75, 1.15, 1)),
    ( 7.5,    8,      Goto(0, 0, 0.75, 1)),

]

#### ROTATING CUBE
# the 9 crazyflies form a cube and the cube rotates
z_mid = 1.5
z_in = 1
z_out = 0.5
x_in = 0.4
cube = [
    ( 0,    0,      Goto(x_in, x_in, z_out, 2.5)),
    ( 0,    1,      Goto(x_in, -x_in, z_out, 2.5)),
    ( 0,    2,      Goto(-x_in, -x_in, z_out, 2.5)),
    ( 0,    3,      Goto(-x_in, x_in, z_out, 2.5)),
    ( 0,    4,      Goto(x_in, x_in, z_mid, 2.5)),
    ( 0,    5,      Goto(x_in, -x_in, z_mid, 2.5)),
    ( 0,    6,      Goto(-x_in, -x_in, z_mid, 2.5)),
    ( 0,    7,      Goto(-x_in, x_in, z_mid, 2.5)),
    ( 0,    8,      Goto(0, 0, z_in, 2.5)),

    ( 2.5,    0,      Goto(x_in, -x_in, z_out, 2.5)),
    ( 2.5,    1,      Goto(-x_in, -x_in, z_out, 2.5)),
    ( 2.5,    2,      Goto(-x_in, x_in, z_out, 2.5)),
    ( 2.5,    3,      Goto(x_in, x_in, z_out, 2.5)),
    ( 2.5,    4,      Goto(x_in, -x_in, z_mid, 2.5)),
    ( 2.5,    5,      Goto(-x_in, -x_in, z_mid, 2.5)),
    ( 2.5,    6,      Goto(-x_in, x_in, z_mid, 2.5)),
    ( 2.5,    7,      Goto(x_in, x_in, z_mid, 2.5)),

    ( 5,    0,      Goto(-x_in, -x_in, z_out, 2.5)),
    ( 5,    1,      Goto(-x_in, x_in, z_out, 2.5)),
    ( 5,    2,      Goto(x_in, x_in, z_out, 2.5)),
    ( 5,    3,      Goto(x_in, -x_in, z_out, 2.5)),
    ( 5,    4,      Goto(-x_in, -x_in, z_mid, 2.5)),
    ( 5,    5,      Goto(-x_in, x_in, z_mid, 2.5)),
    ( 5,    6,      Goto(x_in, x_in, z_mid, 2.5)),
    ( 5,    7,      Goto(x_in, -x_in, z_mid, 2.5)),

    ( 7.5,    0,      Goto(-x_in, x_in, z_out, 2.5)),
    ( 7.5,    1,      Goto(x_in, x_in, z_out, 2.5)),
    ( 7.5,    2,      Goto(x_in, -x_in, z_out, 2.5)),
    ( 7.5,    3,      Goto(-x_in, -x_in, z_out, 2.5)),
    ( 7.5,    4,      Goto(-x_in, x_in, z_mid, 2.5)),
    ( 7.5,    5,      Goto(x_in, x_in, z_mid, 2.5)),
    ( 7.5,    6,      Goto(x_in, -x_in, z_mid, 2.5)),
    ( 7.5,    7,      Goto(-x_in, -x_in, z_mid, 2.5)),

]
