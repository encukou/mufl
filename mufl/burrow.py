from random import shuffle
from math import tau

from wasabi2d import clock, animate, keys

from .common import add_key_icon, change_sprite_image, KEY_NUMBERS, add_space_instruction

CARD_COLOR = 0, 0, 0.02
FACE_COLOR = {
    'card_foot': (0.73, 0.0, 1.0),
    'card_left': (0.0, 1.0, 0.85),
    'card_right': (0.0, 0.8, 1.0),
}

ANGLES = {
    (1, 0): 0,
    (0, 1): tau/4,
    (-1, 0): tau/2,
    (0, -1): tau*3/4,
}

def deck_pos(i):
    return 280 + 80*i, 128-24


def tile_pos(x, y):
    return 304 + x * 62, 315 + y * 62


class Burrowing:
    def __init__(self, game):
        self.game = game

        self.bg_layer = game.scene.layers[0]
        self.deck_layer = self.tile_layer = game.scene.layers[1]
        self.card_layer1 = self.worm_layer = game.scene.layers[2]
        self.card_layer2 = self.hypno_layer = self.key_layer1 = game.scene.layers[3]
        self.card_layer3 = self.key_layer2 = game.scene.layers[4]

        self.deck_sprites = []

        for i in range(4):
            paper = self.deck_layer.add_sprite('card', color=CARD_COLOR, pos=deck_pos(i))
            ink = self.card_layer1.add_sprite('card_back', pos=deck_pos(i))
            k = add_key_icon(self.key_layer1, self.key_layer2, 280 + 80*i + 4, 24, str(i+1))
            self.deck_sprites.append((paper, ink, *k))

        self.space_sprites = add_space_instruction(self.deck_layer, 'Go')

        self.selecting = False
        self.selected = []
        self.turnover_cancels = {}

        self.tile_sprites = {}
        for x in range(4):
            for y in range(5):
                self.tile_sprites[x, y] = self.tile_layer.add_sprite('block_10000', pos=tile_pos(x, y))

        cards = ['card_foot'] * 22 + ['card_left'] * 20 + ['card_right'] * 20
        shuffle(cards)
        q = len(cards) // 4
        self.decks = cards[0:q], cards[q:2*q], cards[2*q:3*q], cards[3*q:4*q]
        self.decks[0].append('card_foot')
        self.decks[1].append('card_left')
        self.decks[2].append('card_right')
        self.decks[3].append('card_foot')

        self.arrow_sprite = self.hypno_layer.add_sprite('arrow_guide', color=(1, 1, 1, 0), pos=tile_pos(0, -1), angle=tau/4)

        async def init_anim():
            await clock.coro.sleep(0.5)
            for i in range(len(self.decks)):
                self.turn_over(i, i/10)
            await clock.coro.sleep(0.5)
            await self.add_card(0)
            self.selecting = True
            clock.coro.run(self.anim_arrow())

        self.paper_sprites = {}
        self.ink_sprites = {}

        clock.coro.run(init_anim())

        pg = self.hypno_layer.add_particle_group(
            'hypno', grow=0.9, max_age=1, spin_drag=1.1,
        )
        pg.add_color_stop(0, (1, 1, 1, 0))
        pg.add_color_stop(.4, (1, 1, 1, 1))
        pg.add_color_stop(.6, (1, 1, 1, .8))
        pg.add_color_stop(1, (.8, .8, 1, 0))
        self.hypno_emitters = []
        for x in range(4):
            for y in range(5):
                em = pg.add_emitter(
                    rate=1, pos=tile_pos(x, y), pos_spread=(16, 16),
                    vel_spread=(8, 8), size=16, spin_spread=tau,
                )
                self.hypno_emitters.append(em)

        x, y = tile_pos(0, -1)
        self.worm_sprites = [
            self.worm_layer.add_sprite('worm_segment', pos=(x-i*16*0.95**i, y+32*(1-0.9**i)), scale=0.9**i)
            for i in reversed(range(10))
        ]


    async def anim_arrow(self):
        while self.selecting:
            await animate(self.arrow_sprite, color=(1, 1, 1, 0.6), duration=0.2)
            await clock.coro.sleep(0.5)
            await animate(self.arrow_sprite, color=(1, 1, 1, 0), duration=0.2)
            await clock.coro.sleep(0.2)


    def turn_over(self, i, delay=0):
        try:
            card = self.decks[i][-1]
        except IndexError:
            for s in self.deck_sprites[i]:
                s.color = 0, 0, 0, 0
            return
        x, y = pos = deck_pos(i)
        paper = self.card_layer2.add_sprite('card', color=(0, 0, 0, 0), pos=pos)
        ink = self.card_layer3.add_sprite('card_back', color=(0, 0, 0, 0), pos=pos)
        self.paper_sprites[i] = paper
        self.ink_sprites[i] = ink

        def maybe_hide_deck():
            if len(self.decks[i]) <= 1:
                for s in self.deck_sprites[i][:2]:
                    s.color = 0, 0, 0, 0
            if len(self.decks[i]) < 1:
                for s in self.deck_sprites[i]:
                    s.color = 0, 0, 0, 0

        cancelled = False
        def cancel():
            nonlocal cancelled
            cancelled = True
            paper.scale_x = ink.scale_x = 1
            paper.y = ink.y = y
            paper.color = CARD_COLOR
            ink.color = (*FACE_COLOR[card], 1)
            change_sprite_image(ink, card)
            maybe_hide_deck()
        async def _turn_over():
            try:
                if delay:
                    await clock.coro.sleep(delay)
                paper.color = CARD_COLOR
                ink.color = (1, 1, 1, 1)
                duration = 0.5
                maybe_hide_deck()
                async for t in clock.coro.frames(seconds=duration):
                    if cancelled:
                        break
                    t /= duration
                    paper.scale_x = ink.scale_x = abs(1 - 2*t)
                    paper.y = ink.y = y + 32 * t * (t-1)
                    if t > 0.5:
                        change_sprite_image(ink, card)
                        ink.color = FACE_COLOR[card]
            finally:
                cancel()
        clock.coro.run(_turn_over())
        self.turnover_cancels[i] = cancel

    async def add_card(self, i):
        try:
            card = self.decks[i].pop()
        except IndexError:
            return
        self.selected.append(card)
        pos = deck_pos(i)
        if not (paper := self.paper_sprites.pop(i, None)):
            paper = self.card_layer2.add_sprite('card', color=CARD_COLOR, pos=pos)
        if not (ink := self.ink_sprites.pop(i, None)):
            print('Missing ink!')
            ink = self.card_layer3.add_sprite(card, color=FACE_COLOR[card], pos=pos)
        self.turn_over(i, delay=0.5)

        self.deck_sprites.append((paper, ink))

        pos = self.get_selected_pos(len(self.selected)-1)
        for s in paper, ink:
            an = animate(s, pos=pos, scale=0.4, duration=0.5, tween='accel_decel')
        await clock.coro.sleep(0.4)
        for spr, sc in (paper, 0.38), (ink, 0.4):
            an = animate(spr, pos=pos, scale=sc, duration=0.1, tween='accel_decel')

        x, y, d = self.get_end_pos()
        self.arrow_sprite.pos = tile_pos(x, y)
        try:
            self.arrow_sprite.angle = ANGLES[d]
            change_sprite_image(self.arrow_sprite, 'arrow_guide')
        except KeyError:
            change_sprite_image(self.arrow_sprite, 'nada_guide')
            ink.color = (1, 1, 1, 0.5)

    def get_selected_pos(self, i):
        return 32 + 20 + 24 * ((i%32)-1), 160 + 38 * (i//32)

    def on_key_down(self, key):
        if self.selecting:
            if key == keys.ESCAPE:
                self.game.abort_activity()
            num = KEY_NUMBERS.get(key)
            if num and 1 <= num <= len(self.decks):
                i = num - 1
                if cancel := self.turnover_cancels.pop(i, None):
                    cancel()
                clock.coro.run(self.add_card(i))
            if key == keys.SPACE:
                self.selecting = False

    def get_end_pos(self):
        pos = [0, -1]
        d = (0, 1)
        for card in self.selected:
            if card == 'card_foot':
                pos[0] += d[0]
                pos[1] += d[1]
            elif card == 'card_left':
                dx, dy = d
                d = dy, -dx
            elif card == 'card_right':
                dx, dy = d
                d = -dy, dx
            if not ((0 <= pos[0] < 4) and (0 <= pos[1] < 5)):
                d = None
                break
        return (*pos, d)
