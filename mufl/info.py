from dataclasses import dataclass

from wasabi2d import animate, clock
from wasabi2d.chain import ChainNode

class VisualizedProperty:
    def __set_name__(self, owner, name):
        self.owner = owner
        self.value = 0
        self.name = name
        self.storage_name = '_' + name
        self.row = owner._row_now
        owner._row_now += 1

    def __set__(self, obj, value):
        setattr(obj, self.storage_name, value)
        sprite = obj.sprites[self.name]
        label = obj.labels[self.name]
        if value:
            animate(sprite, color=(*sprite.color[:3], 1), duration=.2)
            animate(label, color=(*label.color[:3], 1), duration=.2)
        else:
            animate(sprite, color=(*sprite.color[:3], 0), duration=.2)
            animate(label, color=(*label.color[:3], 0), duration=.2)
        label.text = str(value)

    def __get__(self, obj, owner):
        if obj is None:
            return self
        else:
            return getattr(obj, self.storage_name)


COLORS = {
    'food': (.9, .4, .1),
    'magic': (.1, .7, .9),
}

class Info:
    _row_now = 0

    def __init__(self, scene, perm_layer, temp_layer):
        self.scene = scene
        self.perm_layer = perm_layer
        self.temp_layer = temp_layer

        self.labels = {}
        self.sprites = {}

        self.sprites['food'] = self.perm_layer.add_sprite('food', scale=1/2, pos=(8, 8), color=(*COLORS['food'], 0))
        self.labels['food'] = self.perm_layer.add_label('1', font='kufam_bold', pos=(18, 14), color=(0.9, 1, 1, 0), fontsize=15)

        self.sprites['magic'] = self.perm_layer.add_sprite('magic', scale=1/2, pos=(8, 8+16), color=(*COLORS['magic'], 0))
        self.labels['magic'] = self.perm_layer.add_label('10', font='kufam_bold', pos=(18, 14+16), color=(0.9, 1, 1, 0), fontsize=15)

        self.food = 1
        self.magic = 0

    food = VisualizedProperty()
    magic = VisualizedProperty()

    def give(self, sleep=0, **attrs):
        w = 32
        h = 32
        total = sum(attrs.values())
        async def go(name, amount, row):
            await clock.coro.sleep(row/5)
            x = (self.scene.width - w * (amount+1)) // 2
            y = self.scene.height // 2 + h * (row - 2 - len(attrs))
            async def go_one(i):
                sprite = self.temp_layer.add_sprite(name, pos=(x + w + i * w, y), color=COLORS[name], scale=0)
                await animate(sprite, scale=1, duration=0.25)
                await clock.coro.sleep(total / 4 + sleep)
                animate(sprite, duration=1, tween='accelerate', pos=self.sprites[name].pos, scale=self.sprites[name].scale)
                await clock.coro.sleep(.6)
                setattr(self, name, getattr(self, name) + 1)
            for i in range(amount):
                await clock.coro.sleep(.1)
                clock.coro.run(go_one(i))

        for row, (name, amount) in enumerate(attrs.items()):
            clock.coro.run(go(name, amount, row))


@dataclass
class InfoNode(ChainNode):
    """Draw one 'paint' layer only where the 'mask' layer is opaque."""

    inner: ChainNode

    def draw(self, scene):
        """Draw the effect."""
        camera = scene.camera
        prev_pos = camera.pos
        camera.pos = scene.width // 2, scene.height // 2
        scene.layers.shadermgr.set_proj(scene.camera.proj)
        self.inner.draw(scene)
        camera.pos = prev_pos
        scene.layers.shadermgr.set_proj(scene.camera.proj)
