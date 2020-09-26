
from wasabi2d import keys

from .common import THAT_BLUE, add_key_icon, add_space_instruction

class Intro:
    music_track = 'intro'

    def __init__(self, game):
        self.game = game
        backdrop_layer = game.scene.layers[1]
        bg_layer = game.scene.layers[1]
        btn_layer1 = text_layer = game.scene.layers[2]
        btn_layer2 = game.scene.layers[3]

        backdrop_layer.add_rect(
            game.scene.width*2, game.scene.height*2,
            color=(1, 1, 1, 0.7),
        )
        if msg := self.game.info.message:
            addendum = f", not “{msg}”"
        else:
            addendum = ''
        for i, line in enumerate((
            "They say witches and wizards throw the most awesome parties.",
            "When you heard about the Hocus Pocus, a magical party cruise ship,",
            "you decided you need to get onboard.",
            "Trouble is, you're only Level 1, and you know little more than",
            "the Fireball spell. You're not allowed in!",
            "But you know a thing or two about sneaking into parties, and you",
            "manage to get in. It's awesome — the music, the lights, the magic!",
            "",
            "After a few drinks, you try entertaining your new friends with ",
            "a trick involving fishing line and a pack of cards.",
            "It doesn't go too well. The magicians decide to maroon you",
            "on a nearby island. All in good fun of course: castaways",
            "are expected to simply teleport away when they sober up.",
            "",
            "But, teleportation is a Level 3 spell. You don't know it yet.",
            "You might be here for a while.",
            "At least you have your fishing line…",
        )):
            text_layer.add_label(
                line,
                font='kufam_medium',
                color=(*THAT_BLUE, 1),
                pos=(game.scene.width/2, 32 + i * 32),
                align='center',
                fontsize=20,
            )
        add_space_instruction(btn_layer1, "Let's Go!")


    def on_key_down(self, key):
        if key in (keys.SPACE, keys.ESCAPE):
            self.game.abort_activity()
