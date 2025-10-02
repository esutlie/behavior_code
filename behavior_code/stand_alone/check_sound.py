import pygame
import time


def check_sound():
    print('playing tone')
    pygame.mixer.init()
    tone = pygame.mixer.Sound('end_tone.wav')
    tone.set_volume(.5)
    pygame.mixer.Sound.play(tone, fade_ms=500)
    time.sleep(5)
    print('played tone')


if __name__ == '__main__':
    check_sound()
