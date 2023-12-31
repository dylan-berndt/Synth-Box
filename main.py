import objects
from game import *
import pynput
import sys

holding = None
holding_time = 0

focus = None
typing = None
cabling = None

debug = False
menu = False

dragging = False
mouse = pynput.mouse.Controller()

modify = False

minimap = False


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


set_window_position(window_position.x, window_position.y)

set_process()


while True:
    clock.tick(120)
    fps = clock.get_fps()

    mx, my = pygame.mouse.get_pos()
    mp = camera_to_world(Vector2(mx, my))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            close()

        if event.type == pygame.KEYDOWN:
            if event.mod & pygame.KMOD_CTRL:
                if event.key == pygame.K_c:
                    Device.clear_all()
                if event.key == pygame.K_s:
                    save_state()
                if event.key == pygame.K_o:
                    open_state()
                if event.key == pygame.K_d:
                    debug = not debug
                if event.key == pygame.K_m:
                    minimap = not minimap

            if event.key == pygame.K_SPACE:
                pass

            if typing:
                if event.unicode.isalnum() or event.unicode in [".", "-", "#"]:
                    modify = True
                    data = typing.items[1].text + event.unicode
                    typing.value = data

                if event.key == pygame.K_BACKSPACE:
                    modify = True
                    data = typing.items[1].text[:-1]
                    typing.value = data

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                if objects.beatbox_edit:
                    beatbox_num(objects.beatbox_edit, mx, my, False)
                    if my > 320:
                        continue
                if objects.sequence_edit:
                    sequence_num(objects.sequence_edit, mx, my, False)
                    if my > 360:
                        continue
                for device in Object.all_objects:
                    if point_in_object(mp, device):
                        cabling = device

            if event.button == 1:
                tab_check(mx, my)

                if my < 480:
                    if my < 320:
                        objects.beatbox_edit = None
                    objects.sequence_edit = None
                if objects.beatbox_edit:
                    beatbox_num(objects.beatbox_edit, mx, my, True)
                    continue
                elif objects.sequence_edit:
                    sequence_num(objects.sequence_edit, mx, my, True)
                    continue

                if menu:
                    check_menu_ui(mx, my, menu)

                if my < 48:
                    if 1120 > mx > 1050 - 100:
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
                    if modify:
                        modify = False
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
                        holding_time = 0
                    else:
                        focus = holding
                        holding = None
                        holding_time = 0

    if fps != 0 and fps > 5:
        screen.lag_flag = objects.process_lag_flag > 0
        objects.process_lag_flag = max(0, objects.process_lag_flag - 1 / fps)

        for device in Object.all_objects:
            device.anim_time += 1 / fps
        bumps = sim_physics(Object.all_objects, 1 / fps)
        play_bumps(bumps)

        for cable in Cable.all_cables:
            cable.update(1 / fps)

        s = mp - screen.camera_position
        if abs(s.x) > 7 and s.y > -2 and not menu and not objects.beatbox_edit:
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
        holding_time += 0 if fps == 0 else 1 / fps
    if holding_time > 0.1:
        holding.velocity = (mp - holding.position - holding.offset) * 10

    draw(window, focus, debug, menu, minimap, cabling=cabling)
