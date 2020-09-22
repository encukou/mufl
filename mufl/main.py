from math import hypot
from wasabi2d import animate, event, Scene, run, tone, keys, chain

from .fishy import Fishing

scene = Scene(title='Cast Away!', icon='fish')
scene.background = 0.9, 0.9, 1.0

def finish_fish():
    circ = scene.layers[10].add_sprite(
        'blur_circle',
        scale=hypot(scene.width, scene.height)//2 / 50,
        pos=(scene.width//2, scene.height*0.55),
    )
    animate(circ, scale=100/64, duration=5, tween='accelerate')
    scene.chain = [
        chain.Fill(color=(.1, .1, .1, 1)),
        chain.Mask(
            mask=chain.Layers([10]),
            paint=[chain.Fill(color=scene.background), chain.LayerRange(stop=5)],
        ),
    ]

fishing = Fishing(
    scene, scene.layers[1], scene.layers[2], scene.layers[3],
    on_finish=finish_fish,
)
scene.layers[0].set_effect('dropshadow')

@event
def on_key_down(key, mod):
    if key == keys.ESCAPE:
        exit()

run()
