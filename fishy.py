from random import randrange, expovariate

from wasabi2d import clock

from fixes import animate

MAX_FISH_WIDTH = 16*4*2

class Fish:
    def __init__(self, layer, pos=(2, 50), speed=(100, 0)):
        self.sprite = layer.add_sprite('fish', pos=pos)
        if speed[0] >= 0:
            self.sprite.scale_x = -1
        self.speed = speed
        self.task = clock.coro.run(self.coro())

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
            print('.')


class FishSpawner:
    def __init__(self, scene, layer):
        self.width = scene.width
        self.height = scene.height
        self.layer = layer
        self.num_spawned = 0
        self.task = clock.coro.run(self.coro())

    async def coro(self):
        while True:
            if randrange(2):
                x = 0 - MAX_FISH_WIDTH//2
                sx = randrange(50) + 50
            else:
                x = self.width + MAX_FISH_WIDTH//2
                sx = -randrange(50) - 50
            y = randrange(self.height)
            fish = Fish(self.layer, pos=(x, y), speed=(sx, 0))
            await clock.coro.sleep(expovariate(self.height/500))

