import pygame
from MathBasic import *

ppu = 64

camera_position = Vector2(0, 0)


class Sprite(pygame.Surface):
    all_sprites = []

    def __init__(self, path):
        data = pygame.image.load(path).convert_alpha()
        super().__init__(data.get_size(), pygame.SRCALPHA)
        self.size = Vector2(data.get_size()[0], data.get_size()[1])
        self.blit(data, (0, 0))
        self.position = Vector2(0, 0)

        Sprite.all_sprites.append(self)


def world_to_screen(position):
    return (position - camera_position) * ppu + Vector2(600, 300) * 1


def screen_to_world(position):
    return (position - Vector2(600, 300)) / ppu + camera_position * 1


def draw(window, objects):
    for sprite in Sprite.all_sprites:
        pos = world_to_screen(sprite.position)
        pos -= sprite.size / 2
        window.blit(sprite, (pos.x, pos.y))

    for obj in objects:
        obj.sprite.position = obj.position
        tl = world_to_screen(obj.position - obj.size / 2)
        pygame.draw.rect(window, [0, 255, 0], [tl.x, tl.y, obj.size.x * ppu, obj.size.y * ppu], 1)
