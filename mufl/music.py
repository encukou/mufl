from wasabi2d import music, clock, sounds
import pygame


tracks = {
    'intro': 'fun_with_doctor_strangevolt',
    'main': 'the_triumph_of_the_clock_maker',
    'fish': 'mysterious_puzzle',
    'dice': 'whimsical_popsicle',
    'burrow': 'mind_bender',
    'shadow': 'hypnotic_jewels',
    'win': 'endless_sci_fi_runner',
}

soundnames = {
    'menu-move': 'ui_quirky19',# 'lamp_switch_off', #clank_1',
    'menu-select': 'ui_quirky7', #'lamp_switch_on', #clank_2',

    'missile-launch': 'explosion7',
    'missile-launch2': 'powerup28',
    'missile-boom': 'explosion4',
    'missile-boom2': 'powerup25',

    'wave': 'splash',
    'bite': 'random6',
    'fish-got-away': 'powerdown16',

    #'die-hit': 'lamp_switch_on',
    'die-select': 'robot_footstep_3',
    'die-roll': 'ui_quirky27', #'lamp_switch_on',

    'hypno-start': 'bells8', #'powerup17',
    'set-card': 'swish-1', #'powerup17',
    'cast': 'explosion5', #'powerup17',

    'set-item': 'swish-1', #'powerup17',

    'resource-get': 'dingcling_neutral',
}


current_music = None

def set_music(tracktype):
    global current_music
    newmusic = tracks.get(tracktype, 'the_triumph_of_the_clock_maker')
    if current_music != newmusic:
        current_music = newmusic
        music.fadeout(0.5)
        clock.schedule(lambda: music.play(newmusic), 0.5, strong=True)


def play_sound(name, volume=1):
    name = soundnames.get(name)
    if name:
        try:
            snd = getattr(sounds, name)
        except AttributeError:
            pass
        else:
            snd.set_volume(volume)
            snd.play()

