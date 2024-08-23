DIR = '/Games/Threk'
from sys import path
if not DIR in path:
    path.append(DIR)

import time
import thumby
import random

import global_store
from game import GameState
from ui.screens import TitleScreen, MainScreen
from actions import PendingAction
from systems import Sound

thumby.saveData.setName("Threk")

thumby.display.setFPS(30)
random.seed(time.ticks_us())
global_store.game_state = GameState()
global_store.game_state.change_screen(TitleScreen)

global_store.current_time = time.ticks_ms()
last_time = global_store.current_time

while(1):
    gs = global_store.game_state

    global_store.current_time = time.ticks_ms()
    global_store.delta = time.ticks_diff(global_store.current_time, last_time)
    last_time = global_store.current_time

    if PendingAction.queue and type(gs.screen) == MainScreen:
        PendingAction.process(global_store.delta)
    else:
        gs.screen.process()
    gs.screen.draw()

    thumby.display.update()

    Sound.process(global_store.delta)
