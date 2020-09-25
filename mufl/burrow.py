from random import shuffle
from math import tau
from enum import Enum
from dataclasses import dataclass

from wasabi2d import clock, animate, keys

from .common import add_key_icon, change_sprite_image, KEY_NUMBERS, add_space_instruction


@dataclass
class Card:
    value: str
    face_up: bool = False
    current_animation: object = None
    anim_sprite: object = None
    origin_deck: int = 0
    selected_index: int = 0
    sel_sprite: object = None


def deck_pos(i):
    return 280 + 80*i, 128-24

def selected_pos(i):
    return 32 + 20 + 24 * ((i%32)-1), 160 + 38 * (i//32)


class Burrowing:
    def __init__(self, game):
        self.game = game

        self.bg_layer = game.scene.layers[0]
        self.deck_layer = self.tile_layer = game.scene.layers[1]
        self.turncard_layer = self.worm_layer = game.scene.layers[2]
        self.selcard_layer = self.hypno_layer = self.key_layer1 = game.scene.layers[3]
        self.key_layer2 = game.scene.layers[4]

        cards = [Card(c) for c in ['card_foot'] * 22 + ['card_left'] * 20 + ['card_right'] * 20]
        shuffle(cards)
        q = len(cards) // 4
        self.decks = cards[0:q], cards[q:2*q], cards[2*q:3*q], cards[3*q:4*q]
        self.decks[0].append(Card('card_foot'))
        self.decks[1].append(Card('card_left'))
        self.decks[2].append(Card('card_right'))
        self.decks[3].append(Card('card_foot'))

        self.selected = []

        self.deck_sprites = []
        self.deck_keylabels = []
        for i, deck in enumerate(self.decks):
            s = self.deck_layer.add_sprite('card_back', pos=deck_pos(i))
            k = add_key_icon(self.key_layer1, self.key_layer2, 280 + 80*i + 4, 24, str(i+1))
            self.deck_sprites.append(s)
            self.deck_keylabels.append(k)

        self.selecting = False
        async def start_anim():
            for i, deck in enumerate(self.decks):
                self.turn_deck(i)
                await clock.coro.sleep(1/3)
            self.update_deck_sprites()
            self.add_card(0)
            self.selecting = True

        clock.coro.run(start_anim())

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
            s.y = y + 32 * t * (t-1)
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
        pos = selected_pos(card.selected_index)
        anim = animate(card.anim_sprite, pos=pos, scale=0.3, duration=1, tween='accel_decel')
        try:
            await anim
        finally:
            anim.stop(complete=True)
            if card.sel_sprite:
                card.sel_sprite.color = 1, 1, 1, 1

    async def do_undo_animation(self, card):
        card.anim_sprite = s = self.turncard_layer.add_sprite(
            card.value,
            pos=selected_pos(card.selected_index),
            scale = 0.3,
        )
        pos = deck_pos(card.origin_deck)
        anim = animate(card.anim_sprite, pos=pos, scale=1, duration=0.2, tween='linear')
        try:
            await anim
        finally:
            anim.stop(complete=True)
            if card.sel_sprite:
                card.sel_sprite.color = 1, 1, 1, 1

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

