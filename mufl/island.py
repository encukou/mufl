import pkgutil
from dataclasses import dataclass
from itertools import zip_longest

from wasabi2d import animate

from .info import COLORS as BONUS_COLORS
from .common import add_key_icon, add_space_instruction, KEY_NUMBERS

THAT_BLUE = 0.1, 0.3, 0.8

def add_rect_with_topleft_anchor(layer, x, y, w, h, **kwargs):
    return layer.add_rect(w, h, pos=(x+w/2, y+h/2), **kwargs)


@dataclass
class Action:
    caption: str
    cost: tuple
    description: list


def load_actions():
    actions = []
    PERFORATION = ' 8< '.center(42, '-')
    text = pkgutil.get_data('mufl', 'text/actions.txt').decode('utf-8')
    for txt in text.split(PERFORATION):
        txt = txt.strip()
        lines = txt.splitlines()
        cost = lines[1].split()
        assert not lines[2], lines[2]
        actions.append(Action(
            caption=lines[0],
            cost=tuple(cost),
            description=lines[3:],
        ))
    return actions


class Island:
    def __init__(self, game):
        self.actions = load_actions()
        self.game = game
        self.bg_layer = self.game.scene.layers[6]
        self.main_layer = self.game.scene.layers[7]
        self.top_layer = self.game.scene.layers[8]

        self.last_selected = None

        self.bg_sprites = []
        self.caption_labels = []
        self.keyboard_icons = []
        self.cost_icons = []

        ys = 0
        ysep = 110
        xpos = 192+6
        for i, action in enumerate(self.actions):
            s = self.bg_layer.add_sprite('action_bg', pos=(64, ys+16+i*ysep), anchor_x=0, anchor_y=0)
            self.bg_sprites.append(s)
            lbl = self.main_layer.add_label(action.caption, font='kufam_bold', pos=(xpos, ys+56+i*ysep), color=(1, 1, 1), align='center', fontsize=22)
            self.caption_labels.append(lbl)
            ki = add_key_icon(self.main_layer, self.top_layer, xpos-128, ys+56+i*ysep-8+2, str(i+1))
            self.keyboard_icons.append(ki)
            cost = action.cost
            if not cost:
                cost = ['free']
            cost_icons = []
            for j, item in enumerate(cost):
                x = xpos + (j - (len(cost)-1)/2) * 32 - 4
                y = ys+56+i*ysep+16+8
                if item in BONUS_COLORS:
                    o = self.main_layer.add_sprite(item, pos=(x, y), color=BONUS_COLORS[item])
                else:
                    o = self.main_layer.add_label(f'{item}', font='kufam_medium', pos=(x, y+8), color=(1, 1, 1), align='center', fontsize=15)
                cost_icons.append(o)
            self.cost_icons.append(cost_icons)

        self.space_instruction_objs = add_space_instruction(self.bg_layer, 'Press Space to Start')

        self.bg_rect = add_rect_with_topleft_anchor(self.bg_layer, 360, ys+16, 400, ysep*4+64+32, color=(1, 1, 1, 0))
        self.caption_label = self.main_layer.add_label('', font='kufam_medium', pos=(560, ys+64), color=(THAT_BLUE), align='center', fontsize=22)
        self.description_labels = []
        for i in range(max(len(a.description) for a in self.actions)):
            lbl = self.main_layer.add_label('', font='kufam_medium', pos=(560, ys+64+i*30+64), color=(THAT_BLUE), align='center', fontsize=15)
            self.description_labels.append(lbl)

        self.affordable = [False] * 5

        self.reset()

    def reset(self):
        self.on_wealth_changed()
        self.update_help()

    def on_key_down(self, key):
        if key == key.ESCAPE:
            if self.last_selected is None:
                exit()
            self.last_selected = None
            self.update_help()
            return True
        if key == key.DOWN:
            self.move_cursor(1)
        if key == key.UP:
            self.move_cursor(-1)
        if (num := KEY_NUMBERS.get(key)) is not None:
            if 1 <= num <= 5 and self.game.info.known_actions[num - 1]:
                self.last_selected = num - 1
            self.update_help()
        if key == key.SPACE:
            if self.last_selected is not None and self.affordable[self.last_selected]:
                self.game.go_do(self.last_selected)
            else:
                self.last_selected = 0
                self.update_help()

    def move_cursor(self, direction=1):
        if self.last_selected is None:
            self.last_selected = 0
        else:
            n = self.last_selected
            for i in range(5):
                num = (n + (i + 1) * direction) % 5
                if self.affordable[num]:
                    self.last_selected = num
                    break
        self.update_help()

    def update_help(self):
        if sum(self.affordable) == 1:
            self.last_selected = 0
        if self.last_selected and not self.game.info.known_actions[self.last_selected]:
            self.last_selected = None

        for bg_sprite, label, affordable, kbd_icon, cost_icon, known in zip(
            self.bg_sprites, self.caption_labels, self.affordable,
            self.keyboard_icons, self.cost_icons,
            self.game.info.known_actions
        ):
            objs1 = (*cost_icon, bg_sprite)
            objs2 = (*kbd_icon,)
            if affordable:
                label.color = (1, 1, 1, 1)
                for o in objs1: o.color = (*o.color[:3], 1)
                for o in objs2: o.color = (*o.color[:3], 1)
            elif known:
                label.color = (1, 1, 1, .5)
                for o in objs1: o.color = (*o.color[:3], .5)
                for o in objs2: o.color = (*o.color[:3], 0)
            else:
                label.color = (1, 1, 1, 0)
                for o in objs1: o.color = (*o.color[:3], 0)
                for o in objs2: o.color = (*o.color[:3], 0)
            change_sprite_image(bg_sprite, 'action_bg')

        if self.last_selected is None: # or not self.affordable[self.last_selected]:
            color = (*THAT_BLUE, 0)
            animate(self.bg_rect, color=(1, 1, 1, 0), duration=0.1)
            animate(self.caption_label, color=color, duration=0.1)
            for label in self.description_labels:
                animate(label, color=color, duration=0.1)
            for o in self.space_instruction_objs:
                animate(o, color=(*o.color[:3], 0), duration=0.1)
        else:
            num = self.last_selected
            if self.affordable[self.last_selected]:
                color = (*THAT_BLUE, 1)
            else:
                color = (.5, .5, .5, 1)
            action = self.actions[num]
            animate(self.bg_rect, color=(1, 1, 1, 0.5), duration=0.1)
            self.caption_label.text = action.caption
            animate(self.caption_label, color=color, duration=0.1)
            for label, text in zip_longest(self.description_labels, action.description, fillvalue=''):
                label.text = text
                animate(label, color=color, duration=0.1)

            if self.affordable[self.last_selected]:
                for o in self.space_instruction_objs:
                    animate(o, color=(*o.color[:3], 1), duration=0.1)

                self.caption_labels[num].color = THAT_BLUE
                change_sprite_image(self.bg_sprites[num], 'selected_bg')
            else:
                for o in self.space_instruction_objs:
                    animate(o, color=(*o.color[:3], 0), duration=0.1)


    def on_wealth_changed(self):
        dirty = False
        def set_ka(index, known, affordable):
            nonlocal dirty
            if known:
                if info.learn_action(index):
                    dirty = True
            ka = known and affordable
            if self.affordable[index] != ka:
                self.affordable[index] = ka
                dirty = True

        info = self.game.info
        set_ka(0, True, True)
        set_ka(1, info.magic >= 1 and info.food >= 1, info.cube >= 1)
        set_ka(2, info.magic >= 1, info.magic >= 2)
        set_ka(3, info.thing >= 1 or info.magic >= 5, info.thing >= 1)
        set_ka(4, info.magic >= 10, info.magic >= 30)

        if dirty:
            self.reset()

def change_sprite_image(sprite, image):
    "Workaround for https://github.com/lordmauve/wasabi2d/issues/55 "
    if sprite.image != image:
        sprite.image = image
        sprite._set_dirty()
