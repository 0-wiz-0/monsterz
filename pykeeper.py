#!/usr/bin/env python

import pygame
from pygame.locals import *
from random import randint

screen_width = 640
screen_height = 480

board_width = 8
board_height = 8

animals = [
    { 'name': 'elephant', 'color': (127, 200, 255) },
    { 'name': 'panda', 'color': (255, 255, 255) },
    { 'name': 'girafe', 'color': (255, 255, 63) },
    { 'name': 'crocodile', 'color': (63, 200, 63) },
    { 'name': 'lion', 'color': (250, 160, 63) },
    { 'name': 'baboon', 'color': (255, 63, 63) },
    { 'name': 'hippo', 'color': (200, 63, 200) },
    { 'name': 'baby', 'color': (255, 180, 180) }
]

class AnimalSprite(pygame.sprite.Sprite):
    def __init__(self, type, group=None):
        pygame.sprite.Sprite.__init__(self, group)

        tmp = pygame.Surface((sprite_size, sprite_size))
        tmp.set_colorkey(tmp.get_at((0, 0)), RLEACCEL)
        pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 2, sprite_size / 2), sprite_size * 4 / 9)
        pygame.draw.circle(tmp, type['color'], (sprite_size / 2, sprite_size / 2), sprite_size * 3 / 8)
        pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 3, sprite_size * 3 / 8), sprite_size / 8)
        pygame.draw.circle(tmp, (255, 255, 255), (sprite_size / 3, sprite_size * 3 / 8), sprite_size / 16)
        pygame.draw.circle(tmp, (20, 1, 1), (sprite_size - sprite_size / 3, sprite_size * 3 / 8), sprite_size / 8)
        pygame.draw.circle(tmp, (255, 255, 255), (sprite_size - sprite_size / 3, sprite_size * 3 / 8), sprite_size / 16)
        pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 2, sprite_size * 5 / 8), sprite_size / 16)
        self.image = tmp
        self.rect  = tmp.get_rect()
        self.moveTo = None

    def update(self):
        if self.moveTo:
            self.rect.center = self.moveTo
            self.moveTo = None

class SelectSprite(pygame.sprite.Sprite):
    def __init__(self, group=None):
        pygame.sprite.Sprite.__init__(self, group)

        tmp = pygame.Surface((sprite_size, sprite_size))
        tmp.set_colorkey(tmp.get_at((0, 0)), RLEACCEL)
        pygame.draw.rect(tmp, (255, 255, 0), (0, 0, sprite_size, sprite_size), sprite_size / 8)
        self.image = tmp
        self.rect  = tmp.get_rect()
        self.moveTo = None

    def update(self):
        if self.moveTo:
            self.rect.center = self.moveTo
            self.moveTo = None

def has_won():
    # Horizontal
    for y in range(board_height):
        for x in range(board_width - 2):
            a = board.get((x, y))
            b = board.get((x + 1, y))
            c = board.get((x + 2, y))
            if not a or not b or not c:
                continue
            if a != b or a != c:
                continue
            return True
    # Horizontal
    for x in range(board_width):
        for y in range(board_height - 2):
            a = board.get((x, y))
            b = board.get((x, y + 1))
            c = board.get((x, y + 2))
            if not a or not b or not c:
                continue
            if a != b or a != c:
                continue
            return True
    return False

def draw_sprites():
    backSprites.empty()
    # Draw board
    for (coord, animal) in board.items():
        tmp = AnimalSprite(animal, backSprites)
        (x, y) = coord
        x *= sprite_size
        y *= sprite_size
        tmp.moveTo = (x + sprite_size / 2, y + sprite_size / 2)
    # Draw selector
    if select != (-1, -1):
        tmp = SelectSprite(backSprites)
        (x, y) = select
        x *= sprite_size
        y *= sprite_size
        tmp.moveTo = (x + sprite_size / 2, y + sprite_size / 2)

# Compute sprite size
sprite_size = screen_width / board_width
tmp = screen_height / board_height
if tmp < sprite_size:
    sprite_size = tmp

# Fill board with random animals
board = {}
for y in range(board_height):
    while True:
        for x in range(board_width):
            board[(x, y)] = animals[randint(0, len(animals) - 1)]
        if not has_won():
            break

# Init values
select = (-1, -1)

# Start all the stuff
pygame.init()
window = pygame.display.set_mode((640, 480))
pygame.display.set_caption('Le meilleur jeu du monde')
background = pygame.Surface(window.get_size())
background.fill((210,200,150))

backSprites = pygame.sprite.RenderUpdates()
frontSprites = pygame.sprite.RenderUpdates()

draw_sprites()

def main():
    global select
    clock = pygame.time.Clock()
    pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
            elif event.type == MOUSEBUTTONDOWN:
                (x2, y2) = event.pos
                x2 /= sprite_size
                y2 /= sprite_size
                if x2 < 0 or x2 >= board_width or y2 < 0 or y2 >= board_height:
                    continue
                if select == (-1, -1):
                    select = (x2, y2)
                    draw_sprites()
                    continue
                (x1, y1) = select
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    select = (-1, -1)
                    draw_sprites()
                    continue
                tmp = board[(x1, y1)]
                board[(x1, y1)] = board[(x2, y2)]
                board[(x2, y2)] = tmp
                if not has_won():
                    tmp = board[(x1, y1)]
                    board[(x1, y1)] = board[(x2, y2)]
                    board[(x2, y2)] = tmp
                select = (-1, -1)
                draw_sprites()
            #elif event.type == MOUSEMOTION:
            #    (x, y) = event.pos
            #    x /= sprite_size
            #    y /= sprite_size
            #    if x < 0 or x >= board_width or y < 0 or y >= board_height:
            #        continue
        clock.tick(30)
        window.blit(background, (0, 0))
        # Draw stuff here
        backSprites.clear(window, background)
        frontSprites.clear(window, background)
        backSprites.update()
        frontSprites.update()
        dirtyRects1 = backSprites.draw(window)
        dirtyRects2 = frontSprites.draw(window)
        dirtyRects = dirtyRects1 + dirtyRects2
        #pygame.display.update(dirtyRects)

        pygame.display.flip()

main()

