from random import shuffle
from math import tau
from enum import Enum
from dataclasses import dataclass

from wasabi2d import clock, keys

from .common import add_key_icon, change_sprite_image, KEY_NUMBERS, add_space_instruction
from .fixes import animate


@dataclass
class Card:
    value: str
    face_up: bool = False
    current_animation: object = None
    anim_sprite: object = None
    origin_deck: int = 0
    selected_index: int = 0
    sel_sprite: object = None
    active: bool = True


def deck_pos(i):
    return 280 + 80*i, 128-24

def selected_pos(i):
    return 32 + 20 + 24 * ((i%32)-1), 160 + 38 * (i//32)

def tile_pos(x, y):
    return 304 + x * 62, 315 + y * 62

ANGLES = {
    (1, 0): 0,
    (0, 1): tau/4,
    (-1, 0): tau/2,
    (0, -1): tau*3/4,
}


class Burrowing:
    def __init__(self, game):
        self.game = game

        self.bg_layer = game.scene.layers[0]
        self.tile_layer = self.key_layer1 = game.scene.layers[1]
        self.deck_layer = self.key_layer2 = self.worm_layer = game.scene.layers[2]
        self.turncard_layer = self.hypno_layer = game.scene.layers[3]
        self.selcard_layer = game.scene.layers[4]

        cards = [Card(c) for c in ['card_foot'] * 22 + ['card_left'] * 20 + ['card_right'] * 20]
        shuffle(cards)
        q = len(cards) // 4
        self.decks = cards[0:q], cards[q:2*q], cards[2*q:3*q], cards[3*q:4*q]
        self.decks[0].append(Card('card_foot'))
        self.decks[1].append(Card('card_left'))
        self.decks[2].append(Card('card_right'))
        self.decks[3].append(Card('card_foot'))

        self.selecting = False
        self.selected = []

        self.deck_sprites = []
        self.deck_keylabels = []
        for i, deck in enumerate(self.decks):
            s = self.deck_layer.add_sprite('card_back', pos=deck_pos(i))
            k = add_key_icon(self.key_layer1, self.key_layer2, 280 + 80*i + 4, 24, str(i+1))
            self.deck_sprites.append(s)
            self.deck_keylabels.append(k)

        self.arrow_sprite = self.hypno_layer.add_sprite('arrow_guide', color=(1, 1, 1, 0), pos=tile_pos(0, -1), angle=tau/4)

        self.tile_sprites = {}
        for x in range(4):
            for y in range(5):
                self.tile_sprites[x, y] = self.tile_layer.add_sprite('block_10000', pos=tile_pos(x, y))

        x, y = tile_pos(0, -1)
        self.worm_sprites = [
            self.worm_layer.add_sprite('worm_segment', pos=(x-i*16*0.95**i, y+32*(1-0.9**i)), angle=tau/4, scale=0.9**i)
            for i in reversed(range(10))
        ]

        self.space_sprites = add_space_instruction(self.deck_layer, 'Go')
        for s in self.space_sprites:
            s.color = (*s.color[:3], 0)

        async def start_anim():
            for i, deck in enumerate(self.decks):
                self.turn_deck(i)
                await clock.coro.sleep(1/5)
            self.update_deck_sprites()
            self.add_card(0)
            self.selecting = True
            for s in self.space_sprites:
                s.color = (*s.color[:3], 1)
            clock.coro.run(self.anim_arrow())

        clock.coro.run(start_anim())

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

    def update_deck_sprites(self):
        for i, deck in enumerate(self.decks):
            for s in self.deck_keylabels[i]:
                if deck:
                    s.color = (*s.color[:3], 1)
                else:
                    s.color = (*s.color[:3], 0)
            for card in reversed(deck):
                if card.current_animation:
                    continue
                if card.face_up:
                    change_sprite_image(self.deck_sprites[i], card.value)
                    self.deck_sprites[i].color = 1, 1, 1, 1
                else:
                    change_sprite_image(self.deck_sprites[i], 'card_back')
                    self.deck_sprites[i].color = 1, 1, 1, 1
                break
            else:
                self.deck_sprites[i].color = 1, 1, 1, 0

    def set_animation(self, card, animation):
        if card.current_animation:
            card.current_animation.cancel()
        if card.anim_sprite:
            card.anim_sprite.delete()
            card.anim_sprite = None
        async def wrapper():
            try:
                await animation
            finally:
                card.current_animation = None
                if card.anim_sprite:
                    card.anim_sprite.delete()
                    card.anim_sprite = None
                self.update_deck_sprites()
        card.current_animation = clock.coro.run(wrapper())

    def turn_deck(self, i):
        """Make sure top of deck is turned face up"""
        try:
            card = self.decks[i][-1]
        except IndexError:
            return
        if not card.face_up:
            card.face_up = True
            self.set_animation(card, self.do_flip_animation(card, i, True))
        self.update_deck_sprites()

    async def do_flip_animation(self, card, deck, to_face_up):
        if to_face_up:
            start_face = 'card_back'
            end_face = card.value
        else:
            start_face = card.value
            end_face = 'card_back'
        x, y = pos = deck_pos(deck)
        card.anim_sprite = s = self.turncard_layer.add_sprite(
            start_face,
            pos=pos,
        )
        duration = 0.5
        async for t in clock.coro.frames(seconds=duration):
            t /= duration
            s.scale_x = abs(1 - 2*t)
            s.y = y + 64 * t * (t-1)
            if t > 0.5:
                change_sprite_image(s, end_face)

    def add_card(self, i):
        try:
            card = self.decks[i].pop()
        except IndexError:
            return
        card.face_up = True
        clock.schedule(lambda: self.turn_deck(i), 0.2, strong=True)
        card.origin_deck = i
        card.selected_index = len(self.selected)
        self.selected.append(card)
        card.active = self.update_arrow()
        self.set_animation(card, self.do_put_animation(card))
        card.sel_sprite = self.selcard_layer.add_sprite(
            card.value,
            pos=selected_pos(card.selected_index),
            color=(1, 1, 1, 0),
            scale=0.3,
        )
        self.update_deck_sprites()

    async def do_put_animation(self, card):
        card.anim_sprite = s = self.turncard_layer.add_sprite(
            card.value,
            pos=deck_pos(card.origin_deck),
        )
        if card.active:
            end_color = 1, 1, 1, 1
        else:
            end_color = .5, .5, .5, .5
        pos = selected_pos(card.selected_index)
        anim = animate(card.anim_sprite, pos=pos, scale=0.3, color=end_color, duration=1/3, tween='accel_decel')
        try:
            await anim
        finally:
            anim.stop(complete=True)
            if card.sel_sprite:
                card.sel_sprite.color = end_color

    async def do_undo_animation(self, card):
        card.anim_sprite = s = self.turncard_layer.add_sprite(
            card.value,
            pos=selected_pos(card.selected_index),
            scale = 0.3,
        )
        pos = deck_pos(card.origin_deck)
        anim = animate(card.anim_sprite, pos=pos, scale=1, duration=0.2, tween='accel_decel')
        try:
            await anim
        finally:
            anim.stop(complete=True)

    def undo(self):
        try:
            card = self.selected.pop()
        except IndexError:
            return
        self.decks[card.origin_deck].append(card)
        if card.sel_sprite:
            card.sel_sprite.delete()
            card.sel_sprite = None
        self.set_animation(card, self.do_undo_animation(card))
        self.update_deck_sprites()
        self.update_arrow()

    def on_key_down(self, key):
        if self.selecting:
            if key == keys.ESCAPE:
                if len(self.selected) > 1:
                    self.undo()
                    return
                self.game.abort_activity()
            num = KEY_NUMBERS.get(key)
            if num and 1 <= num <= len(self.decks):
                i = num - 1
                self.add_card(i)
            if key == keys.SPACE:
                self.selecting = False
                clock.coro.run(self.burrow())

    async def anim_arrow(self):
        while self.selecting:
            await animate(self.arrow_sprite, color=(1, 1, 1, 0.6), duration=0.2)
            await clock.coro.sleep(0.5)
            await animate(self.arrow_sprite, color=(1, 1, 1, 0), duration=0.2)
            await clock.coro.sleep(0.2)

    def update_arrow(self):
        x, y, d = self.get_end_pos()
        self.arrow_sprite.pos = tile_pos(x, y)
        try:
            self.arrow_sprite.angle = ANGLES[d]
            change_sprite_image(self.arrow_sprite, 'arrow_guide')
            return True
        except KeyError:
            change_sprite_image(self.arrow_sprite, 'nada_guide')
            return False

    def get_end_pos(self):
        pos = [0, -1]
        d = (0, 1)
        for card in self.selected:
            if card.value == 'card_foot':
                pos[0] += d[0]
                pos[1] += d[1]
            elif card.value == 'card_left':
                dx, dy = d
                d = dy, -dx
            elif card.value == 'card_right':
                dx, dy = d
                d = -dy, dx
            if not ((0 <= pos[0] < 4) and (0 <= pos[1] < 5)):
                d = None
                break
        return (*pos, d)

    async def burrow(self):
        for i, sprite in enumerate(reversed(self.worm_sprites)):
            clock.coro.run(self._burrow_one(sprite, i))

    async def _burrow_one(self, sprite, slp):
        is_head = not slp
        pos = [0, -1]
        d = (0, 1)
        D = 1/2
        if slp:
            await animate(sprite, pos=tile_pos(*pos), duration=slp*D/5)
        for card in self.selected:
            if is_head and card.sel_sprite:
                animate(card.sel_sprite, scale=2, duration=D)

            if card.value == 'card_foot':
                pos[0] += d[0]
                pos[1] += d[1]
                await animate(sprite, pos=tile_pos(*pos), duration=D)
            elif card.value == 'card_left':
                dx, dy = d
                d = dy, -dx
                await animate(sprite, angle=sprite.angle-tau/4, duration=D/2)
            elif card.value == 'card_right':
                dx, dy = d
                d = -dy, dx
                await animate(sprite, angle=sprite.angle+tau/4, duration=D/2)

            if is_head and card.sel_sprite:
                animate(card.sel_sprite, scale=0, y=-100, duration=D)

        await animate(sprite, scale=0, duration=(10-slp)/20)


def sched(func, time):
    clock.schedule(func, time, strong=True)

