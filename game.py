from math import hypot
from wasabi2d import animate, event, Scene, run, tone

from fishy import FishSpawner

scene = Scene()
scene.background = 0.9, 0.9, 1.0

scene.layers[0].set_effect('dropshadow')
circle = scene.layers[0].add_circle(
    radius=30,
    pos=(400, 300),
    color='red',
)

@event
def on_mouse_move(pos):
    circle.pos = pos


@event
def on_mouse_down(pos):
    mouse_x, mouse_y = pos
    cx, cy = circle.pos

    hit = hypot(mouse_x - cx, mouse_y - cy) < circle.radius

    if hit:
        circle.radius = 50
        animate(circle, 'bounce_end', radius=30)
        tone.play(440/3, 0.5, volume=0.4)

FishSpawner(scene, scene.layers[1])
scene.layers[0].set_effect('dropshadow')

run()
