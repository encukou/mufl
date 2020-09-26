import pkgutil
from dataclasses import dataclass
from itertools import zip_longest
from math import tau
from random import uniform

from wasabi2d import clock
import numpy

from .info import COLORS as BONUS_COLORS
from .common import add_key_icon, add_space_instruction, KEY_NUMBERS, change_sprite_image, THAT_BLUE
from .fixes import animate
from .thing import get_thing_sprite_info

def add_rect_with_topleft_anchor(layer, x, y, w, h, **kwargs):
    return layer.add_rect(w, h, pos=(x+w/2, y+h/2), **kwargs)

FIRE_POS = 484, 570


@dataclass
class Action:
    caption: str
    cost: tuple
    description: list


def load_actions():
    actions = []
    PERFORATION = ' 8< '.center(42, '-')
    text = pkgutil.get_data('mufl', 'text/actions.txt').decode('utf-8')
    for txt in text.split(PERFORATION):
        txt = txt.strip()
        lines = txt.splitlines()
        cost = lines[1].split()
        assert not lines[2], lines[2]
        actions.append(Action(
            caption=lines[0],
            cost=tuple(cost),
            description=lines[3:],
        ))
    return actions


class Island:
    def __init__(self, game):
        self.actions = load_actions()
        self.game = game
        self.backdrop_layer = self.game.scene.layers[6]
        self.shade_layer = self.game.scene.layers[7]
        self.effect_layer = self.thing_layer = self.game.scene.layers[8]
        self.bg_layer = self.game.scene.layers[9]
        self.main_layer = self.textbg_layer = self.game.scene.layers[10]
        self.top_layer = self.text_layer = self.game.scene.layers[11]

        self.input_frozen = False

        self.backdrop_layer.add_sprite('island', anchor_x=0, anchor_y=80)

        self.last_selected = None

        self.bg_sprites = []
        self.caption_labels = []
        self.keyboard_icons = []
        self.cost_icons = []

        ys = 0
        ysep = 110
        xpos = 192+6
        for i, action in enumerate(self.actions):
            s = self.bg_layer.add_sprite('action_bg', pos=(64, ys+16+i*ysep), color=(.5, .5, .5), anchor_x=0, anchor_y=0)
            self.bg_sprites.append(s)
            lbl = self.main_layer.add_label(action.caption, font='kufam_bold', pos=(xpos, ys+56+i*ysep), color=(1, 1, 1), align='center', fontsize=22)
            self.caption_labels.append(lbl)
            ki = add_key_icon(self.main_layer, self.top_layer, xpos-128, ys+56+i*ysep-8+2, str(i+1))
            self.keyboard_icons.append(ki)
            cost = action.cost
            if not cost:
                cost = ['free']
            cost_icons = []
            for j, item in enumerate(cost):
                x = xpos + (j - (len(cost)-1)/2) * 32 - 4
                y = ys+56+i*ysep+16+8
                if item in BONUS_COLORS:
                    o = self.main_layer.add_sprite(item, pos=(x, y), color=BONUS_COLORS[item])
                else:
                    o = self.main_layer.add_label(f'{item}', font='kufam_medium', pos=(x, y+8), color=(1, 1, 1), align='center', fontsize=15)
                cost_icons.append(o)
            self.cost_icons.append(cost_icons)

        self.space_instruction_objs = add_space_instruction(self.bg_layer, 'Press Space to Start')

        self.bg_rect = add_rect_with_topleft_anchor(self.textbg_layer, 360, ys+16, 400, ysep*4+64+32, color=(1, 1, 1, 0))
        self.caption_label = self.text_layer.add_label('', font='kufam_medium', pos=(560, ys+64), color=(THAT_BLUE), align='center', fontsize=22)
        self.description_labels = []
        for i in range(max(len(a.description) for a in self.actions)):
            lbl = self.text_layer.add_label('', font='kufam_medium', pos=(560, ys+64+i*30+64), color=(THAT_BLUE), align='center', fontsize=15)
            self.description_labels.append(lbl)

        self.affordable = [False] * 5

        pg = self.bg_layer.add_particle_group(
            texture='blur_circle',
            gravity=1,
        )
        pg.add_color_stop(0, (1, 0, 0))
        pg.add_color_stop(2, (1, 1, 0))
        pg.add_color_stop(3, (0, 0, 0))
        pg.add_color_stop(3.2, (.5, .5, .5, 0))
        self.emitter = pg.add_emitter(
            rate=10,
            pos=(490, 576),
            size=8,
        )

        self.flames = []
        for i in range(4):
            s = self.effect_layer.add_sprite('flame', pos=FIRE_POS, scale=1/3, anchor_y=48, color=(1, 0, 0, .4))
            if i % 2:
                s.scale_x = -1
            self.flames.append(s)
            clock.coro.run(self.anim_flame(s, i, *FIRE_POS))

        pg = self.effect_layer.add_particle_group(
            'blur_circle', grow=1.0, max_age=3.2, spin_drag=1.1, gravity=-4,
        )
        pg.add_color_stop(0, (1, 0, 0))
        pg.add_color_stop(2, (1, 1, 0))
        pg.add_color_stop(3, (.5, .5, .5))
        pg.add_color_stop(3.2, (.5, .5, .5, 0))
        self.hypno_emitters = []
        em = pg.add_emitter(
            rate=20, pos=FIRE_POS, pos_spread=(2, 2), vel=(2, -8),
            vel_spread=(4, 0.1), size=1.2, size_spread=0.1, spin_spread=tau,
        )
        self.hypno_emitter = em

        self.shade_layer.add_rect(
            self.game.scene.width, self.game.scene.height*2+2,
            pos=(self.game.scene.width//2, -self.game.scene.height),
            color=(1, 1, 1, 1),
        )
        self.shadow_sprite = self.shade_layer.add_sprite(
            'island_shadow',
            pos=(self.game.scene.width//2, self.game.scene.height//2),
            color=(1, 1, 1, 0),
        )

        self.last_message = ()
        self.message_sprites = []

        self.reset()

    async def anim_flame(self, s, i, x, y):
        while True:
            d = uniform(0.5, 1.5)
            sxs = sx = uniform(.2, .4)
            if i % 2:
                sxs = -sx
            await animate(
                s, duration=d,
                scale_x=sxs, scale_y=uniform(.2, 1) * sx,
                angle=uniform(-tau/8, tau/8),
                pos=(x+uniform(-3, 3), y+uniform(-3, 3)),
            )


    def reset(self):
        self.on_wealth_changed()
        self.update_help()
        self.reset_display()

    def on_key_down(self, key):
        if self.input_frozen:
            return
        if key == key.ESCAPE:
            if self.last_selected is None:
                exit()
            self.deselect()
            return True
        if key == key.DOWN:
            self.move_cursor(1)
        if key == key.UP:
            self.move_cursor(-1)
        if (num := KEY_NUMBERS.get(key)) is not None:
            if 1 <= num <= 5 and self.game.info.known_actions[num - 1]:
                self.last_selected = num - 1
            self.update_help()
        if key == key.SPACE:
            if self.last_selected is not None and self.affordable[self.last_selected]:
                self.game.go_do(self.last_selected)
            else:
                self.last_selected = 0
                self.update_help()

    def deselect(self):
        self.last_selected = None
        self.update_help()

    def move_cursor(self, direction=1):
        if self.last_selected is None:
            self.last_selected = 0
        else:
            n = self.last_selected
            for i in range(5):
                num = (n + (i + 1) * direction) % 5
                if self.affordable[num]:
                    self.last_selected = num
                    break
        self.update_help()

    def update_help(self):
        if self.last_selected and not self.game.info.known_actions[self.last_selected]:
            self.last_selected = None

        for bg_sprite, label, affordable, kbd_icon, cost_icon, known in zip(
            self.bg_sprites, self.caption_labels, self.affordable,
            self.keyboard_icons, self.cost_icons,
            self.game.info.known_actions
        ):
            objs1 = (*cost_icon, )
            objs2 = (*kbd_icon,)
            if affordable:
                label.color = (1, 1, 1, 1)
                bg_sprite.color = .5, .5, .5, 1
                for o in objs1: o.color = (*o.color[:3], 1)
                for o in objs2: o.color = (*o.color[:3], 1)
            elif known:
                label.color = (1, 1, 1, .5)
                bg_sprite.color = .5, .5, .5, .9
                for o in objs1: o.color = (*o.color[:3], .9)
                for o in objs2: o.color = (*o.color[:3], 1)
            else:
                label.color = (1, 1, 1, 0)
                bg_sprite.color = .5, .5, .5, 0
                for o in objs1: o.color = (*o.color[:3], 0)
                for o in objs2: o.color = (*o.color[:3], 0)
            change_sprite_image(bg_sprite, 'action_bg')

        if self.last_selected is None: # or not self.affordable[self.last_selected]:
            color = (*THAT_BLUE, 0)
            animate(self.bg_rect, color=(1, 1, 1, 0), duration=0.1)
            animate(self.caption_label, color=color, duration=0.1)
            for label in self.description_labels:
                animate(label, color=color, duration=0.1)
            for o in self.space_instruction_objs:
                o.color=(*o.color[:3], 0)
        else:
            num = self.last_selected
            if self.affordable[self.last_selected]:
                color = (*THAT_BLUE, 1)
            else:
                color = (.5, .5, .5, 1)
            action = self.actions[num]
            animate(self.bg_rect, color=(.9, .9, .93, 0.98), duration=0.1)
            self.caption_label.text = action.caption
            animate(self.caption_label, color=color, duration=0.1)
            for label, text in zip_longest(self.description_labels, action.description, fillvalue=''):
                label.text = text
                animate(label, color=color, duration=0.1)

            if self.affordable[self.last_selected]:
                for o in self.space_instruction_objs:
                    o.color=(*o.color[:3], 1)

                self.caption_labels[num].color = THAT_BLUE
                change_sprite_image(self.bg_sprites[num], 'selected_bg')
                self.bg_sprites[num].color = 1, 1, 1, 1
            else:
                for o in self.space_instruction_objs:
                    o.color=(*o.color[:3], 0)


    def on_wealth_changed(self):
        dirty = False
        def set_ka(index, known, affordable):
            nonlocal dirty
            if affordable and index and info.food <= 1:
                affordable = False
            if known:
                if info.learn_action(index):
                    dirty = True
            ka = known and affordable
            if self.affordable[index] != ka:
                self.affordable[index] = ka
                dirty = True

        info = self.game.info
        set_ka(0, True, True)
        set_ka(1, info.food >= 2 and (info.cube >= 1 or info.magic >= 1), info.cube >= 1)
        set_ka(2, info.food >= 2 and (info.food >= 5 or info.magic >= 1), info.magic >= 2)
        set_ka(3, info.food >= 2 and (info.thing >= 1 or info.magic >= 5), info.thing >= 1)
        set_ka(4, info.food >= 2 and info.magic >= 10, info.magic >= 30)

        if dirty:
            self.reset()

    def reset_display(self):
        info = self.game.info
        space_label = self.space_instruction_objs[1]
        things = tuple((info.things[i], p) for p, i in enumerate(info.display) if i != None)
        if things:
            print(things)
            if self.last_message == things:
                return
            while self.message_sprites:
                self.message_sprites.pop().delete()
            self.shadow_sprite.color = 1, 1, 1, 1
            for thing, p in things:
                sprites_now = []
                max_x = max_y = 0
                for x, y, image, angle in get_thing_sprite_info(thing):
                    s = self.shade_layer.add_sprite(
                        image, angle=angle,
                        pos=(390 + (p*5 + x) * 16, 215 + y * 16),
                        scale=1/4+1/64,
                        color=(1, 1, 1, 1),
                    )
                    sprites_now.append(s)
                    if x > max_x: max_x = x
                    if y > max_y: max_y = y
                    s = self.thing_layer.add_sprite(
                        image, angle=angle,
                        pos=(450 + (p*5 + x) * 5, 445 + y * 5),
                        scale=1/16+2/64,
                        color=(0, 0, 0, 1),
                    )
                    sprites_now.append(s)
                self.message_sprites.extend(sprites_now)
                for s in sprites_now:
                    s.x += (3-max_x)/2 * 64 * s.scale_x
                    s.y += (4-max_y) * 64 * s.scale_x
            space_label.color = 1, 1, 1, space_label.color[-1]
        else:
            while self.message_sprites:
                self.message_sprites.pop().delete()
            self.shadow_sprite.color = 1, 1, 1, 0
            space_label.color = (*THAT_BLUE, space_label.color[-1])
        self.last_message = things

    def fire_missile(self):
        self.deselect()
        self.game.info.magic -= 30
        scene = self.game.scene
        chain = scene.chain
        camera = scene.camera
        prev_pos = camera.pos
        mask_fill = self.game.set_missile_chain()
        clock.schedule(
            lambda: animate(mask_fill, color=(1, 1, 1, 0), duration=2, tween='accelerate'),
            2,
            strong=True,
        )
        async def anim():
            self.input_frozen = True
            try:
                missile_layer = scene.layers[1]
                sparks_layer = scene.layers[2]
                sprite = missile_layer.add_sprite(
                    'blur_circle',
                    pos=FIRE_POS,
                    scale=1/6,
                )
                pg = sparks_layer.add_particle_group(
                    'magic_particle', grow=0.9, max_age=3, spin_drag=1.1,
                    gravity=numpy.array([0, -4]),
                )
                pg.add_color_stop(0, (1, 1, 1))
                pg.add_color_stop(0.2, (0, 1, 1))
                pg.add_color_stop(1, (1, 0, 1))
                pg.add_color_stop(2, (1, 1, 0, 1))
                pg.add_color_stop(3, (1, 1, 0, 0))
                em = pg.add_emitter(
                    rate=50, pos=FIRE_POS, pos_spread=(3, 3), vel=(0, 0),
                    emit_angle_spread=tau,
                    vel_spread=(16, 16), size=15, size_spread=5,
                    spin_spread=tau/4,
                )

                duration = 8
                async for t in clock.coro.frames(seconds=duration):
                    print(t)
                    t /= duration
                    anit = t * t
                    camera.pos = scene.width/2, scene.height/2 - anit * scene.height*2
                    sprite.pos = em.pos = FIRE_POS[0], FIRE_POS[1] - anit * (scene.height*2 + 400)
                    em.vel = 0, -t * 400
                    em.rate = max(0, (.7 - t) * 50)
                em.vel = 0, 0
                pg.gravity = numpy.array([0, 200])
                pg.emit(
                    400, pos=em.pos, vel=(0, 0), vel_spread=(300, 300),
                    spin_spread=tau/4,
                    angle_spread=tau, size=20, size_spread=10,
                )
                sparks_layer.set_effect('trails', fade=0.5)
                await animate(sprite, scale=3, color=(1, 1, 1, 0), duration=2, tween='decelerate')
                await clock.coro.sleep(4)
                cam_x, cam_y = camera.pos
                if self.game.info.message_assembled:
                    for i, line in enumerate((
                        "The explosion, combined with your message,",
                        "got the attention of a broom-mounted,",
                        "teleport-savvy savior.",
                        "You made it out alive and well – just with",
                        "a lifetime ban on any more magic parties.",
                    )):
                        l = missile_layer.add_label(
                            line,
                            font='kufam_medium',
                            align='center',
                            pos=(cam_x, cam_y + i * 32),
                            color=(1, 1, 1, 0),
                            fontsize=15,
                        )
                        animate(l, color=(1, 1, 1, 1))
                    l = missile_layer.add_label(
                        'Congratulations!',
                        font='kufam_medium',
                        align='center',
                        pos=(cam_x, cam_y - 64),
                        color=(1, 1, 1, 1),
                        fontsize=50,
                    )
                    animate(l, color=(1, 1, 1, 1))
                    await clock.coro.sleep(3600)
                duration = 2
                async for t in clock.coro.frames(seconds=duration):
                    t /= duration
                    camera.pos = scene.width/2, scene.height/2 - (1-t) * scene.height*2
                await animate(mask_fill, color=(1, 1, 1, 1), duration=.2, tween='accelerate')
                sparks_layer.clear_effect()
            finally:
                scene.chain = chain
                camera.pos = prev_pos
                del scene.layers[1]
                del scene.layers[2]
                self.input_frozen = False
        clock.coro.run(anim())
