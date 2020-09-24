from math import hypot

from wasabi2d import chain, animate, Scene, clock, event

from .fishy import Fishing
from .dicy import DiceThrowing
from .info import Info, InfoNode


class Game:
    def __init__(self):
        self.scene = Scene(title='Cast Away!', icon='logo', width=800, height=600)
        self.scene.background = 0.9, 0.9, 1.0

        self.action_layers = chain.LayerRange(stop=9)
        self.fade_layers = chain.Layers([10])
        self.info_layers = chain.Layers([11, 12])
        self.info_node = InfoNode(self.info_layers)

        self.info = Info(self.scene, self.scene.layers[11], self.scene.layers[12])

        self.scene.chain = [
            self.action_layers,
            self.info_node,
        ]

        self.scene.layers[11].set_effect('dropshadow', radius=3, offset=(0, 0), opacity=3)

    def go_fish(self):
        self.activity = Fishing(
            self, on_finish=self.finish_activity,
        )

    def go_dice(self):
        self.activity = DiceThrowing(
            self, on_finish=self.finish_activity,
        )

    def finish_activity(self, speedup=1, **bonus):
        circ = self.scene.layers[10].add_sprite(
            'blur_circle',
            scale=hypot(self.scene.width, self.scene.height)//2 / 50,
            pos=(self.scene.width//2, self.scene.height*0.55),
        )
        if speedup == 1:
            tween = 'accelerate'
        else:
            tween = 'linear'
        animate(circ, scale=getattr(self.activity, 'end_fadeout_scale', 100/64), duration=5/speedup, tween=tween)
        self.scene.chain = [
            chain.Fill(color=(.1, .1, .1, 1)),
            chain.Mask(
                mask=self.fade_layers,
                paint=[chain.Fill(color=self.scene.background), self.action_layers],
            ),
            self.info_node,
        ]
        clock.schedule(lambda: self.info.give(sleep=1, **bonus), 4, strong=True)

    def on_key_down(self, key):
        try:
            on_key_down = self.activity.on_key_down
        except AttributeError:
            pass
        else:
            return on_key_down(key)
