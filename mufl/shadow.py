import string
from operator import itemgetter
from itertools import chain

from wasabi2d import Group, keys, clock

from .thing import get_thing_sprite_info
from .common import add_key_icon, add_space_instruction
from .fixes import animate

KEY_VALUES = {getattr(keys, k): k for k in string.ascii_uppercase}
for prefix in 'K_', 'KP_', 'F':
    for k in string.digits:
        if constant := getattr(keys, prefix + k, None):
            KEY_VALUES[constant] = k


class Shadowing:
    def __init__(self, game):
        self.game = game
        self.starting_display = list(self.game.info.display)

        self.backdrop_layer = game.scene.layers[0]
        self.ui_layer = game.scene.layers[1]
        self.menu_layer = self.display_layer = game.scene.layers[2]
        self.item_layer = self.display_layer = game.scene.layers[3]

        self.backdrop_layer.add_sprite('ledge', anchor_x=0, anchor_y=0)

        self.cursor_sprite = self.ui_layer.add_sprite('sel_cursor', pos=(self.cursor_pos(0)))

        self.selected_pos = 0

        self.things = {i: v for i, v in enumerate(self.game.info.things) if v}
        self.item_sprites = {}
        self.menu_sprites = {}
        self.item_bottoms = {}
        self.item_rights = {}
        self.menu_groups = {}
        self.item_groups = {}
        self.item_kbd_labels = {}
        self.item_shortcuts = {}
        self.assigned_shortcuts = {}
        for i, item in self.things.items():
            item_sprites = self.item_sprites[i] = {}
            menu_sprites = self.menu_sprites[i] = {}
            for x, y, image, angle in get_thing_sprite_info(item):
                s = self.menu_layer.add_sprite(image, pos=(x * 16, y * 16), angle=angle, scale=1/4+1/64, color=(.5, .5, .5, 1))
                menu_sprites[x, y] = s
                s = self.item_layer.add_sprite(image, pos=(x * 16, y * 16), angle=angle, scale=1/4+1/64, color=(0, 0, 0, 1))
                item_sprites[x, y] = s
            maxx = max(xy[0] for xy in item_sprites)
            maxy = max(xy[1] for xy in item_sprites)
            self.item_bottoms[i] = bot = 4 - maxy
            self.item_rights[i] = 3 - maxx
            for s in chain(item_sprites.values(), menu_sprites.values()):
                s.x += (3-maxx)/2 * 16
                s.y += bot/2 * 16
            thing_bg = self.ui_layer.add_sprite('thing_bg', color=(1, 1, 1, 0.5), pos=(0.5*16, 2*16))
            menu_group = self.menu_groups[i] = Group((*menu_sprites.values(), thing_bg))
            item_group = self.item_groups[i] = Group((*item_sprites.values(), ))
            item_group.pos = menu_group.pos = self.menu_pos(i)
            self.item_shortcuts[i] = []
            self.item_kbd_labels[x, y] = []
            self.assign_key(i, str((i + 1) % 10))

        for i, item in self.things.items():
            code, tileinfo, label = item.split(':')
            if len(label) == 1 and label in string.ascii_uppercase:
                self.assign_key(i, label)
        for i, item in self.things.items():
            code, tileinfo, label = item.split(':')
            if len(label) == 1 and label in string.ascii_lowercase:
                self.assign_key(i, label.upper())

        add_space_instruction(self.ui_layer, 'OK')

        for place, i in enumerate(self.starting_display):
            if i != None:
                self.anim_to_place(i, place, d=0.001)
        for place, i in enumerate(self.starting_display):
            if i == None:
                self.set_selection(place, d=0.001)
                break

    def assign_key(self, i, key):
        if key in self.assigned_shortcuts:
            return
        self.assigned_shortcuts[key] = i
        if key in KEY_VALUES.values():
            kbd_labels = add_key_icon(self.ui_layer, self.menu_layer, 24+8, 104 + len(self.item_shortcuts[i])*32, key)
            self.item_shortcuts[i].append(constant)
            self.menu_groups[i].extend(kbd_labels)

    def menu_pos(self, i):
        maxi = max(self.things)
        sep = 80 + 8 * (9 - maxi)
        w = 48
        return (self.game.scene.width - sep * (maxi) - w) / 2  + sep * i, 424 - 64

    def display_pos(self, i):
        return 144 + 144 * i - 6, 128 - 64

    def cursor_pos(self, i):
        return 208-16 + 144 * i, 320 - 64

    def on_key_down(self, key):
        if key == keys.ESCAPE:
            if self.game.info.display[self.selected_pos] != None:
                self.select(None)
                return
            self.end()
        elif key == keys.RIGHT:
            self.adjust_selection(+1)
        elif key == keys.LEFT:
            self.adjust_selection(-1)
        elif value := KEY_VALUES.get(key):
            if (i := self.assigned_shortcuts.get(value)) is not None:
                self.select(i)
        if key == keys.SPACE:
            self.end()

    def end(self):
        if self.starting_display == self.game.info.display:
            self.game.abort_activity()
        self.game.abort_activity(return_food=False, deselect=True)

    def select(self, i, place=None):
        if place is None:
            place = self.selected_pos
        if (prev := self.game.info.display[place]) != None:
            self.game.info.display[place] = None
            self.anim_to_menu(prev)
        if (thing := self.things.get(i)):
            for j, prev in enumerate(self.game.info.display):
                if prev == i:
                    if j != place:
                        self.select(None, j)
            self.game.info.display[place] = i
            self.anim_to_place(i, place)
            self.adjust_selection(1)
        print('That spells: ', self.game.info.message)

    def anim_to_place(self, i, place, d=1/4):
        group = self.item_groups[i]
        right = self.item_rights[i]
        bottom = self.item_bottoms[i]
        for (x, y), sprite in self.item_sprites[i].items():
            animate(sprite, pos=((x+right/2)*32, (y+bottom)*32), scale=1/2+1/64, duration=d, tween='decelerate')
        animate(group, pos=self.display_pos(place), duration=d)

    def anim_to_menu(self, i, d=1/4):
        group = self.item_groups[i]
        right = self.item_rights[i]
        bottom = self.item_bottoms[i]
        for (x, y), sprite in self.item_sprites[i].items():
            animate(sprite, pos=((x+right/2)*16, (y+bottom/2)*16), scale=1/4+1/64, duration=d, tween='accelerate')
        animate(group, pos=self.menu_pos(i), duration=d)

    def adjust_selection(self, adjustment):
        self.set_selection((self.selected_pos + adjustment) % 4)

    def set_selection(self, pos, d=1/4):
        self.selected_pos = pos
        animate(self.cursor_sprite, pos=self.cursor_pos(pos), duration=d, tween='accel_decel')
