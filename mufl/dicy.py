from math import tau
import pkgutil
from dataclasses import dataclass
from itertools import chain

import moderngl
from wasabi2d.allocators.packed import PackedBuffer
from wasabi2d import clock
import numpy as np
from pyrr import Quaternion

# Parts pilfered from wasabi2d/primitives/sprites.py

QUAD = np.array([0, 1, 2, 0, 2, 3], dtype='u4')

CUBE_VERTS = np.array([
    [-1, -1, -1],
    [ 1, -1, -1],
    [ 1,  1, -1],
    [-1,  1, -1],
], dtype='i4')
CUBE_INDEXES = np.array([
    0, 1, 2, 0, 3, 2,
], dtype='u4')
CUBE_UV = np.array([
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
], dtype='u4')
CUBE_NORM = np.array([
    *[[0, 0, -1]] * 4,
])


@dataclass
class TextureContext:
    tex: moderngl.Texture
    prog: moderngl.Program
    ctx: moderngl.Context

    def __enter__(self):
        """Bind the given texture to the given program during the context."""
        self.prog['tex'].value = 0
        self.tex.use(0)
        self.ctx.front_face = 'cw'
        self.ctx.cull_face = 'back'
        self.ctx.enable(moderngl.CULL_FACE)

    def __exit__(self, *_):
        self.ctx.disable(moderngl.CULL_FACE)

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

class Die:
    def __init__(self, layer):
        self.rotation = Quaternion()
        self.rotation_speed = Quaternion.from_x_rotation(tau/2) * Quaternion.from_y_rotation(3/4)

        self.layer = layer
        self._dirty = True
        layer.objects.add(self)
        layer._dirty.add(self)
        self.texregion = layer.group.atlas.get('die')

        self.prog = load_program(self.layer.group.shadermgr)

        self._set_img()

        clock.each_tick(self.rotate)

    def _update(self):
        self._array = self._get_array(self.texregion.tex)

        verts = self._array.get_verts(self._array_id)
        verts['in_color'][:] = 1, 0, 1, 1

        tc = self.texregion.texcoords[1::2, :].copy()
        add = tc[1]
        mul = (tc[0] - tc[1])
        mul[0] //= 5
        verts['in_uv'][:] = CUBE_UV * mul + add
        verts['in_vert'][:] = CUBE_VERTS
        verts['in_norm'][:] = CUBE_NORM

    def _get_array(self, tex):
        k = ('mufl', 'die', id(tex))
        array = self.layer.arrays.get(k)
        if not array:
            prog = load_program(self.layer.group.shadermgr)
            array = PackedBuffer(
                moderngl.TRIANGLE_STRIP,
                self.layer.ctx,
                prog,
                dtype=np.dtype([
                    ('in_vert', '3f4'),
                    ('in_color', '4f2'),
                    ('in_uv', '2u2'),
                    ('in_norm', '3f2'),
                ]),
                draw_context=TextureContext(tex, prog, self.layer.ctx),
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

    def rotate(self, dt):
        try:
            self.rotation *= self.rotation_speed.power(dt)
        except AssertionError as e:
            print('AssertionError in quaternion power:', e)
            pass
        self.prog['pos'] = 50, 50
        self.prog['rot'] = tuple(chain(*self.rotation.matrix44))

class DiceThrowing:
    def __init__(self, game, on_finish):
        self.game = game
        self.on_finish = on_finish

        dice_layer = game.scene.layers[1]
        Die(dice_layer)
