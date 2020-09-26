from math import hypot

from wasabi2d import chain, animate, Scene, clock, event

from .fishy import Fishing
from .dicy import DiceThrowing
from .info import Info, InfoNode
from .island import Island
from .burrow import Burrowing
from .shadow import Shadowing


class Game:
    def __init__(self):
        self.scene = Scene(title='Cast Away!', icon='logo', width=800, height=600)
        self.scene.background = 0.9, 0.9, 1.0

        self.fade_layer = self.scene.layers[30]
        self.info_layer1 = self.scene.layers[31]
        self.info_layer2 = self.scene.layers[32]

        self.action_layers = chain.LayerRange(stop=5)
        self.fade_layers = chain.Layers([30])
        self.info_layers = chain.Layers([31, 32])
        self.island_layers = chain.LayerRange(start=6, stop=10)
        self.info_node = InfoNode(self.info_layers)

        self.island = None
        self.info = Info(self, self.info_layer1, self.info_layer2)
        self.island = Island(self)

        self.scene.chain = [
            self.action_layers,
            self.info_node,
        ]

        self.info_layer1.set_effect('dropshadow', radius=3, offset=(0, 0), opacity=3)

        self.fade_circ = self.fade_layer.add_sprite(
            'blur_circle',
            scale=hypot(self.scene.width, self.scene.height)//2 / 50,
            pos=(self.scene.width//2, self.scene.height*0.55),
        )
        self.fade_rect = self.fade_layer.add_rect(
            self.scene.width * 3, self.scene.height * 3,
            color=(0, 0, 0, 0),
        )

        self.return_to_island()

    def go_do(self, idx):
        self.info.food -= 1
        self.activity = None
        for i in range(5):
            self.scene.layers.pop(i, None)
        async def coro():
            self.scene.chain = [
                self.island_layers,
                self.fade_layers,
                self.info_node,
            ]
            self.fade_circ.color = (0, 0, 0, 0)
            self.fade_rect.color = (0, 0, 0, 0)
            await animate(self.fade_rect, color=(0, 0, 0, 1), duration=0.25, tween='accelerate')
            black = clock.coro.sleep(0.25)
            if idx == 0:
                self.go_fish()
            elif idx == 1:
                self.go_dice()
            elif idx == 2:
                self.go_burrow()
            elif idx == 3:
                self.go_shadow()
            else:
                await black
                print('ERROR, unknown action')
                self.return_to_island()
                return
            self.scene.chain = [
                self.action_layers,
                self.fade_layers,
                self.info_node,
            ]
            await black
            await animate(self.fade_rect, color=(0, 0, 0, 0), duration=0.25, tween='accelerate')
            self.fade_rect.color = (0, 0, 0, 0)
            self.scene.chain = [
                self.action_layers,
                self.info_node,
            ]
        clock.coro.run(coro())

    def go_fish(self):
        self.activity = Fishing(
            self, on_finish=self.finish_activity,
        )

    def go_dice(self):
        self.activity = DiceThrowing(
            self, on_finish=self.finish_activity,
        )

    def go_burrow(self):
        self.activity = Burrowing(self)

    def go_shadow(self):
        self.activity = Shadowing(self)

    def return_to_island(self):
        self.activity = self.island
        self.scene.chain = [
            self.island_layers,
            self.info_node,
        ]
        self.island.reset()

    def finish_activity(self, speedup=1, superfast=False, extra_delay=4, **bonus):
        self.activity = None
        async def coro():
            if speedup == 1:
                tween = 'accelerate'
                efs = getattr(self.activity, 'end_fadeout_scale', 100/64)
            else:
                tween = 'linear'
                efs = 0
            self.fade_circ.color = (0, 0, 0, 1)
            self.fade_circ.scale = hypot(self.scene.width, self.scene.height)//2 / 50
            ani = animate(self.fade_circ, scale=efs, duration=5/speedup, tween=tween)
            self.scene.chain = [
                chain.Fill(color=(.1, .1, .1, 1)),
                chain.Mask(
                    mask=self.fade_layers,
                    paint=[chain.Fill(color=self.scene.background), self.action_layers],
                ),
                self.info_node,
            ]
            if extra_delay:
                await clock.coro.sleep(extra_delay)
            self.info.give(sleep=1, **bonus)
            await ani
            if self.fade_circ.scale:
                print(self.fade_circ.scale)
                await clock.coro.sleep(1)
                await animate(self.fade_circ, scale=0, duration=self.fade_circ.scale, tween='accelerate')
            self.scene.chain = [
                self.island_layers,
                self.fade_layers,
                self.info_node,
            ]
            self.fade_rect.color = (0, 0, 0, 1)
            await animate(self.fade_rect, color=(0, 0, 0, 0), duration=0.25, tween='accelerate')
            for i in range(5):
                self.scene.layers.pop(i, None)
            self.return_to_island()
        clock.coro.run(coro())

    def abort_activity(self, return_food=True, deselect=False):
        if return_food:
            self.info.food += 1
        self.activity = None
        async def coro():
            self.scene.chain = [
                self.action_layers,
                self.fade_layers,
                self.info_node,
            ]
            self.fade_circ.color = (0, 0, 0, 0)
            self.fade_rect.color = (0, 0, 0, 0)
            await animate(self.fade_rect, color=(0, 0, 0, 1), duration=0.25, tween='accelerate')
            black = clock.coro.sleep(0.25)
            for i in range(5):
                self.scene.layers.pop(i, None)
            self.scene.chain = [
                self.island_layers,
                self.fade_layers,
                self.info_node,
            ]
            self.activity = self.island
            self.island.reset()
            await black
            await animate(self.fade_rect, color=(0, 0, 0, 0), duration=0.25, tween='accelerate')
            self.scene.chain = [
                self.island_layers,
                self.info_node,
            ]
        clock.coro.run(coro())
        if deselect:
            self.island.deselect()

    def on_key_down(self, key):
        try:
            on_key_down = self.activity.on_key_down
        except AttributeError:
            pass
        else:
            return on_key_down(key)

    def on_key_up(self, key):
        try:
            on_key_up = self.activity.on_key_up
        except AttributeError:
            pass
        else:
            return on_key_up(key)
