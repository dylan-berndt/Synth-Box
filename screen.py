import pygame
from MathBasic import *
from pygame.gfxdraw import bezier
import os

ppu = 64
anim_fps = 24

camera_position = Vector2(0, 0)

surface = pygame.Surface((1200, 600), pygame.SRCALPHA)
converted = False
bg = pygame.Surface((300, 150))

cb = pygame.Surface((300, 150), pygame.SRCALPHA)

bb = pygame.Surface((300, 150), pygame.SRCALPHA)

pygame.font.init()
font = pygame.font.Font("Resources/04B03.ttf", 24)
item_sprite = pygame.image.load("Resources/element.png")
expand = pygame.image.load("Resources/expand.png")

shadow = pygame.image.load("Resources/shadow.png")

controls = pygame.image.load("Resources/controls.png")

logo = pygame.image.load("Resources/logo.png")

beatbox_ui = pygame.image.load("Resources/beatbox_ui.png")
sequencer_ui = pygame.image.load("Resources/sequencer_ui.png")

paths = os.listdir("Resources/Waves/")
triangle_wave = [pygame.image.load(os.path.join("Resources/Waves/", path)) for path in paths if path[0:2] == "tr"]
square_wave = [pygame.image.load(os.path.join("Resources/Waves/", path)) for path in paths if path[0:2] == "sq"]
sine_wave = [pygame.image.load(os.path.join("Resources/Waves/", path)) for path in paths if path[0:2] == "si"]
tape_roll = [pygame.image.load(os.path.join("Resources/Waves/", path)) for path in paths if path[0:2] == "ta"]

wave_dict = {"Sine": sine_wave, "Square": square_wave, "Triangle": triangle_wave, "Sample": tape_roll}

switch_path = os.listdir("Resources/Switch/")
switches = [pygame.image.load(os.path.join("Resources/Switch/", path)) for path in switch_path if path[0] != "f"]
f_switches = [pygame.image.load(os.path.join("Resources/Switch/", path)) for path in switch_path if path[0] == "f"]


class Sprite(pygame.sprite.Sprite):
    all_sprites = []
    group = pygame.sprite.Group()

    def __init__(self, path):
        super().__init__()

        self.image = pygame.image.load(path).convert_alpha()
        self.size = Vector2(self.image.get_size()[0], self.image.get_size()[1])
        self.position = Vector2(0, 0)
        self.rect = self.image.get_rect()

        Sprite.all_sprites.append(self)
        Sprite.group.add(self)

    def remove(self):
        Sprite.all_sprites.remove(self)
        Sprite.group.remove(self)
        del self

    def update(self):
        pos = world_to_camera(self.position)
        self.rect.x = pos.x - self.size.x / 2
        self.rect.y = pos.y - self.size.y / 2

    def get_width(self):
        return self.rect.width

    def get_height(self):
        return self.rect.height


def world_to_camera(position):
    return (position - camera_position) * ppu + Vector2(600, 300) * 1


def world_to_screen(position):
    return position * ppu + Vector2(600, 300) * 1


def camera_to_world(position):
    return (position - Vector2(600, 300)) / ppu + camera_position * 1


def draw_list(items):
    list_size = sum(element.height for element in items)
    exp = True in [type(element).__name__ == "Expand" for element in items]
    list_surface = pygame.Surface((36 * 4 * (1 + exp), list_size * 12 * 4))
    j = 0
    for e, element in enumerate(items):
        for i, item in enumerate(element.items):
            list_surface.blit(item_sprite, (0, j * 12 * 4))
            render = font.render(item.text, False, [255, 255, 255])
            list_surface.blit(render, (6, j * 12 * 4 + 12))
            if type(element).__name__ == "Expand":
                list_surface.blit(expand, (0, j * 12 * 4))
            j += 1
    return list_surface


def draw_bb(beatbox):
    global bb

    bb = pygame.Surface((300, 150), pygame.SRCALPHA)
    if beatbox is not None:
        b = hasattr(beatbox, "notation")

        bb.blit(beatbox_ui if b else sequencer_ui, (0, 0))
        j = 0
        row_size = 8 if not b else len(beatbox.notation[0])
        rows = 4 if b else 1
        width = int(300 / row_size)
        height = 12

        def draw_note(value, j):
            color = (255, 255, 255) if value > 0 else (46, 34, 47)
            w, h = width * (j % row_size) + 3, height * int(j / row_size) + 101 + (12 * (4 - rows))
            pygame.draw.rect(bb, color, (w, h, width - 2, height - 2), width=1)

        for row in (beatbox.sequence if not b else beatbox.notation):
            if not b:
                draw_note(row > 0, j)
                j += 1
            else:
                for note in row:
                    draw_note(note > 0, j)
                    j += 1
        box = pygame.transform.scale(bb, (1200, 600))
        return box
    else:
        return pygame.Surface((1200, 600), pygame.SRCALPHA)


def draw_bg(shift):
    tiles = math.ceil(300 / 16) + 4
    height = 6
    y_start = 7 * 16
    x_start = 300 - ((tiles - 2) * 16) - shift - 6
    length = [i * 7 for i in range(height + 1)]

    def stretch(x0, y0):
        return x0 + ((y0 / height) * (x0 - 150) * 1.5)

    for x in range(tiles):
        for y in range(height):
            r = int((tiles - x) * 5 * y / height) + 20
            color = [217, 240, 255] if (x + y) % 2 == 0 else [r, r, r]
            y1, y2 = y_start + length[y], y_start + length[y + 1]
            x1, x2 = x_start + (x * 16), x_start + ((x + 1) * 16)
            x3, x4 = x1, x2
            x1, x2, x3, x4 = stretch(x1, y), stretch(x2, y), stretch(x3, y + 1), stretch(x4, y + 1)
            points = [[x1, y1], [x2, y1], [x4, y2], [x3, y2]]
            pygame.draw.polygon(bg, color, points)


def draw_cables(cables, cabling):
    mx, my = pygame.mouse.get_pos()

    cb.fill([0, 0, 0, 0])
    for cable in cables:
        dark = [num * 0.6 for num in cable.color]
        points = [world_to_camera(point) / 4 for point in
                  [cable.left_point, cable.midpoint, cable.right_point]]
        under = [point + Vector2(0, 1) * 1 for point in points]
        bezier(cb, under, 10, dark)
        bezier(cb, points, 10, cable.color)

    if cabling is not None and cabling.total_outputs > 0:
        pos = cabling.position + Vector2(7/16 * cabling.size.x / 1.6, 9/16)
        pos += Vector2(0, -6/16) * (len(cabling.outputs) - 1 * (len(cabling.outputs) >= cabling.total_outputs))
        left = world_to_camera(pos) / 4
        pygame.draw.line(cb, (255, 255, 255), [left.x, left.y], [mx / 4, my / 4], 2)

    cable_draw = pygame.transform.scale(cb, (1200, 600))

    if cabling is not None and cabling.total_outputs > 0:
        pos = left * 4
        pygame.draw.rect(cable_draw, [255, 255, 255], [pos.x - 4, pos.y - 4, 8, 8])

    for cable in cables:
        dark = [num * 0.6 for num in cable.color]
        points = [world_to_camera(point) for point in [cable.left_point, cable.right_point]]
        pygame.draw.rect(cable_draw, dark, [points[0].x - 8, points[0].y - 4, 16, 8])
        pygame.draw.rect(cable_draw, dark, [points[0].x - 4, points[0].y - 8, 8, 16])
        pygame.draw.rect(cable_draw, dark, [points[1].x - 8, points[1].y - 4, 16, 8])
        pygame.draw.rect(cable_draw, dark, [points[1].x - 4, points[1].y - 8, 8, 16])
        pygame.draw.rect(cable_draw, cable.color, [points[0].x - 4, points[0].y - 4, 8, 8])
        pygame.draw.rect(cable_draw, cable.color, [points[1].x - 4, points[1].y - 4, 8, 8])

    return cable_draw


def draw(window, objects, cables, focus, debug, menu, seq=None, beat=None, cabling=None):
    mx, my = pygame.mouse.get_pos()

    global converted
    if not converted:
        surface.convert()
        converted = True

    cam = world_to_screen(camera_position)
    draw_bg(cam.x / 4 % (ppu / 2))

    background = pygame.transform.scale(bg, (1200, 600))
    surface.blit(background, (0, 0))

    for obj in objects:
        obj.sprite.position = obj.position
        y = ((4 * (10 + obj.position.y)) / 11.5) - 1.5
        x = obj.position.x + 0.5 * (3 - y)
        pos = Vector2(x, y)
        pos = world_to_camera(pos)
        size = shadow.get_size()
        pos -= Vector2(size[0], size[1]) / 2
        surface.blit(shadow, (pos.x, pos.y))

    Sprite.group.update()
    Sprite.group.draw(surface)

    for device in objects:
        pos = world_to_camera(device.position)
        if device.switch is not None:
            if device.total_outputs > 0:
                switch_dir = switches[not device.switch]
            else:
                switch_dir = f_switches[not device.switch]
            size = switch_dir.get_size()
            s_pos = pos - Vector2(size[0], size[1]) / 2
            surface.blit(switch_dir, (s_pos.x, s_pos.y))
        if not device.switch:
            continue
        if type(device).__name__ in wave_dict:
            wave = wave_dict[type(device).__name__]
            sprite_num = int((device.anim_time * anim_fps) % len(wave))
            size = wave[sprite_num].get_size()
            pos -= Vector2(size[0], size[1]) / 2
            surface.blit(wave[sprite_num], (pos.x, pos.y))

    cable_layer = draw_cables(cables, cabling)
    surface.blit(cable_layer, (0, 0))

    if focus and not menu:
        ui_surface = draw_list(focus.ui)
        pos = world_to_camera(focus.position + focus.offset * 2)
        pos -= Vector2(ui_surface.get_width() / 2, ui_surface.get_height() + focus.sprite.get_height() / 2 + 16)
        surface.blit(ui_surface, (pos.x, pos.y))

    if menu:
        menu_surface = draw_list(menu)
        surface.blit(menu_surface, (1200 - 36 * 4, 48))

    pygame.draw.rect(surface, [0, 0, 0], [0, 0, 1200, 48])
    synth_stomp = font.render("Synth Box", False, (255, 255, 255))
    surface.blit(synth_stomp, (48 + 16 + 30, 14))
    plus = font.render("|  Generators  |  Effects  |  Mixing  |  Utility  |", False, (255, 255, 255))
    num = plus.get_width()
    surface.blit(plus, (1200 - num - 16 - 100, 14))
    surface.blit(logo, (24, 8))

    surface.blit(controls, (1200 - 80, 0))

    beatbox = draw_bb(beat if beat else seq)
    surface.blit(beatbox, (0, 0))

    if debug:
        for obj in objects:
            tl = world_to_camera(obj.position + obj.offset - obj.size / 2)
            pygame.draw.rect(surface, [0, 255, 0], [tl.x, tl.y, obj.size.x * ppu, obj.size.y * ppu], 1)
        mouse_pos = font.render(str(mx) + ", " + str(my), False, (255, 255, 255))
        pygame.draw.rect(surface, [0, 0, 0], [1050, 552, 150, 48])
        surface.blit(mouse_pos, [1058, 560])

    window.blit(surface, (0, 0))

    pygame.display.update()
