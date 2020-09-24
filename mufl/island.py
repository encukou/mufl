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
        cost = [int(s[1:]) if s.startswith('x') else s for s in lines[1].split()]
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
        self.held_keys = []

        self.bg_sprites = []

        ys = 8
        ysep = 110
        xpos = 192+6
        for i, action in enumerate(self.actions):
            s = self.bg_layer.add_sprite('action_bg', pos=(64, ys+16+i*ysep), anchor_x=0, anchor_y=0)
            self.bg_sprites.append(s)
            self.main_layer.add_label(action.caption, font='kufam_bold', pos=(xpos, ys+56+i*ysep), color=(1, 1, 1), align='center', fontsize=22)
            add_key_icon(self.main_layer, self.top_layer, xpos-128, ys+56+i*ysep-8+2, str(i+1))
            for j, item in enumerate(action.cost):
                x = xpos + (j - (len(action.cost)-1)/2) * 32
                y = ys+56+i*ysep+16+8
                if isinstance(item, int):
                    self.main_layer.add_label(f'×{item}', font='kufam_medium', pos=(x, y+8), color=(1, 1, 1), align='center', fontsize=15)
                else:
                    self.main_layer.add_sprite(item, pos=(x, y), color=BONUS_COLORS[item])

            add_space_instruction(self.bg_layer, 'Press Space to Start')

        self.bg_rect = add_rect_with_topleft_anchor(self.bg_layer, 360, ys+16, 400, ysep*4+64+32, color=(1, 1, 1, 0))
        self.caption_label = self.main_layer.add_label('', font='kufam_medium', pos=(560, ys+64), color=(THAT_BLUE), align='center', fontsize=22)
        self.description_labels = []
        for i in range(max(len(a.description) for a in self.actions)):
            lbl = self.main_layer.add_label('', font='kufam_medium', pos=(560, ys+64+i*30+64), color=(THAT_BLUE), align='center', fontsize=15)
            self.description_labels.append(lbl)

        self.reset()

    def reset(self):
        self.last_selected = None
        self.update_help()

    def on_key_down(self, key):
        if (num := KEY_NUMBERS.get(key)) is not None:
            if 1 <= num <= 5:
                self.held_keys.append(num-1)
        self.update_help()

    def on_key_up(self, key):
        if (num := KEY_NUMBERS.get(key)) is not None:
            if 1 <= num <= 5:
                try:
                    self.held_keys.remove(num-1)
                except ValueError:
                    pass
        self.update_help()

    def update_help(self):
        for sprite in self.bg_sprites:
            sprite.image = 'action_bg'

        try:
            num = self.held_keys[-1]
        except IndexError:
            self.last_selected = None
            color = (*THAT_BLUE, 0)
            animate(self.bg_rect, color=(1, 1, 1, 0), duration=0.1)
            animate(self.caption_label, color=color, duration=0.1)
            for label in self.description_labels:
                animate(label, color=color, duration=0.1)
        else:
            print(num, type(num))
            print(num)
            self.last_selected = num
            color = (*THAT_BLUE, 1)
            action = self.actions[num]
            animate(self.bg_rect, color=(1, 1, 1, (1-0.5 ** len(self.held_keys))), duration=0.1)
            self.caption_label.text = action.caption
            animate(self.caption_label, color=color, duration=0.1)
            for label, text in zip_longest(self.description_labels, action.description, fillvalue=''):
                label.text = text
                animate(label, color=color, duration=0.1)
            self.bg_sprites[num].image = 'selected_bg'

        #self.bg_sprites[2].image = 'selected_bg'
