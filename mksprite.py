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

mksprite(8, 0, 2, 2, 'worm_segment')
mksprite(10, 0, 2, 2, 'blur_circle')
mksprite(12, 0, 1.5, 1, 'kbd_arrows')
mksprite(13.5, 0, 1.5, 0.5, 'kbd_space')
mksprite(15, 0, 1, 1, 'sea')
mksprite(13.5, 0.5, 1, 1.5, 'sel_cursor')
mksprite(14.5, 0.5, 0.5, 0.5, 'kbd_empty')

mksprite(0, 1, 0.5, 0.5, 'fish_mouth')
mksprite(0.5, 1, 0.5, 0.5, 'fin')
mksprite(1, 1, 0.5, 0.5, 'bubble')
mksprite(1.5, 1, 0.5, 0.5, 'food')
mksprite(2, 1, 0.5, 0.5, 'magic')
mksprite(2.5, 1, 0.5, 0.5, 'cube')
mksprite(3, 1, 0.5, 0.5, 'nada')
mksprite(3.5, 1, 0.5, 0.5, 'thing')
mksprite(4, 1, 1, 1, 'magic_particle')
mksprite(7, 1, 1, 1, 'flame')

mksprite(5, 1, 2, 2, 'hypno')
mksprite(12, 1, 1, 1, 'logo')
mksprite(15, 1, 1, 1, 'molten')

mksprite(0, 1.5, 0.5, 0.5, 'arrow')
mksprite(0.5, 1.5, 0.5, 0.5, 'arrow_guide')
mksprite(1, 1.5, 0.5, 0.5, 'nada_guide')

mksprite(0, 2, 1, 1, 'die_front')
mksprite(1, 2, 1, 1, 'die_side')
mksprite(2, 2, 1, 1, 'die_back')
mksprite(3, 2, 1, 1, 'die_top')
mksprite(4, 2, 1, 1, 'die_bottom')
mksprite(7, 2, 1, 1.5, 'card')
mksprite(8, 2, 1, 1.5, 'card_back')
mksprite(9, 2, 1, 1.5, 'card_foot')
mksprite(10, 2, 1, 1.5, 'card_right')
mksprite(11, 2, 1, 1.5, 'card_left')

mksprite(12, 2, 4, 1.5, 'action_bg')

mksprite(10, 3.5, 2, 1.5, 'thing_bg')
mksprite(12, 3.5, 4, 1.5, 'selected_bg')

mksprite(0, 3, 1, 1, 'block_10000')
mksprite(1, 3, 1, 1, 'block_11000')
mksprite(2, 3, 1, 1, 'block_11100')
mksprite(3, 3, 1, 1, 'block_11010')
mksprite(4, 3, 1, 1, 'block_11110')
mksprite(5, 3, 1, 1, 'block_11111')
mksprite(0, 4, 1, 1, 'block_00000')
mksprite(1, 4, 1, 1, 'block_01000')
mksprite(2, 4, 1, 1, 'block_01100')
mksprite(3, 4, 1, 1, 'block_01010')
mksprite(4, 4, 1, 1, 'block_01110')
mksprite(5, 4, 1, 1, 'block_01111')


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
