from dataclasses import dataclass
from traceback import print_exc

from wasabi2d import animate, clock, storage
from wasabi2d.chain import ChainNode

from .common import THAT_BLUE, CHEAT
from .fixes import animate


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
        if obj.game.island:
            obj.game.island.on_wealth_changed()

    def __get__(self, obj, owner):
        if obj is None:
            return self
        else:
            return getattr(obj, self.storage_name)


COLORS = {
    'food': (.9, .4, .1, 1),
    'magic': (.1, .7, .9, 1),
    'cube': (.8, .9, .1, 1),
    'thing': (.3, .3, .3, 1),
    'nada': (.2, .1, .1, .5),
}

class Info:
    _row_now = 0

    def __init__(self, game, perm_layer, temp_layer):
        self.game = game
        self.scene = game.scene
        self.perm_layer = perm_layer
        self.temp_layer = temp_layer

        self.labels = {}
        self.sprites = {}

        for i, (name, color) in enumerate(COLORS.items()):
            self.sprites[name] = self.perm_layer.add_sprite(name, scale=1/2, pos=(8, 8+16*i), color=(*color[:3], 0))
            self.labels[name] = self.perm_layer.add_label('0', font='kufam_bold', pos=(18, 14+16*i), color=(0.9, 1, 1, 0), fontsize=15)

        self.reset()

    def reset(self):
        self.food = 0
        self.magic = 0
        self.cube = 0
        self.thing = 0

        self.boxfish = []
        self.things = []
        self.display = [None] * 4

        self.known_actions = [False] * 5
        if self.game.island:
            self.game.island.reset()

    food = VisualizedProperty()
    magic = VisualizedProperty()
    cube = VisualizedProperty()
    thing = VisualizedProperty()

    def load(self, storage):
        try:
            self._load(storage)
        except Exception as e:
            print('Loading failed!')
            print_exc()
            print('Storage was:')
            print(storage)
            print('Clearing storage')
            storage.clear()
            self.reset()
        finally:
            if self.game.island:
                self.game.island.reset()

    def _load(self, storage):
        for attr_name in 'food', 'magic':
            if attr_name in storage:
                setattr(self, attr_name, int(storage[attr_name]))
        if 'boxfish' in storage:
            self.cube = 0
            for r, g, b in storage['boxfish']:
                self.cube += 1
                self.boxfish.append((float(r), float(g), float(b)))
        if 'things' in storage:
            self.thing = 0
            self.things.clear()
            for i, thing in zip(range(10), storage['things']):
                if thing is None:
                    self.things.append(None)
                else:
                    thing = str(thing)
                    assert thing.count('-') == 2
                    self.things.append(thing)
                    self.thing += 1
        if 'display' in storage:
            self.display[:] = [None] * 4
            for i, d in zip(range(4), storage['display']):
                if d is not None and 0 <= d < len(self.things) and self.things[d]:
                    self.display[i] = d
        if 'known_actions' in storage:
            for i, (o, n) in enumerate(zip(self.known_actions, storage['known_actions'])):
                self.known_actions[i] = bool(n)
        if self.game.island:
            self.game.island.reset()

    def save(self, storage):
        storage.update({
            'food': self.food,
            'magic': self.magic,
            'boxfish': tuple(self.boxfish),
            'things': tuple(self.things),
            'display': tuple(self.display),
            'known_actions': tuple(self.known_actions),
        })

    def add_boxfish(self, color):
        self.boxfish.append(color)

    def give(self, sleep=0, pos=None, outline=False, hoffset=1, **attrs):
        attrs = {n: v for n, v in attrs.items() if v}
        tasks = []
        w = 32
        h = 32
        if pos is None:
            pos = self.scene.width // 2, self.scene.height // 2 - 3 * h
        total = sum(attrs.values())
        if not total:
            return
        self.temp_layer.clear_effect()
        if outline:
            self.temp_layer.set_effect('dropshadow', radius=3, opacity=2, offset=(0, 0))
        async def go(name, amount, row):
            task = clock.coro.sleep(row/5)
            tasks.append(task)
            await task
            x = pos[0] - (w * (amount+1)) // 2
            y = pos[1] + h * (row - len(attrs) * hoffset + hoffset)
            async def go_one(i):
                sprite = self.temp_layer.add_sprite(name, pos=(x + w + i * w, y), color=COLORS[name], scale=0)
                await animate(sprite, scale=1, duration=0.25)
                await clock.coro.sleep(total / 8 + sleep)
                anim = animate(sprite, duration=1, tween='accelerate', pos=self.sprites[name].pos, scale=self.sprites[name].scale)
                await clock.coro.sleep(.6)
                setattr(self, name, getattr(self, name) + 1)
                await anim
                sprite.delete()
                tasks.append(anim)
            for i in range(amount):
                await clock.coro.sleep(.1)
                task = clock.coro.run(go_one(i))
                tasks.append(task)

        for row, (name, amount) in enumerate(attrs.items()):
            clock.coro.run(go(name, amount, row))

    def learn_action(self, index):
        if not self.known_actions[index]:
            self.known_actions[index] = True
            if self.game.island:
                self.game.island.on_wealth_changed()
            return True
        return False

    def add_thing(self, thing):
        if CHEAT:
            print(thing)
        self.things.append(thing)
        self.thing += 1

    def remove_thing(self, i):
        thing = self.things[i]
        print('Casting away', thing)
        self.things[i] = None
        self.thing -= 1

    def display_message(self, message):
        print(message)
        rect = self.temp_layer.add_rect(
            self.scene.width*0.99, 64,
            pos=(self.scene.width//2, self.scene.height//2-8),
            color=(1, 1, 1, 0),
        )
        label = self.temp_layer.add_label(
            message,
            font='kufam_medium',
            pos=(self.scene.width//2, self.scene.height//2),
            align='center',
            color=(*THAT_BLUE, 0),
            fontsize=30,
        )
        async def animit():
            animate(rect, color=(1, 1, 1, 0.95), duration=0.2)
            await animate(label, color=(*THAT_BLUE, 1), duration=0.2)
            await clock.coro.sleep(0.5 + len(message)/15)
            animate(rect, color=(1, 1, 1, 0))
            await animate(label, color=(*THAT_BLUE, 0))
            await clock.coro.sleep(1)
            try:
                rect.delete()
                label.delete()
            except Exception:
                # XXX : why?
                pass
        clock.coro.run(animit())

    @property
    def message(self):
        msg = ''
        for i in self.display:
            if i is None:
                label = ''
            else:
                code1, code2, label = self.things[i].split('-')
            if len(label) == 1:
                msg += label.upper()
            elif msg and not msg.endswith(' '):
                msg += ' '
        return msg.strip()

    @property
    def message_assembled(self):
        return self.message == 'HELP'

    @property
    def things_full(self):
        if len(self.things) >= 10 and all(t != None for t in self.things):
            return True
        return False

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
