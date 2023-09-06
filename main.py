import pygame

import screen
from game import *
import ctypes
import pynput
import sys

holding = None
focus = None
typing = None
cabling = None

debug = False
menu = False

dragging = False
mouse = pynput.mouse.Controller()


def on_click(x, y, button, pressed):
    global dragging
    if button == pynput.mouse.Button.left:
        if not pressed:
            dragging = False


listener = pynput.mouse.Listener(on_click=on_click)
listener.start()

x, y = mouse.position
mpo = Vector2(x, y)
window_position = Vector2(100, 100)

window = pygame.display.set_mode((1200, 600), pygame.NOFRAME)
pygame.display.set_caption("Synth Box")
pygame.display.set_icon(pygame.image.load("Resources/logo.png"))

mid = Sprite("Resources/back.png")
lft = Sprite("Resources/back.png")
rgt = Sprite("Resources/back.png")

trash = Sprite("Resources/trash.png")
trash_pos = Vector2(-8.75, -3.25)

lft.position = Vector2(-6, 0)
rgt.position = Vector2(6, 0)

clock = pygame.time.Clock()

hwnd = pygame.display.get_wm_info()["window"]


def set_window_position(x, y):
    ctypes.windll.user32.MoveWindow(hwnd, x, y, 1200, 600, True)


def minimize():
    ctypes.windll.user32.ShowWindow(hwnd, 6)


set_window_position(window_position.x, window_position.y)


while True:
    clock.tick(120)
    fps = clock.get_fps()

    mx, my = pygame.mouse.get_pos()
    mp = camera_to_world(Vector2(mx, my))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_c:
                    debug = not debug
                if event.key == pygame.K_s:
                    save_state()
                if event.key == pygame.K_o:
                    open_state()

            if event.key == pygame.K_SPACE:
                pass

            if typing:
                if event.unicode.isalnum() or event.unicode in [".", "-", "#"]:
                    data = typing.items[1].text + event.unicode
                    typing.value = data
                    update_process()

            if event.key == pygame.K_BACKSPACE:
                if typing:
                    data = typing.items[1].text[:-1]
                    typing.value = data
                    update_process()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                for device in Object.all_objects:
                    if point_in_object(mp, device):
                        cabling = device

            if event.button == 1:
                if menu:
                    check_menu_ui(mx, my, menu)

                if my < 48:
                    if mx > 1120:
                        if mx > 1160:
                            pygame.quit()
                            sys.exit()
                        else:
                            minimize()
                    elif mx > 1050 - 100:
                        menu = utility_list
                    elif mx > 921 - 100:
                        menu = mixer_list
                    elif mx > 781 - 100:
                        menu = effects_list
                    elif mx > 586 - 100:
                        menu = generator_list
                    else:
                        dragging = True
                        x, y = mouse.position
                        mpo = Vector2(x, y)
                else:
                    menu = None

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
                    pos = holding.position - screen.camera_position - trash_pos + holding.offset
                    if pos.magnitude() < 0.5:
                        Device.remove(holding)
                        holding = None
                        update_process()
                    else:
                        focus = holding
                        holding = None

    if fps != 0:
        for device in Object.all_objects:
            device.anim_time += 1 / fps
        sim_physics(Object.all_objects, 1 / fps)

        for cable in Cable.all_cables:
            cable.update(1 / fps)

        s = mp - screen.camera_position
        if abs(s.x) > 7 and s.y > -1 and not menu:
            if mx != 0 and mx != 1199:
                speed = (s.x / abs(s.x)) * (abs(s.x) - 7)
                screen.camera_position += Vector2(speed * 1 / fps, 0) * 2.3 * 1.5

                for device in Object.all_objects:
                    device.position -= Vector2(speed * 1 / fps, 0) * 1.4 * 1.5

    diff = screen.camera_position.x - mid.position.x
    if abs(diff) > 6:
        shift = diff / abs(diff)
        shift = Vector2(6 * shift, 0)
        lft.position += shift
        mid.position += shift
        rgt.position += shift

    trash.position = trash_pos + screen.camera_position

    if dragging:
        x, y = mouse.position
        diff = Vector2(x, y) - mpo
        window_position += diff
        set_window_position(int(window_position.x), int(window_position.y))
        mpo = Vector2(x, y)

    if holding:
        holding.velocity = (mp - holding.position - holding.offset) * 10

    draw(window, Object.all_objects, Cable.all_cables, focus, debug, menu, cabling=cabling)
