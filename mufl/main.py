from wasabi2d import event, run, keys

from .game import Game

game = Game()
game.go_fish()

@event
def on_key_down(key, mod):
    if key == keys.ESCAPE:
        exit()

run()
