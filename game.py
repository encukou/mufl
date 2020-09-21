from math import hypot
from wasabi2d import animate, event, Scene, run, tone

from fishy import Fishing

scene = Scene()
scene.background = 0.9, 0.9, 1.0


Fishing(scene, scene.layers[1])
scene.layers[0].set_effect('dropshadow')

run()
