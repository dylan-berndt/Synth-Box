import pygame
from MathBasic import *
from pygame.gfxdraw import bezier

ppu = 64

camera_position = Vector2(0, 0)

surface = pygame.Surface((1200, 600), pygame.SRCALPHA)
bg = pygame.Surface((300, 150))

cb = pygame.Surface((300, 150), pygame.SRCALPHA)

pygame.font.init()
font = pygame.font.Font("Resources/04B03.ttf", 24)
item_sprite = pygame.image.load("Resources/element.png")


class Sprite(pygame.Surface):
    all_sprites = []

    def __init__(self, path):
        data = pygame.image.load(path).convert_alpha()
        super().__init__(data.get_size(), pygame.SRCALPHA)
        self.size = Vector2(data.get_size()[0], data.get_size()[1])
        self.blit(data, (0, 0))
        self.position = Vector2(0, 0)

        Sprite.all_sprites.append(self)


def world_to_camera(position):
    return (position - camera_position) * ppu + Vector2(600, 300) * 1


def world_to_screen(position):
    return position * ppu + Vector2(600, 300) * 1


def camera_to_world(position):
    return (position - Vector2(600, 300)) / ppu + camera_position * 1


def draw_list(items):
    list_size = sum(element.height for element in items)
    list_surface = pygame.Surface((36 * 4, list_size * 12 * 4))
    j = 0
    for e, element in enumerate(items):
        for i, item in enumerate(element.items):
            list_surface.blit(item_sprite, (0, j * 12 * 4))
            render = font.render(item.text, False, [255, 255, 255])
            list_surface.blit(render, (6, j * 12 * 4 + 12))
            j += 1
    return list_surface


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


def draw_cables(cables):
    cb.fill([0, 0, 0, 0])
    for cable in cables:
        dark = [num * 0.6 for num in cable.color]
        points = [world_to_camera(point) / 4 for point in [cable.left_point, cable.midpoint, cable.right_point]]
        under = [point + Vector2(0, 1) for point in points]
        bezier(cb, under, 10, dark)
        bezier(cb, points, 10, cable.color)

    cable_draw = pygame.transform.scale(cb, (1200, 600))
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


def draw(window, objects, cables, focus, debug, menu, menu_list):
    cam = world_to_screen(camera_position)
    draw_bg(cam.x / 4 % (ppu / 2))

    background = pygame.transform.scale(bg, (1200, 600))
    surface.blit(background, (0, 0))

    for obj in objects:
        obj.sprite.position = obj.position

    for sprite in Sprite.all_sprites:
        pos = world_to_camera(sprite.position)
        pos -= sprite.size / 2
        surface.blit(sprite, (pos.x, pos.y))

    if focus and not menu:
        ui_surface = draw_list(focus.ui)
        pos = world_to_camera(focus.position + focus.offset * 2)
        pos -= Vector2(ui_surface.get_width() / 2, ui_surface.get_height() + focus.sprite.get_height() / 2 + 16)
        surface.blit(ui_surface, (pos.x, pos.y))

    if menu:
        menu_surface = draw_list(menu_list)
        surface.blit(menu_surface, (1200 - 36 * 4, 48))

    for obj in objects:
        if debug:
            obj.sprite.position = obj.position
            tl = world_to_camera(obj.position + obj.offset - obj.size / 2)
            pygame.draw.rect(surface, [0, 255, 0], [tl.x, tl.y, obj.size.x * ppu, obj.size.y * ppu], 1)

    cable_layer = draw_cables(cables)
    surface.blit(cable_layer, (0, 0))

    pygame.draw.rect(surface, [0, 0, 0], [0, 0, 1200, 48])
    synth_stomp = font.render("Synth Stomp", False, (255, 255, 255))
    surface.blit(synth_stomp, (16, 12))
    plus = font.render("[ + ]", False, (255, 255, 255))
    surface.blit(plus, (1200 - 68, 12))

    window.blit(surface, (0, 0))

    pygame.display.update()
