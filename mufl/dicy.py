import pkgutil
from dataclasses import dataclass

import moderngl
from wasabi2d.allocators.packed import PackedBuffer
import numpy as np

# Parts pilfered from wasabi2d/primitives/sprites.py

QUAD = np.array([0, 1, 2, 0, 2, 3], dtype='u4')


@dataclass
class TextureContext:
    tex: moderngl.Texture
    prog: moderngl.Program

    def __enter__(self):
        """Bind the given texture to the given program during the context."""
        self.prog['tex'].value = 0
        self.tex.use(0)

    def __exit__(self, *_):
        pass

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
        self.layer = layer
        self._dirty = True
        layer.objects.add(self)
        layer._dirty.add(self)
        self.texregion = layer.group.atlas.get('die')

        load_program(self.layer.group.shadermgr)

        self._set_img()

    def _update(self):
        self._array = self._get_array(self.texregion.tex)

        verts = self._array.get_verts(self._array_id)
        verts['in_color'][:] = 1, 0, 1, 1
        verts['in_uv'][:] = self.texregion.texcoords
        verts['in_vert'][:] = self.orig_verts[:, :2]

    def _get_array(self, tex):
        k = ('mufl', 'die', id(tex))
        array = self.layer.arrays.get(k)
        if not array:
            prog = load_program(self.layer.group.shadermgr)
            array = PackedBuffer(
                moderngl.TRIANGLES,
                self.layer.ctx,
                prog,
                dtype=np.dtype([
                    ('in_vert', '2f4'),
                    ('in_color', '4f2'),
                    ('in_uv', '2u2'),
                ]),
                draw_context=TextureContext(tex, prog),
            )
            self.layer.arrays[k] = array
        return array

    def _set_img(self):
        """Set the image."""
        texregion = self.texregion
        self.uvs = texregion.texcoords
        self.orig_verts = texregion.get_verts(0, 0)
        xs = self.orig_verts[:, 0]
        ys = self.orig_verts[:, 1]

        self._dirty = True

        tex = self.texregion.tex

        # migrate into a new array
        self._array = self._get_array(tex)
        self._array_id, _ = self._array.alloc(4, QUAD)

class DiceThrowing:
    def __init__(self, game, on_finish):
        self.game = game
        self.on_finish = on_finish

        dice_layer = game.scene.layers[1]
        Die(dice_layer)
