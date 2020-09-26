
from wasabi2d import keys

from .common import THAT_BLUE, add_key_icon, add_space_instruction

class AskMissile:
    def __init__(self, game):
        self.game = game
        backdrop_layer = game.scene.layers[1]
        bg_layer = game.scene.layers[1]
        btn_layer1 = text_layer = game.scene.layers[2]
        btn_layer2 = game.scene.layers[3]

        backdrop_layer.add_rect(
            game.scene.width*2, game.scene.height*2,
            color=(0, 0, .2),
        )
        bg_layer.add_rect(
            game.scene.width*3/4, game.scene.height/4,
            pos=(game.scene.width/2, game.scene.height/3),
            color=(1, 1, 1, 0.7),
        )
        if msg := self.game.info.message:
            addendum = f", not “{msg}”"
        else:
            addendum = ''
        for i, line in enumerate((
            "A missile won't do any good without the right message.",
            f"You need to spell out “HELP”{addendum}.",
            "Cast Arcane Missile anyway?",
        )):
            text_layer.add_label(
                line,
                font='kufam_medium',
                color=(*THAT_BLUE, 1),
                pos=(game.scene.width/2, game.scene.height/3 - 32 + i * 32),
                align='center',
                fontsize=20,
            )
        add_key_icon(btn_layer1, btn_layer2, game.scene.width*2/5, game.scene.height*3/6 - 32+8+4, "Y")
        add_key_icon(btn_layer1, btn_layer2, game.scene.width*3/5, game.scene.height*3/6 - 32+8+4, "N")
        add_space_instruction(btn_layer1, "Don't do it")


    def on_key_down(self, key):
        if key == keys.Y:
            self.game.abort_activity(on_done=self.game.island.fire_missile)
        if key in (keys.N, keys.SPACE, keys.ESCAPE):
            self.game.abort_activity()
