from wasabi2d import event, run, keys

from .game import Game

game = Game()

game.info.food = game.info.magic = game.info.cube = 6
game.info.magic = 9

#game.go_fish()

game.go_dice()

#game.return_to_island()

#game.info.give(magic=1, thing=2)

@event
def on_key_down(key, mod):
    if key == keys.RETURN:
        key = keys.SPACE
    if key == keys.BACKSPACE:
        key = keys.ESCAPE
    if game.on_key_down(key):
        return
    else:
        if key == keys.ESCAPE:
            exit()

@event
def on_key_up(key, mod):
    if key == keys.RETURN:
        key = keys.SPACE
    if key == keys.BACKSPACE:
        key = keys.ESCAPE
    if game.on_key_up(key):
        return

run()
