from wasabi2d import event, run, keys

from .game import Game
from .common import CHEAT

game = Game()

#game.island.last_selected = 3
#game.info.food = game.info.magic = game.info.cube = 30
#game.info.cube = 6
#game.info.magic = 5
#game.island.on_key_down(keys.KP3)
#game.island.on_key_down(keys.SPACE)

def coalesce_key(key):
    if key in (keys.RETURN, keys.KP_ENTER):
        key = keys.SPACE
    if key == keys.BACKSPACE:
        key = keys.ESCAPE
    return key

@event
def on_key_down(key, mod):
    game.on_key_down(coalesce_key(key))


    if CHEAT:
        amt = -1 if (mod & (key.LSHIFT | key.RSHIFT)) else 1
        if key == keys.M:
            game.info.magic += amt
        if key == keys.F:
            game.info.food += amt
        if key == keys.C:
            game.info.cube += amt

@event
def on_key_up(key, mod):
    game.on_key_up(coalesce_key(key))

@event
def on_mouse_down():
    game.info.display_message('Let go of the mouse. You only need the keyboard.')

#for i in range(6):
    #from random import random
    #import colorsys
    #hue = random()
    #color = colorsys.hsv_to_rgb(hue, .7, .9)
    #game.info.add_boxfish(color)

run()
