import pygame

from physics import *
from sound import *
from screen import *
import screen

import pyaudio

holding = None
focus = None

pygame.display.set_icon(pygame.image.load("Resources/logo.png"))
window = pygame.display.set_mode((1200, 600))
pygame.display.set_caption("Synth Stomp")

mid = Sprite("Resources/back.png")
lft = Sprite("Resources/back.png")
rgt = Sprite("Resources/back.png")

lft.position = Vector2(-6, 0)
rgt.position = Vector2(6, 0)

# speaker = Speaker(Vector2(0, 0))
# oscillator = Oscillator(Vector2(1, -4))
# speaker.inputs = [oscillator]
#
# audio = pyaudio.PyAudio()
# stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)
# stream.write(speaker.process().astype(np.float32).tobytes())
# stream.stop_stream()
# stream.close()

clock = pygame.time.Clock()

while True:
    clock.tick(120)
    fps = clock.get_fps()

    mx, my = pygame.mouse.get_pos()
    mp = screen_to_world(Vector2(mx, my))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                if event.mod & pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT:
                    pass

            if event.key == pygame.K_SPACE:
                pass

        if event.type == pygame.MOUSEBUTTONDOWN:
            focus = None
            if event.button == 1:
                for device in Object.all_objects:
                    if point_in_object(mp, device):
                        holding = device

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if holding:
                    focus = holding
                    holding = None

    if fps != 0:
        sim_physics(Object.all_objects, 1 / fps)

        s = mp - screen.camera_position
        if abs(s.x) > 6:
            speed = (s.x / abs(s.x)) * (abs(s.x) - 6)
            screen.camera_position += Vector2(speed * 1 / fps, 0) * 4

    diff = screen.camera_position.x - mid.position.x
    if abs(diff) > 6:
        shift = diff / abs(diff)
        shift = Vector2(6 * shift, 0)
        lft.position += shift
        mid.position += shift
        rgt.position += shift

    if holding:
        holding.velocity = (mp - holding.position) * 5

    draw(window, Object.all_objects)

    pygame.display.update()
