from wasabi2d import event, run, keys

from .game import Game

game = Game()
#game.go_fish()

#game.info.give(food=3, magic=3, cube=3)
game.go_dice()

@event
def on_key_down(key, mod):
    if key == keys.ESCAPE:
        exit()

run()
