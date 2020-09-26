from wasabi2d import event, run, keys

from .game import Game
from .common import CHEAT

game = Game()

#game.island.last_selected = 3
game.info.food = game.info.magic = game.info.cube = 5
#game.info.cube = 6
#game.info.magic = 5
game.info.add_thing('@O00:N4000KOOOO0000000000:l')
game.info.add_thing('O111:OOOON0001O0000O0000I:L')
game.info.add_thing('@000:L0000000000000000000:.')
game.info.add_thing('L4<0:OON0003O000CM0000000:hook')
game.info.add_thing('H888:ON0001O0000O0000O000:')
game.info.add_thing('ODL0:OOOOLO?O00KOM0000000:P')
game.info.add_thing('L8L0:OOL003O<00COL0000000:H')
game.info.add_thing('OE@@:OOOONO9I9IO0000I0000:e')
game.info.add_thing('LDL0:OON00O7O00KOM0000000:o')
game.info.display[:] = 6, 7, 1, 5
game.info.food = game.info.magic = game.info.cube = 5
game.island.reset()
#game.island.on_key_down(keys.KP4)
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

print(game.scene.chain)

run()
