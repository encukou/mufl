from PIL import Image

base = Image.open('pics.png')

UNIT = 128

def mksprite(x, y, w, h, name):
    base.crop((UNIT*x, UNIT*y, UNIT*(x+w), UNIT*(y+h))).resize((int(UNIT*w/2), int(UNIT*h/2))).save(f'mufl/images/{name}.png')

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
mksprite(14.5, 0.5, 0.5, 0.5, 'kbd_empty')

mksprite(0, 1, 0.5, 0.5, 'fish_mouth')
mksprite(0.5, 1, 0.5, 0.5, 'fin')
mksprite(1, 1, 0.5, 0.5, 'bubble')
mksprite(1.5, 1, 0.5, 0.5, 'food')
mksprite(2, 1, 0.5, 0.5, 'magic')
mksprite(2.5, 1, 0.5, 0.5, 'cube')
mksprite(3, 1, 0.5, 0.5, 'nada')

mksprite(15, 1, 1, 1, 'logo')

mksprite(0, 2, 1, 1, 'die_front')
mksprite(1, 2, 1, 1, 'die_side')
mksprite(2, 2, 1, 1, 'die_back')
mksprite(3, 2, 1, 1, 'die_top')
mksprite(4, 2, 1, 1, 'die_bottom')
mksprite(5, 2, 1, 1, 'die_any')
mksprite(5, 2, 2.25, 1, 'die_equal')
mksprite(7.5, 2, 0.5, 0.5, 'arrow')


def mkdie():
    margin = 16*2
    side = UNIT - margin * 2
    result = Image.new('RGBA', (side * 5, side))
    for i in range(5):
        c = base.crop((
            i * UNIT + margin, 2 * UNIT + margin,
            (i+1) * UNIT - margin, 3 * UNIT - margin,
        ))
        result.paste(c, (i * side, 0))
    result.save('mufl/images/die.png')

mkdie()
