from PIL import Image

base = Image.open('pics.png')

def mksprite(x, y, w, h, name):
    base.crop((64*x, 64*y, 64*(x+w), 64*(y+h))).save(f'mufl/images/{name}.png')

mksprite(0, 0, 2, 1, 'fish')
mksprite(2, 0, 0.5, 1, 'hook')
mksprite(2.5, 0, .5, 1, 'hook_in')
mksprite(3, 0, 2, 1, 'fish_scaly')
mksprite(5, 0, 2, 1, 'fish_crown')
mksprite(7, 0, 1, 1, 'fish_box')

mksprite(10, 0, 2, 2, 'blur_circle')
mksprite(12, 0, 1.5, 1, 'kbd_arrows')
mksprite(13.5, 0, 1.5, 0.5, 'kbd_space')
mksprite(15, 0, 1, 1, 'sea')

mksprite(0, 1, 0.5, 0.5, 'fish_mouth')
mksprite(0.5, 1, 0.5, 0.5, 'fin')
mksprite(1, 1, 0.5, 0.5, 'bubble')
mksprite(1.5, 1, 0.5, 0.5, 'food')
mksprite(2, 1, 0.5, 0.5, 'magic')
mksprite(2.5, 1, 0.5, 0.5, 'cube')
