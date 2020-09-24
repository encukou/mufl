from math import tau, sqrt, sin, cos, atan2, hypot
import pkgutil
from dataclasses import dataclass
from itertools import chain
from random import uniform
from contextlib import contextmanager

import moderngl
from wasabi2d.allocators.packed import PackedBuffer
from wasabi2d import clock
import numpy
import numpy as np
from pyrr import Quaternion, Vector3

# Parts pilfered from wasabi2d/primitives/sprites.py

DAMPING = 0.9

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
    return np.array([cos(angle), sin(angle), 2]) * uniform(3, 6)

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
        self.pos = numpy.array([250.+150*i, 250., 50.])
        self.speed = get_rand_speed()
        self.size = 24
        self.r = sqrt(3) * self.size
        self.gravity = 10

        self.layer = layer
        self._dirty = True
        layer.objects.add(self)
        layer._dirty.add(self)
        self.texregion = layer.group.atlas.get('die')

        self.prog = load_program(self.layer.group.shadermgr)

        self._set_img()

        clock.each_tick(self.advance)

    def randomize_rotation(self):
        self.rotation_speed = (
            Quaternion.from_x_rotation(uniform(0, tau))
            * Quaternion.from_y_rotation(uniform(0, tau))
            * Quaternion.from_z_rotation(uniform(0, tau))
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
        self.pos += self.speed
        r = self.r
        self._try_bounce(self.pos[0], (1, 0, 0))
        self._try_bounce(self.scene.width - self.pos[0], (-1, 0, 0))
        self._try_bounce(self.pos[1], (0, 1, 0))
        self._try_bounce(self.scene.height - self.pos[1], (0, -1, 0))
        self._try_bounce(self.pos[2], (0, 0, 1))
        try:
            self.rotation *= self.rotation_speed.power(dt)
        except AssertionError as e:
            print('AssertionError in quaternion power:', e)
            pass
        self.speed *= 0.9 ** dt
        self.speed[2] -= self.gravity * dt

    def _try_bounce(self, dist, norm):
        if dist > self.r:
            return
        norm = numpy.array(norm)
        if self.bounce(dist, norm):
            for i in range(3):
                self.speed = self.speed - 2 * self.speed.dot(norm) * norm
                if norm.dot(self.speed):
                    break
            self.pos += (self.r - dist) * norm

    def bounce(self, dist, norm=(0, 0, 1)):
        rot = self.rotation
        rot_mat = rot.matrix33
        low_pt = 0, 0, 0
        for xp in -1, 1:
            for yp in -1, 1:
                for zp in -1, 1:
                    point = rot_mat * Vector3([xp, yp, zp])
                    if point[2] < low_pt[2]:
                        low_pt = point
        if low_pt[2] >= dist:
            return False
        rot_imp = Vector3(norm).cross(Vector3((*low_pt.xy, 0.0))) * (.5 + hypot(*self.speed) / 10)
        riq = Quaternion.from_axis(rot_imp)
        ump = -Vector3(self.speed).cross(norm)
        umpq = Quaternion.from_axis(ump)
        self.rotation_speed = Quaternion().lerp(umpq * riq * self.rotation_speed, 0.7)
        self.speed *= 0.9
        return True

class DiceThrowing:
    def __init__(self, game, on_finish):
        self.game = game
        self.on_finish = on_finish

        dice_layer = game.scene.layers[1]
        for i in range(3):
            Die(self, dice_layer, i)
