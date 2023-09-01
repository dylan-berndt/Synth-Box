import pygame
from game import *

holding = None
focus = None
typing = None
cabling = None

debug = False
menu = False

pygame.display.set_icon(pygame.image.load("Resources/logo.png"))
window = pygame.display.set_mode((1200, 600))
pygame.display.set_caption("Synth Stomp")

mid = Sprite("Resources/back.png")
lft = Sprite("Resources/back.png")
rgt = Sprite("Resources/back.png")

lft.position = Vector2(-6, 0)
rgt.position = Vector2(6, 0)

Oscillator(Vector2(0, 0))

clock = pygame.time.Clock()

while True:
    clock.tick(120)
    fps = clock.get_fps()

    mx, my = pygame.mouse.get_pos()
    mp = camera_to_world(Vector2(mx, my))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c and event.mod & pygame.KMOD_CTRL:
                debug = not debug

            if event.key == pygame.K_SPACE:
                pass

            if event.unicode.isnumeric() or event.unicode == ".":
                if typing:
                    typing.items[1].text += event.unicode
                    typing.value = float(typing.items[1].text)

            if event.key == pygame.K_BACKSPACE:
                if typing:
                    typing.items[1].text = typing.items[1].text[0:-1]
                    if len(typing.items[1].text) == 0:
                        typing.value = 0
                    else:
                        typing.value = float(typing.items[1].text)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                for device in Object.all_objects:
                    if point_in_object(mp, device):
                        cabling = device

            if event.button == 1:
                if menu:
                    check_menu_ui(mx, my, menu_list)

                menu = mx > 1100 and my < 48

                left_focus = True
                ui_click = False

                if focus:
                    left_focus, ui_click, typing = check_focus_ui(focus, mx, my)
                    if ui_click:
                        continue

                for device in Object.all_objects:
                    if point_in_object(mp, device):
                        holding = device
                        if holding == focus:
                            left_focus = False
                if left_focus:
                    focus = None

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                attempt_cable(mp, cabling)
                cabling = None

            if event.button == 1:
                if holding:
                    focus = holding
                    holding = None

    if fps != 0:
        sim_physics(Object.all_objects, 1 / fps)

        for cable in Cable.all_cables:
            cable.update(1 / fps)

        s = mp - screen.camera_position
        if abs(s.x) > 7 and s.y > -3 and not menu:
            speed = (s.x / abs(s.x)) * (abs(s.x) - 7)
            screen.camera_position += Vector2(speed * 1 / fps, 0) * 4

            for device in Object.all_objects:
                device.position -= Vector2(speed * 1 / fps, 0) * 0.4

    diff = screen.camera_position.x - mid.position.x
    if abs(diff) > 6:
        shift = diff / abs(diff)
        shift = Vector2(6 * shift, 0)
        lft.position += shift
        mid.position += shift
        rgt.position += shift

    if holding:
        holding.velocity = (mp - holding.position - holding.offset) * 10

    draw(window, Object.all_objects, Cable.all_cables, focus, debug, menu, menu_list)
