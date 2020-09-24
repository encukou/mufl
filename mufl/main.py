from wasabi2d import event, run, keys

from .game import Game

game = Game()
#game.go_fish()

game.info.food = game.info.magic = game.info.cube = 6
game.info.magic = 3
game.go_dice()

@event
def on_key_down(key, mod):
    if game.on_key_down(key):
        return
    else:
        if key == keys.ESCAPE:
            exit()

run()
