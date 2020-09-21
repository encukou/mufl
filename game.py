from math import hypot
from wasabi2d import animate, event, Scene, run, tone, keys

from fishy import Fishing

scene = Scene(title='Cast Away!', icon='fish')
scene.background = 0.9, 0.9, 1.0


fishing = Fishing(scene, scene.layers[1], scene.layers[2])
scene.layers[0].set_effect('dropshadow')

@event
def on_key_down(key, mod):
    if key == keys.ESCAPE:
        exit()

run()
