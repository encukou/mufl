from wasabi2d import event, run, keys

from .game import Game
from .common import CHEAT

game = Game()

#game.info.load({'food': 4, 'magic': 5, 'boxfish': (), 'things': ('@O00-N4000KOOOO0000000000-l', 'O111-OOOON0001O0000O0000I-L', '@000-L0000000000000000000-.', 'L4<0-OON0003O000CM0000000-hook', 'H888-ON0001O0000O0000O000-', 'ODL0-OOOOLO?O00KOM0000000-P', 'L8L0-OOL003O<00COL0000000-H', 'OE@@-OOOONO9I9IO0000I0000-e', 'LDL0-OON00O7O00KOM0000000-o', 'LDL0-OON00O7O00KOM0000000-o'), 'display': (6, 7, 5, 1), 'known_actions': (True, True, True, True, False)})

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

run()
