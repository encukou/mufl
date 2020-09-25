from wasabi2d import clock, keyboard, animate, keys

KEY_NUMBERS = {
    keys.K_1: 1,
    keys.KP1: 1,
    keys.F1: 1,
    keys.K_2: 2,
    keys.KP2: 2,
    keys.F2: 2,
    keys.K_3: 3,
    keys.KP3: 3,
    keys.F3: 3,
    keys.K_4: 4,
    keys.KP4: 4,
    keys.F4: 4,
    keys.K_5: 5,
    keys.KP5: 5,
    keys.F5: 5,
    keys.K_6: 6,
    keys.KP6: 6,
    keys.F6: 6,
}

def add_key_icon(layer1, layer2, x, y, label):
    s = layer1.add_sprite('kbd_empty', pos=(x-4, y))
    l = layer2.add_label(label, font='kufam_medium', pos=(x, y+3), color=(0.1, 0.3, 0.8), fontsize=15, align='center')
    return s, l


def add_space_instruction(layer, text):
    h = 600
    s = layer.add_sprite('kbd_space', pos=(2, h-20), anchor_x=0)
    l=layer.add_label(text, font='kufam_medium', pos=(106, h-10), color=(0.1, 0.3, 0.8), fontsize=50)
    l.scale = 1/2
    return s, l

