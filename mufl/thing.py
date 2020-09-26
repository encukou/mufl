from math import tau
from random import choice
import pkgutil
import string

from .common import change_sprite_image

ROTS = {
    (1, 0): 0,
    (0, 1): 1,
    (-1, 0): 2,
    (0, -1): 3,
}

SYMBOLS = {}
text = pkgutil.get_data('mufl', 'text/symbols.txt').decode('utf-8')
for line in text.splitlines():
    sym, codes = line.rsplit(maxsplit=1)
    for i in range(0, len(codes), 4):
        key = codes[i:i+4]
        SYMBOLS[key] = sym

def encode_letter(letter):
    enc = []
    for x in range(4):
        num = 0
        for y in range(5):
            num <<= 1
            if (x, y) in letter:
                num += 1
        enc.append(chr(48+num))
    return ''.join(enc)

class ThingTile:
    def __init__(self):
        self.filled = False
        self.corners = [False] * 4

    def get_sprite_info(self):
        fc = '01'[self.filled]
        num_corners = sum(self.corners)
        if num_corners == 0:
            return f'block_{fc}0000', 0
        elif num_corners == 1:
            return f'block_{fc}1000', tau/4 * self.corners.index(True)
        elif num_corners == 2:
            if self.corners == [True, False, True, False]:
                return f'block_{fc}1010', 0
            elif self.corners == [False, True, False, True]:
                return f'block_{fc}1010', tau/4
            elif self.corners == [True, False, False, True]:
                return f'block_{fc}1100', tau*3/4
            else:
                return f'block_{fc}1100', tau/4 * self.corners.index(True)
        elif num_corners == 3:
            return f'block_{fc}1110', tau/4 * (self.corners.index(False) + 2)
        else:
            return f'block_{fc}1111', 0

    def update_sprite(self, sprite):
        image, rotation = self.get_sprite_info()
        change_sprite_image(sprite, image)
        sprite.angle = rotation

    def set_wormy_corners(self, d, plus=0):
        rot = ROTS[d] + plus
        self.set_corner(rot)
        self.set_corner(rot-1)

    def set_corner(self, c):
        self.corners[c%4] = True

    def encode(self):
        num = int(self.filled)
        for corner in self.corners:
            num <<= 1
            num |= corner
        return chr(ord('0') + num)

    @classmethod
    def from_code(cls, code):
        self = cls()
        num = ord(code) - ord('0')
        for i, corner in reversed(list(enumerate(self.corners))):
            self.corners[i] = bool(num & 1)
            num >>= 1
        self.filled = bool(num & 1)
        return self

def encode_thing(thing):
    thingset = {pos for pos, tile in thing.items() if tile.filled}
    letter = encode_letter(thingset)
    tileset = ''.join(thing[x, y].encode() for x in range(4) for y in range(5))
    return f'{letter}-{tileset}-{SYMBOLS.get(letter, "")}'


def classify_thing(thing):
    shape = frozenset(pos for (pos, tile) in thing.items() if tile.filled)
    return encode_letter(shape)


def get_thing_sprite_info(thing_string):
    code, tileinfo, comment = thing_string.split('-')
    for i, c in enumerate(tileinfo):
        if c != '0':
            x = i // 5
            y = i % 5
            yield (x, y, *ThingTile.from_code(c).get_sprite_info())

def get_thing_mesage(encoded):
    sym = SYMBOLS.get(encoded)
    def cls(*choices):
        return choice(list(set((choices))))
    usefuls = (
        "It doesn't look useful.",
        "Probably not too useful here.",
        "Probably not too useful.",
        "In other words, trash.",
        "It doesn't look useful here.",
        "You don't know what to do with that.",
        "You don't see how it can be useful here.",
    )
    if sym is None:
        ci = cls('a curious', 'an interesting', 'a weird')
        useful = cls(*usefuls)
        useful_waste = cls(
            *usefuls,
            "A waste of metal.",
            "A waste of material.",
            "Frankly, this is a waste of metal.",
        )
        return cls(
            f"That doesn't remind you of anything.\n{useful_waste}",
            f"It's… um… modern art?\n{useful_waste}",
            f"Doesn't look familiar.\n{useful_waste}",
            f"That's {ci} piece of metal.\n{useful}",
            f"That's {ci} hunk of metal.\n{useful}",
        )
    if sym == 'box':
        return cls(
            f"A roughly rectangular piece of metal.",
        ) + "\n" + cls(*usefuls)
    elif sym == '.':
        return cls(
            f"A tiny bit of metal.",
        ) + "\n" + cls(*usefuls)
    elif len(sym) == 1:
        if sym in string.ascii_uppercase:
            letrune = choice(('letter', 'rune'))
            message = cls(
                f"That is the {letrune} {sym}!",
                f"That's the {letrune} {sym}!",
                f"It is the {letrune} {sym}!",
                f"It's the {letrune} {sym}!",
                f"A perfect {letrune} {sym}!",
                f"A perfect {sym}!",
                f"You made the {letrune} {sym}!",
                f"You made a {sym}!",
                f"The {letrune} {sym}!",
            )
            if sym in 'HELP':
                message += "\n" + cls(
                    f"That should get some attention!",
                    f"Display it!",
                    f"It will be helpful!",
                )
            else:
                message += "\n" + cls(
                    *usefuls,
                    "That's not too interesting.",
                    "It doesn't look useful.",
                )
            return message
        if sym in string.ascii_lowercase:
            sym = sym.upper()
            letrune = choice(('letter', 'rune'))
            message = cls(
                f"That resembles the {letrune} {sym}.",
                f"Looks a bit like the {letrune} {sym}.",
                f"Someone could read it as the {letrune} {sym}...",
                f"It's a bit like the {letrune} {sym}!",
                f"It's similar to a {sym}!",
            )
            if sym in 'HELP':
                message += "\n" + cls(
                    f"That could get some attention.",
                    f"Try to display it.",
                    f"It might be helpful!",
                )
            else:
                message += "\n" + cls(
                    *usefuls,
                    f"Frankly, a waste of metal.",
                )
            return message
        else:
            message = cls(
                f"That resembles the symbol {sym}...",
                f"It's… the symbol “{sym}”!",
                f"Someone could read it as “{sym}”",
                f"It's a bit like a “{sym}”.",
                f"It's similar to a “{sym}”.",
            )
            message += "\n" + cls(
                *usefuls,
                "Frankly, a waste of metal.",
            )
            return message
    elif sym == 'hook':
        return cls(
            f"A hook!\nMight make the fishing easier.",
            f"It's a fish hook!",
            f"A hook!\nYou'll use it next time you fish.",
            f"A metal fish hook!\nProbably not more effective than your regular ones.",
        )
    else:
        return cls(
            f"It's a {sym}.",
            f"A {sym}!",
            f"It resembles a {sym}.",
            f"You made a metal {sym}!",
            f"Looks like a {sym}.",
        ) + "\n" + cls(*usefuls)
