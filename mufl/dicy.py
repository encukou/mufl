from math import tau, sqrt, sin, cos, atan2, hypot
import pkgutil
from dataclasses import dataclass
from itertools import chain
from random import uniform
from contextlib import contextmanager
from collections import Counter

import moderngl
from wasabi2d.allocators.packed import PackedBuffer
from wasabi2d import clock, keyboard, animate, keys
import numpy
import numpy as np
from numpy.linalg import norm as linalg_norm
from pyrr import Quaternion, Vector3

from .info import COLORS as BONUS_COLORS
from .common import add_key_icon, add_space_instruction, KEY_NUMBERS

# Parts pilfered from wasabi2d/primitives/sprites.py

DAMPING = 0.9
DAMPING_BOUNCE = 0.7

UP = Vector3((0, 0, 1))
DIE_SIZE = 24

CUBE_VERTS = np.array([
    [-1, -1,  1],
    [-1,  1,  1],
    [ 1,  1,  1],
    [ 1, -1,  1],

    [ 1, -1,  1],
    [ 1,  1,  1],
    [ 1,  1, -1],
    [ 1, -1, -1],

    [-1, -1, -1],
    [-1,  1, -1],
    [-1,  1,  1],
    [-1, -1,  1],

    [ 1, -1, -1],
    [ 1,  1, -1],
    [-1,  1, -1],
    [-1, -1, -1],

    [-1, -1, -1],
    [-1, -1,  1],
    [ 1, -1,  1],
    [ 1, -1, -1],

    [ 1,  1, -1],
    [ 1,  1,  1],
    [-1,  1,  1],
    [-1,  1, -1],
], dtype='i1')
CUBE_INDEXES = np.array([
     0, 1, 2, 0, 2, 3,
     4, 5, 6, 4, 6, 7,
     8, 9,10, 8,10,11,
    12,13,14,12,14,15,
    16,17,18,16,18,19,
    20,21,22,20,22,23,
], dtype='u4')
CUBE_UV = np.array([
    [0, 1],
    [0, 0],
    [1, 0],
    [1, 1],

    [1, 1],
    [1, 0],
    [2, 0],
    [2, 1],

    [2, 1],
    [2, 0],
    [1, 0],
    [1, 1],

    [2, 1],
    [2, 0],
    [3, 0],
    [3, 1],

    [3, 0],
    [3, 1],
    [4, 1],
    [4, 0],

    [4, 0],
    [4, 1],
    [5, 1],
    [5, 0],
], dtype='u4')


FACE_NAMES = (
    'die_front',
    'die_side',
    'die_back',
    'die_top',
    'die_bottom',
)
BONUSES = (
    {'magic': 2, 'food': 1},
    {'magic': 1},
    {},
    {'food': 1},
    {'food': 2},
)


@dataclass
class DrawContext:
    tex: moderngl.Texture
    prog: moderngl.Program
    die: 'Die'

    def __enter__(self):
        """Bind the given texture to the given program during the context."""
        self.prog['tex'].value = 0
        self.tex.use(0)
        self.die.layer.ctx.front_face = 'cw'
        self.die.layer.ctx.cull_face = 'back'
        self.die.layer.ctx.enable(moderngl.CULL_FACE)
        self.die.prog['pos'] = tuple(self.die.pos)
        self.die.prog['rot'] = tuple(chain(*self.die.rotation.matrix44))
        self.die.prog['size'] = self.die.size * (1+self.die.pos[2]/600)
        self.die.prog['color'] = self.die.color

    def __exit__(self, *_):
        self.die.layer.ctx.disable(moderngl.CULL_FACE)

def load_program(mgr) -> moderngl.Program:
    names = ('die', 'die')
    if names in mgr.programs:
        return mgr.programs[names]

    frag_shader = pkgutil.get_data('mufl', 'glsl/die.frag').decode('utf-8')
    vert_shader = pkgutil.get_data('mufl', 'glsl/die.vert').decode('utf-8')
    prog = mgr.programs[names] = mgr.ctx.program(
        vertex_shader=vert_shader,
        fragment_shader=frag_shader,
    )
    return prog

def get_rand_speed():
    angle = uniform(0, tau)
    return np.array([cos(angle) * 2, sin(angle), 1]) * uniform(10, 15)

class Die:
    def __init__(self, throwing, layer, i, pos=None, gravity=20):
        self.throwing = throwing
        self.scene = throwing.game.scene
        self.rotation = Quaternion.from_x_rotation(tau/32) * Quaternion.from_y_rotation(tau*0.45)
        self.rotation_speed = Quaternion.from_y_rotation(1)
        self.pos = numpy.array([250.+150*(i//3), 250.+150*(i%3), 150.])
        if pos is not None:
            self.pos[:len(pos)] = pos
        self.speed = np.zeros(3)
        self.size = DIE_SIZE
        self.r = sqrt(3) * self.size
        self.sq_r = self.r ** 2
        self.gravity = gravity
        self.face = None
        self.locked = False

        self.layer = layer
        self._dirty = True
        layer.objects.add(self)
        layer._dirty.add(self)
        self.texregion = layer.group.atlas.get('die')

        self.prog = load_program(self.layer.group.shadermgr)

        self._set_img()

        clock.each_tick(self.advance)

        #self.speed[:] = 0
        #self.gravity=0
        #self.rotation_speed = Quaternion()
        #self.rotation = Quaternion()

        self.color = [(1,1,1),(0,0,1),(0,1,0),(1,0,0),(1,1,0),(0,1,1),(1,0,1),(0,0,0)][i%8]

    def roll(self):
        self.speed = get_rand_speed()
        self.randomize_rotation()
        self.gravity = 20

    def randomize_rotation(self):
        self.rotation_speed = (
            Quaternion.from_x_rotation(uniform(0, tau*15))
            * Quaternion.from_y_rotation(uniform(0, tau*15))
            * Quaternion.from_z_rotation(uniform(0, tau*15))
        )

    def _update(self):
        self._array = self._get_array(self.texregion.tex)

        verts = self._array.get_verts(self._array_id)

        tc = self.texregion.texcoords[1::2, :].copy()
        add = tc[1] + 1
        mul = (tc[0] - tc[1]) - 2
        mul[0] //= 5
        verts['in_uv'][:] = CUBE_UV * mul + add
        verts['in_vert'][:] = CUBE_VERTS

    def _get_array(self, tex):
        k = ('mufl', 'die', id(tex), id(self))
        array = self.layer.arrays.get(k)
        if not array:
            prog = load_program(self.layer.group.shadermgr)
            array = PackedBuffer(
                moderngl.TRIANGLES,
                self.layer.ctx,
                prog,
                dtype=np.dtype([
                    ('in_vert', '3i1'),
                    ('in_uv', '2u2'),
                ]),
                draw_context=DrawContext(tex, prog, self),
            )
            self.layer.arrays[k] = array
        return array

    def _set_img(self):
        """Set the image."""
        texregion = self.texregion
        self.uvs = texregion.texcoords
        self.orig_verts = CUBE_VERTS

        self._dirty = True

        tex = self.texregion.tex

        # migrate into a new array
        self._array = self._get_array(tex)
        self._array_id, _ = self._array.alloc(len(CUBE_VERTS), CUBE_INDEXES)

    def advance(self, dt):
        if self.locked:
            return
        if abs(sum(self.speed)) < 1 and self.rotation_speed.angle < 0.3:
            a = self.rotation.matrix33.inverse * UP
            aa = numpy.concatenate((a, -a))
            face_arg = aa.argmax()
            self.face = (1, 3, 2, 1, 4, 0)[face_arg]
            if aa[face_arg] > 0.99:
                self.locked = True
                self.pos[2] = self.r
                return
        if keyboard.keyboard.left:
            self.rotation *= Quaternion.from_y_rotation(-dt)
        if keyboard.keyboard.right:
            self.rotation *= Quaternion.from_y_rotation(dt)
        if keyboard.keyboard.up:
            self.rotation *= Quaternion.from_x_rotation(dt)
        if keyboard.keyboard.down:
            self.rotation *= Quaternion.from_x_rotation(-dt)
        self.pos += self.speed
        r = self.r
        self.bounce(self.pos[0], (1, 0, 0))
        self.bounce(self.scene.width - self.pos[0], (-1, 0, 0))
        self.bounce(self.pos[1], (0, 1, 0))
        self.bounce(self.scene.height - self.pos[1], (0, -1, 0))
        self.bounce(self.pos[2], (0, 0, 1))
        #self.bounce(hypot(self.pos[1] - self.pos[0]), (sqrt(1/2), -sqrt(1/2), 0))
        try:
            self.rotation *= self.rotation_speed.power(dt)
        except AssertionError as e:
            print('AssertionError in pyrr quaternion power:', e)
            pass
        self.speed *= DAMPING ** dt
        self.speed[2] -= self.gravity * dt

    def bounce(self, dist, norm):
        if dist > self.r:
            return False
        norm = numpy.array(norm)

        rot = self.rotation
        rot_mat = rot.matrix33
        low_pt = None
        for xp in -1, 1:
            for yp in -1, 1:
                for zp in -1, 1:
                    point = rot_mat * Vector3([xp, yp, zp])
                    if low_pt is None or point[2] < low_pt[2]:
                        low_pt = point
        if low_pt[2] >= dist:
            return False
        self.locked = False
        rot_imp = Vector3(norm).cross(Vector3((*low_pt.xy, 0.0))) * (.5 + hypot(*self.speed) / 10)
        riq = Quaternion.from_axis(rot_imp)
        ump = -Vector3(self.speed).cross(norm)
        umpq = Quaternion.from_axis(ump)
        if np.isnan(umpq).any():
            umpq = Quaternion()
        self.rotation_speed = Quaternion().lerp(umpq * riq * self.rotation_speed, 0.7)
        self.speed *= DAMPING_BOUNCE

        # Reflect speed
        if linalg_norm(norm) >= 2:
            1/0
        s = self.speed
        self.speed = s - 2 * s.dot(norm) * norm

        self.pos += (self.r - dist) * norm
        return True

    def collide(self, other):
        sep = self.pos - other.pos
        sq_dist = np.sum(sep ** 2., axis=-1) / 4
        if sq_dist <= self.sq_r:
            dist = sqrt(sq_dist)

            direction = sep / linalg_norm(sep)
            if self.bounce(dist, direction):
                self.speed += direction * 20
            if other.bounce(dist, -direction):
                self.speed -= direction * 20

class DiceThrowing:
    end_fadeout_scale = 0

    def __init__(self, game, on_finish):
        self.game = game
        self.on_finish = on_finish

        self.dice_layer = game.scene.layers[1]
        self.dice_layer.set_effect('dropshadow', radius=3, opacity=2, offset=(0, 0))

        self.line_layer = game.scene.layers[2]
        self.sel_layer = game.scene.layers[3]
        self.sel2_layer = game.scene.layers[4]

        self.dice = []
        self.selection = []
        self.select_dice()

        self.selecting = True

        #self.dice = [Die(self, dice_layer, i) for i in range(4)]

    def collide(self, dt):
        to_collide = []
        for die in self.dice:
            for other in to_collide:
                die.collide(other)
            to_collide.append(die)

        if all(d.locked for d in self.dice):
            for die in self.dice:
                bonuses = BONUSES[die.face]
                self.game.info.give(**bonuses, pos=die.pos[:2], sleep=0.5 + 0.5 * len(self.dice), outline=True, hoffset=0.5)

            def give_bonus_pairs(dt=None):
                to_check = set()
                for die in self.dice:
                    for other in set(to_check):
                        if die.face == other.face:
                            line = self.line_layer.add_line(
                                (die.pos[:2], other.pos[:2]),
                                color=(np.array(die.color) + other.color) / 2,
                                stroke_width=0,
                            )
                            to_check.discard(other)
                            animate(line, stroke_width=5)
                            bonuses = Counter(BONUSES[die.face]) + Counter(BONUSES[other.face]) + Counter(magic=3)
                            midpos = (die.pos[:2] + other.pos[:2]) / 2
                            self.game.info.give(**bonuses, pos=midpos, sleep=1.5, outline=True, hoffset=0.5)
                            animate(die, size=die.size*1.1)
                            animate(other, size=other.size*1.1)
                            break
                    else:
                        to_check.add(die)
                for left_die in set(to_check):
                    animate(left_die, size=left_die.size*0.99)
                self.on_finish(speedup=1.1)

            clock.unschedule(self.collide)
            clock.schedule(give_bonus_pairs, 0.5 * len(self.dice), strong=True)

    def on_key_down(self, key):
        if not self.selecting:
            return True
        if key in (keys.ESCAPE, keys.BACKSPACE):
            self.game.abort_activity()
            self.selecting = False
            return True
        elif key in (keys.SPACE, keys.RETURN):
            self.selecting = False
            self.dice = [d for d, v in zip(self.dice, self.selection) if v]
            for die in self.dice:
                die.roll()
            clock.each_tick(self.collide)
            del self.game.scene.layers[3]
            del self.game.scene.layers[4]
            self.game.info.magic -= sum(self.selection)
        if (num := KEY_NUMBERS.get(key)) is not None:
            self.toggle_die(num - 1)

    def toggle_die(self, number, time=1, recurse=True):
        try:
            fish_sprite = self.fish_sprites[number]
            die = self.dice[number]
            sel = self.selection[number]
        except KeyError:
            return
        if sel:
            self.selection[number] = False
            _anim(fish_sprite, 'decelerate', scale=0.5, duration=0.2*time)
            _anim(die, 'accelerate', size=0, duration=0.1*time)
        else:
            self.selection[number] = True
            _anim(fish_sprite, 'decelerate', scale=0, duration=0.2*time)
            _anim(die, 'decelerate', size=DIE_SIZE, duration=0.1*time)

        num_selected = sum(self.selection)
        for i, cost in enumerate(self.cost_sprites):
            if i < num_selected:
                _anim(cost, 'accelerate', scale=1, duration=0.1*time)
            else:
                _anim(cost, 'accelerate', scale=0, duration=0.1*time)

        if recurse:
            self.adjust_selection(number)

    def adjust_selection(self, avoid=None, time=1):
        num_selected = sum(self.selection)
        if num_selected > self.game.info.magic:
            for i, sel in reversed(list(enumerate(self.selection))):
                if sel and i != avoid:
                    self.toggle_die(i, recurse=False, time=time)
                    break
        if len(self.dice) == 1:
            avoid = None
        if num_selected < 1:
            for i, sel in list(enumerate(self.selection)):
                if not sel and i != avoid:
                    self.toggle_die(i, recurse=False, time=time)
                    return


    def select_dice(self):
        w = self.game.scene.width
        h = self.game.scene.height
        sel_layer = self.sel_layer

        selecting = self.game.info.cube > 1

        xpos = w//3
        if selecting:
            sel_layer.add_label('Select your dice', font='kufam_medium', pos=(xpos, 50), align='center', color=(0.1, 0.3, 0.8), fontsize=30)

        ysep = 80 + 10 * (6 - self.game.info.cube)
        ypos = 100 + ysep * (6 - self.game.info.cube) // 3
        self.fish_sprites = []
        for i in range(min(self.game.info.cube, 6)):
            while i >= len(self.game.info.boxfish):
                self.game.info.boxfish.append((0.9, 0.9, 0.9))
            die = Die(self, self.dice_layer, i, pos=(xpos, ypos, 50), gravity=0)
            color = self.game.info.boxfish[i]
            die.color = color
            self.dice.append(die)
            fish_sprite = sel_layer.add_sprite('fish_box', pos=(xpos, ypos), color=color, scale=0)
            self.fish_sprites.append(fish_sprite)
            self.selection.append(True)
            if selecting:
                add_key_icon(sel_layer, self.sel2_layer, xpos - 64-4, ypos, str(i+1))
            ypos += ysep

        xpos = w*5//6
        sel_layer.add_label('Rewards', font='kufam_medium', pos=(xpos, 50), align='center', color=(0.1, 0.3, 0.8), fontsize=30)

        color = (.96, .96, 1)
        ysep = 64 + 24
        ystart = 128 + 8
        for i, (name, bonuses) in enumerate(zip(FACE_NAMES, BONUSES)):
            sel_layer.add_sprite(name, pos=(xpos - 16, ystart + i * ysep), anchor_x=64, color=color)
            if bonuses:
                sel_layer.add_sprite('arrow', pos=(xpos, ystart + i * ysep), color=color)
            else:
                bonuses = {'nada': 1}
            maxamt = 2 # max(bonuses.values())
            for k, (kind, amount) in enumerate(bonuses.items()):
                sx = xpos + 16 + (maxamt - amount)/2 * 32
                for l in range(amount):
                    x = sx + l * 32
                    y = ystart + i * ysep + (k - (len(bonuses) - 1) / 2) * 24
                    sel_layer.add_sprite(kind, pos=(x, y), color=BONUS_COLORS[kind], anchor_x=0)
        i += 1
        y = ystart + i * ysep + 8
        if selecting:
            color = (0.1, 0.3, 0.8)
        else:
            color = (0.4, 0.4, 0.4)
            sel_layer.add_label('(with more dice)', font='kufam_medium', pos=(xpos, y), align='center', color=color, fontsize=15)
            y -= 16
        sel_layer.add_label('Bonus for matching pairs!', font='kufam_medium', pos=(xpos, y), align='center', color=color, fontsize=15)

        add_space_instruction(sel_layer, 'Roll for')

        self.cost_sprites = []
        for i in range(self.game.info.cube):
            s = sel_layer.add_sprite('magic', pos=(106+115 + i * 32, h-20), color=BONUS_COLORS['magic'])
            self.cost_sprites.append(s)

        for i in range(self.game.info.magic, len(self.cost_sprites)):
            self.adjust_selection(time=0)


def _anim(obj, *args, duration=1, **kwargs):
    if duration == 0:
        for name, value in kwargs.items():
            setattr(obj, name, value)
    else:
        animate(obj, *args, duration=duration, **kwargs)
