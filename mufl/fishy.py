from random import randrange, expovariate, random, lognormvariate, choice
from math import exp, hypot, tau, copysign, log
import colorsys

from wasabi2d import clock, Group, keyboard, keys

from .fixes import animate, fix_transforms
from .common import add_key_icon, add_space_instruction
from .music import play_sound

MAX_FISH_WIDTH = 16*4*2
FISH_SIZE = 16*1.5

class Fishing:
    music_track = 'fish'

    def __init__(self, game, on_finish):
        self.game = game
        self.active = True
        fish_layer = game.scene.layers[1]
        hook_layer = game.scene.layers[2]
        hud_layer = game.scene.layers[3]
        self.scene = game.scene
        self.hook = None
        self.on_finish = on_finish
        self.spawner = FishSpawner(self, fish_layer)
        self.hook = Hook(
            self, hook_layer, self.spawner.group, pos=(game.scene.width//2, 10),
        )

        hud_layer.add_sprite('kbd_arrows', pos=(2, game.scene.height-74), anchor_x=0)
        l=hud_layer.add_label('Move!', font='kufam_medium', pos=(106, game.scene.height-50), color=(0.1, 0.3, 0.8), fontsize=50)
        l.scale = 1/2
        add_space_instruction(hud_layer, 'Pull!')

    def on_key_down(self, key):
        if self.hook.hooked_fish:
            return True
        if key in (keys.ESCAPE, keys.BACKSPACE):
            self.game.abort_activity()
            self.selecting = False
            return True


class Fish:
    def __init__(self, fishing, layer, group, pos, speed,
                 on_finish=lambda f: None):
        self.fishing = fishing
        self.anim = None
        self.caught = False
        hue = random()
        kind = 'fish'
        fin_pos = (28, -2)
        anchor_x = 32
        anchor_y = 32
        self.bonus = {
            'food': randrange(2, 5),
            'magic': randrange(0, int(max(1, log(max(1, -group.y/5))/2))),
            'cube': 0,
        }
        if abs(hue - 1/6) < random() / 16:
            kind = 'fish_crown'
            self.bonus['magic'] += randrange(5, 9)
            hue = 1/6
        elif random() < 1 / 32 and self.fishing.game.info.cube < 6:
            kind = 'fish_box'
            fin_pos = 16, -12
            anchor_x = 20
            anchor_y = 48
            self.bonus['magic'] += 2
            self.bonus['cube'] += 1
        elif self.bonus['magic']:
            kind = 'fish_scaly'
        color = colorsys.hsv_to_rgb(hue, .7, .9)
        self.color = color
        sprite = layer.add_sprite(kind, anchor_x=anchor_x, anchor_y=anchor_y, color=color)
        self.mouth_sprite = layer.add_sprite('fish_mouth', color=color)
        self.fin_sprite = layer.add_sprite('fin', color=color, pos=fin_pos)
        fix_transforms(sprite)
        self.group = Group([
            sprite,
            self.mouth_sprite,
            self.fin_sprite,
        ])
        group.append(self.group)
        self.group.pos = pos
        if speed[0] >= 0:
            self.group.scale_x = -1
        self.group.scale_y = 1 - abs(abs(speed[0])) / 2000
        self.speed = speed
        self.task = None
        self.reset_task()
        self.on_finish = on_finish
        self.fin_task = clock.coro.run(self.move_fin())
        self.cooldown = 0

    def reset_task(self):
        if self.task:
            self.task.cancel()
        self.task = clock.coro.run(self.coro())

    async def coro(self):
        try:
            while self.fishing.active:
                start_x, start_y = self.group.pos
                if start_x < -MAX_FISH_WIDTH or start_x > (self.fishing.scene.width + MAX_FISH_WIDTH):
                    for obj in self.group:
                        obj.delete()
                    self.on_finish(self)
                    self.fin_task.cancel()
                    return
                spd_x, spd_y = self.speed
                dur = 1
                self.anim = animate(
                    self.group,
                    pos=(start_x + spd_x/dur, start_y + spd_y/dur),
                    tween='linear',
                    duration=dur,
                )
                await self.anim
                while self.caught:
                    await clock.coro.sleep(1)
        finally:
            self.task = None


    async def move_fin(self):
        dur = 0.25
        max_angle = 0.4
        while self.fishing.active:
            await animate(
                self.fin_sprite,
                angle=max_angle,
                tween='accel_decel',
                duration=dur,
            )
            await animate(
                self.fin_sprite,
                angle=-max_angle,
                tween='accel_decel',
                duration=dur,
            )


class FishSpawner:
    def __init__(self, fishing, layer):
        self.fishes = set()
        self.fishing = fishing
        self.scene = fishing.scene
        self.width = self.scene.width
        self.height = self.scene.height
        self.layer = layer
        self.group = Group([])
        self.sprite = layer.add_sprite('sea', anchor_y=-0.5)
        self.sprite.scale_x = self.scene.width / 16
        self.sprite.scale_y = self.scene.height
        self.sprite.y = -self.scene.height
        self.group.capture(self.sprite)
        self.task = clock.coro.run(self.coro())

    async def coro(self):
        await clock.coro.sleep(0.1)
        while self.fishing.active:
            depth = abs(self.fishing.hook.sprite.y)
            if randrange(2):
                x = 0 - MAX_FISH_WIDTH//2
                sx = randrange(100 + depth//50) + 50
            else:
                x = self.width + MAX_FISH_WIDTH//2
                sx = -randrange(100 + depth//50) - 50
            y = randrange(self.height * 4)
            if self.fishing.hook.hooked_fish:
                y -= self.height * 3
            if y - self.group.y > MAX_FISH_WIDTH:
                fish = Fish(
                    self.fishing, self.layer, self.group,
                    pos=(x, y - self.group.y),
                    speed=(sx, 0), on_finish=self.fishes.discard,
                )
                self.fishes.add(fish)
            await clock.coro.sleep(expovariate(self.height/100 + abs(self.fishing.hook.sprite.y/1000)))
        self.task = None

    def stop(self):
        if self.task:
            self.task.cancel()
            self.task = None


class Hook:
    def __init__(self, fishing, layer, group, pos):
        self.fishing = fishing
        self.scene = fishing.scene
        self.sprite = layer.add_sprite('hook', pos=pos)
        fix_transforms(self.sprite)
        self.line = layer.add_line([(-9, -18), (-9, -self.scene.height)])
        self.group = group
        group.capture(self.sprite)
        group.capture(self.line)
        self.speed = 0, 100
        self.task = clock.coro.run(self.coro())
        self.cooled_down = True
        self.caught_fish = None
        self.hooked_fish = None
        self.pullout_speed = 200
        self.want_h = self.scene.height // 5
        self.caught_timer = 0
        self.pull_timer = 0
        self.particle_group = layer.add_particle_group(
            texture='bubble',
            gravity=(0, 550),
            max_age=1,
            grow=0.5,
        )
        self.particle_group.add_color_stop(0, (1, 1, 1, 0))
        self.particle_group.add_color_stop(0.25, (1, 1, 1, 0.5))
        self.particle_group.add_color_stop(.5, (0.75, 0.9, 1, 0.5))
        self.particle_group.add_color_stop(1, (0.9, 1, 1, 0))
        self.active = True

    async def coro(self):
        space = True
        while True:
            dt = await clock.coro.next_frame()
            ws = self.sprite.x / self.scene.width
            if self.active:
                if keyboard.keyboard.right:
                    xs = 100
                elif keyboard.keyboard.left:
                    xs = -100
                else:
                    xs = 0
                if keyboard.keyboard.up:
                    ys = -100
                elif keyboard.keyboard.down:
                    ys = 200
                else:
                    ys = 50
            else:
                xs = copysign(10, 1/2-ws)
                ys = 50
            if self.hooked_fish:
                ys -= self.pullout_speed
            self.speed = xs, ys
            if not space and keyboard.keyboard.space and self.sprite.pos[1] > 50 and self.cooled_down:
                self.sprite.y -= 20
                self.cooled_down = False
                clock.coro.run(self.cool())
                if self.caught_fish and not self.hooked_fish:
                    self.catch_fish()
            space = keyboard.keyboard.space
            x = self.sprite.x + self.speed[0] * dt
            x = (x * 10 + self.scene.width * dt) / (10 + 2 * dt)
            if x < 0:
                x = 1
            if x >= self.scene.width:
                x = self.scene.width
            y = self.sprite.y + self.speed[1] * dt
            if y < -self.scene.height * 10:
                y = -self.scene.height * 10
            if (y < 0) != (self.sprite.y < 0):
                if 1or self.hooked_fish:
                    play_sound('wave')
                    self.particle_group.emit(
                        abs(ys)/2, size=10, size_spread=10,
                        vel_spread=(100, 50),
                        vel=(0, -200-ys/2),
                        angle_spread=tau,
                        pos=self.sprite.pos + self.group.pos,
                    )
                else:
                    y = 1
            self.sprite.pos = x, y
            self.line.pos = self.sprite.pos
            gpy = self.group.y
            newy = self.want_h - self.sprite.y
            t = 1 - 2 / (1 + 1.05*exp(dt))
            gpy = gpy * (1-t) + newy * t
            if self.hooked_fish:
                t = self.pull_timer
                if t > 1:
                    t = 1
                gpy = gpy * (1-t) + newy * t
            self.group.pos = 0, gpy

            if fish := self.caught_fish:
                self.pull_timer += dt
                fish.group.pos = self.sprite.pos
                if not self.hooked_fish:
                    self.caught_timer -= dt
                    if self.caught_timer < 0:
                        if randrange(sum(fish.bonus.values())) < 2:
                            self.catch_fish()
                        else:
                            play_sound('fish-got-away')
                            self.caught_fish = None
                            fish.caught = False
                            fish.cooldown = 1
                            xs, ys = fish.speed
                            fish.speed = xs * 4, ys
                            animate(fish, cooldown=0)
                            animate(fish, speed=(xs * 2, ys), duration=4)
                            fish.reset_task()
                            self.sprite.image = 'hook'
            else:
                for fish in self.fishing.spawner.fishes:
                    dist = hypot(*(self.sprite.pos - fish.group.pos)) / (FISH_SIZE * 4)
                    if dist < 1:
                        if dist < 1/4/2 and fish.cooldown <= 0:
                            play_sound('bite', volume=.4)
                            fish.mouth_sprite.angle = 0
                            self.caught_fish = fish
                            self.sprite.image = 'hook_in'
                            self.caught_timer = 0.2 + lognormvariate(0, 0.25) / 2
                            if fish.task:
                                fish.task.cancel()
                            if fish.anim:
                                fish.anim.stop()
                            break
                        else:
                            fish.mouth_sprite.angle = (dist)-1
                    elif fish.mouth_sprite.angle != 0:
                        fish.mouth_sprite.angle = 0

    def catch_fish(self):
        self.hooked_fish = self.caught_fish
        self.hooked_fish.fin_task.cancel()
        if self.hooked_fish.speed[0] > 0:
            angle = -tau/4
        else:
            angle = tau/4
        animate(self.hooked_fish.group, angle=angle)
        animate(
            self, tween='accelerate', duration=15,
            pullout_speed=1000,
        )
        animate(
            self, duration=3,
            want_h=self.scene.height // 2
        )
        self.pull_timer = 0

        clock.schedule(self.fishing.spawner.stop, 3, strong=True)
        clock.schedule(lambda: setattr(self, 'active', False), 0.5, strong=True)

        if self.hooked_fish.bonus['cube']:
            self.fishing.game.info.add_boxfish(self.hooked_fish.color)
        self.fishing.on_finish(**self.hooked_fish.bonus)

    async def cool(self):
        await clock.coro.sleep(0.25)
        self.cooled_down = True
