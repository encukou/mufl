from math import tau, sqrt, sin, cos, atan2, hypot
import pkgutil
from dataclasses import dataclass
from itertools import chain
from random import uniform
from contextlib import contextmanager

import moderngl
from wasabi2d.allocators.packed import PackedBuffer
from wasabi2d import clock, keyboard
import numpy
import numpy as np
from numpy.linalg import norm as linalg_norm
from pyrr import Quaternion, Vector3

# Parts pilfered from wasabi2d/primitives/sprites.py

DAMPING = 0.9
DAMPING_BOUNCE = 0.7

UP = Vector3((0, 0, 1))

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
    return np.array([cos(angle), sin(angle), 1]) * uniform(6, 12)

class Die:
    def __init__(self, throwing, layer, i):
        self.throwing = throwing
        self.scene = throwing.game.scene
        self.rotation = Quaternion()
        self.rotation = (
            Quaternion.from_x_rotation(uniform(0, tau))
            * Quaternion.from_x_rotation(uniform(0, tau))
            * Quaternion.from_x_rotation(uniform(0, tau))
        )
        self.randomize_rotation()
        self.pos = numpy.array([250.+150*(i//4), 250.+50*(i%4), 150.])
        self.speed = get_rand_speed()
        self.size = 24
        self.r = sqrt(3) * self.size
        self.sq_r = self.r ** 2
        self.gravity = 20
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

    def randomize_rotation(self):
        self.rotation_speed = (
            Quaternion.from_x_rotation(uniform(0, tau*5))
            * Quaternion.from_y_rotation(uniform(0, tau*5))
            * Quaternion.from_z_rotation(uniform(0, tau*5))
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
            if aa[face_arg] > 0.98:
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
            print('BOOM!')
            dist = sqrt(sq_dist)

            direction = sep / linalg_norm(sep)
            print(dist, direction)
            if self.bounce(dist, direction):
                self.speed += direction * 20
            if other.bounce(dist, -direction):
                self.speed -= direction * 20

class DiceThrowing:
    def __init__(self, game, on_finish):
        self.game = game
        self.on_finish = on_finish

        dice_layer = game.scene.layers[1]
        dice_layer.set_effect('dropshadow', radius=3, opacity=2, offset=(0, 0))
        self.dice = [Die(self, dice_layer, i) for i in range(10)]

        clock.each_tick(self.collide)

    def collide(self, dt):
        #print([die.face for die in self.dice])
        to_collide = []
        for die in self.dice:
            for other in to_collide:
                die.collide(other)
            to_collide.append(die)
