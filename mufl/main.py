from wasabi2d import event, run, keys

from .game import Game

game = Game()

game.island.last_selected = 3
game.info.food = game.info.magic = game.info.cube = 30
game.info.cube = 6
#game.info.magic = 5
game.island.on_key_down(keys.KP3)
game.island.on_key_down(keys.SPACE)

@event
def on_key_down(key, mod):
    if key == keys.RETURN:
        key = keys.SPACE
    if key == keys.BACKSPACE:
        key = keys.ESCAPE
    game.on_key_down(key)

@event
def on_key_up(key, mod):
    if key == keys.RETURN:
        key = keys.SPACE
    if key == keys.BACKSPACE:
        key = keys.ESCAPE
    game.on_key_up(key)

#for i in range(6):
    #from random import random
    #import colorsys
    #hue = random()
    #color = colorsys.hsv_to_rgb(hue, .7, .9)
    #game.info.add_boxfish(color)


run()
