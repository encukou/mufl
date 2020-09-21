from random import randrange, expovariate, random
from math import exp
import colorsys

from wasabi2d import clock, Group, keyboard

from fixes import animate, fix_transforms

MAX_FISH_WIDTH = 16*4*2

class Fishing:
    def __init__(self, scene, fish_layer, hook_layer):
        self.spawner = FishSpawner(scene, fish_layer)
        self.hook = Hook(
            scene, hook_layer, self.spawner.group, pos=(scene.width//2, 10),
        )


class Fish:
    def __init__(self, scene, layer, group, pos=(2, 50), speed=(100, 0),
                 on_finish=lambda f: None):
        self.scene = scene
        self.sprite = layer.add_sprite('fish', pos=pos, anchor_x=8)
        fix_transforms(self.sprite)
        self.sprite.color = colorsys.hsv_to_rgb(random(), .5, 1)
        group.append(self.sprite)
        if speed[0] >= 0:
            self.sprite.scale_x = -1
        self.sprite.scale_y = 1 - abs(abs(speed[0])) / 500
        self.speed = speed
        self.task = clock.coro.run(self.coro())
        self.on_finish = on_finish

    async def coro(self):
        while True:
            start_x, start_y = self.sprite.pos
            if start_x < -MAX_FISH_WIDTH or start_x > (self.scene.width + MAX_FISH_WIDTH):
                self._del()
                return
            spd_x, spd_y = self.speed
            dur = 1
            await animate(
                self.sprite,
                pos=(start_x + spd_x/dur, start_y + spd_y/dur),
                tween='linear',
                duration=dur,
            )

    def _del(self):
        self.sprite.delete()
        self.on_finish(self)


class FishSpawner:
    def __init__(self, scene, layer):
        self.fishes = set()
        self.scene = scene
        self.width = scene.width
        self.height = scene.height
        self.layer = layer
        self.group = Group([])
        self.sprite = layer.add_sprite('sea', anchor_y=0)
        self.sprite.scale_x = scene.width
        self.sprite.scale_y = scene.height
        self.sprite.y = -scene.height
        self.group.capture(self.sprite)
        self.task = clock.coro.run(self.coro())

    async def coro(self):
        while True:
            if randrange(2):
                x = 0 - MAX_FISH_WIDTH//2
                sx = randrange(100) + 50
            else:
                x = self.width + MAX_FISH_WIDTH//2
                sx = -randrange(100) - 50
            y = randrange(self.height * 4)
            if y - self.group.y > MAX_FISH_WIDTH:
                fish = Fish(
                    self.scene, self.layer, self.group, pos=(x, y - self.group.y),
                    speed=(sx, 0), on_finish=self.fishes.discard,
                )
                await clock.coro.sleep(expovariate(self.height/100))
                self.fishes.add(fish)


class Hook:
    def __init__(self, scene, layer, group, pos):
        self.scene = scene
        self.sprite = layer.add_sprite('hook', pos=pos)
        self.line = layer.add_line([(0, 0), (0, -scene.height)])
        self.group = group
        group.capture(self.sprite)
        group.capture(self.line)
        self.speed = 0, 100
        self.task = clock.coro.run(self.coro())
        self.cooled_down = True

    async def coro(self):
        space = True
        while True:
            dt = await clock.coro.next_frame()
            #dt *= 10
            ws = self.sprite.pos[0] / self.scene.width
            if keyboard.keyboard.right:
                xs = 100
            elif keyboard.keyboard.left:
                xs = -100
            else:
                xs = 0
            if keyboard.keyboard.up:
                self.speed = xs, -100
            elif keyboard.keyboard.down:
                self.speed = xs, 200
            else:
                self.speed = xs, 50
            if not space and keyboard.keyboard.space and self.sprite.pos[1] > 50 and self.cooled_down:
                self.sprite.y -= 20
                self.cooled_down = False
                clock.coro.run(self.cool())
            space = keyboard.keyboard.space
            x = self.sprite.x + self.speed[0] * dt
            x = (x * 10 + self.scene.width * dt) / (10 + 2 * dt)
            if x < 0:
                x = 0
            if x >= self.scene.width:
                x = self.scene.width
            y =  self.sprite.y + self.speed[1] * dt
            self.sprite.pos = x, y
            self.line.pos = self.sprite.pos
            gpy = self.group.y
            newy = self.scene.height // 5 - self.sprite.y
            t = 1 - 2 / (1 + 1.05*exp(dt))
            gpy = gpy * (1-t) + newy * t
            self.group.pos = 0, gpy

    async def cool(self):
        await clock.coro.sleep(0.25)
        self.cooled_down = True


def h_tween(a, b, t):
    if t < 0:
        t = 0
    if t > 1:
        t = 1
    return a * (1 - t) + b * t
