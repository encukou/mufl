from random import randrange, expovariate
from math import exp

from wasabi2d import clock, Group

from fixes import animate

MAX_FISH_WIDTH = 16*4*2

class Fishing:
    def __init__(self, scene, layer):
        self.spawner = FishSpawner(scene, layer)
        self.hook = Hook(
            scene, layer, self.spawner.group, pos=(scene.width//2, 0),
        )


class Fish:
    def __init__(self, layer, group, pos=(2, 50), speed=(100, 0)):
        self.sprite = layer.add_sprite('fish', pos=pos)
        if speed[0] >= 0:
            self.sprite.scale_x = -1
        self.speed = speed
        self.task = clock.coro.run(self.coro())
        group.capture(self.sprite)

    async def coro(self):
        while True:
            start_x, start_y = self.sprite.pos
            spd_x, spd_y = self.speed
            dur = 1
            await animate(
                self.sprite,
                pos=(start_x + spd_x/dur, start_y + spd_y/dur),
                tween='linear',
                duration=dur,
            )


class FishSpawner:
    def __init__(self, scene, layer):
        self.width = scene.width
        self.height = scene.height
        self.layer = layer
        self.group = Group([])
        self.task = clock.coro.run(self.coro())

    async def coro(self):
        while True:
            if randrange(2):
                x = 0 - MAX_FISH_WIDTH//2
                sx = randrange(50) + 50
            else:
                x = self.width + MAX_FISH_WIDTH//2
                sx = -randrange(50) - 50
            y = randrange(self.height * 4)
            fish = Fish(self.layer, self.group, pos=(x, y - self.group.pos[1]), speed=(sx, 0))
            await clock.coro.sleep(expovariate(self.height/100))


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

    async def coro(self):
        while True:
            dt = await clock.coro.next_frame()
            self.sprite.pos += self.speed[0] * dt, self.speed[1] * dt
            self.line.pos = self.sprite.pos
            self.group.pos = 0, -h_tween(0, self.sprite.pos[1] - self.scene.height // 3, self.sprite.pos[1]/self.scene.height*3)
            #if self.sprite.pos[1] > self.scene.height // 2:
            #    self.group.pos = 0, -(self.sprite.pos[1] - self.scene.height // 2)

def h_tween(a, b, t):
    if t < 0:
        t = 0
    if t > 1:
        t = 1
    return a * (1 - t) + b * t
