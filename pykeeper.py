#!/usr/bin/env python

import pygame
from pygame.locals import *
from random import randint

screen_width = 640
screen_height = 480

board_width = 8
board_height = 8

animals = [
    { 'name': 'elephants', 'color': (127, 200, 255) },
    { 'name': 'pandas', 'color': (255, 255, 255) },
    { 'name': 'girafes', 'color': (255, 255, 63) },
    { 'name': 'crocodiles', 'color': (63, 200, 63) },
    { 'name': 'lions', 'color': (250, 160, 63) },
    { 'name': 'baboons', 'color': (255, 63, 63) },
    { 'name': 'hippos', 'color': (200, 63, 200) },
    { 'name': 'rabbits', 'color': (255, 180, 180) }
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

def do_move(a, b):
    global board
    tmp = board[a]
    board[a] = board[b]
    board[b] = tmp

def list_moves(board):
    moves = []
    for y in range(board_height - 1):
        for x in range(board_width - 1):
            do_move((x, y), (x, y + 1))
            if get_wins(board):
                moves.append([(x, y), (x, y + 1)])
            do_move((x, y), (x, y + 1))
            do_move((x, y), (x + 1, y))
            if get_wins(board):
                moves.append([(x, y), (x + 1, y)])
            do_move((x, y), (x + 1, y))
    return moves

def fill_board():
    global board
    for z in range(board_height):
        y = board_height - z - 1
        for x in range(board_width):
            if board.has_key((x, y)):
                continue
            found = None
            for y2 in range(0, y):
                if board.has_key((x, y2)):
                    found = (x, y2)
            if found:
                board[(x, y)] = board[found]
                del board[found]
            else:
                board[(x, y)] = animals[randint(0, len(animals) - 1)]

def enum_wins(wins):
    msg = ''
    for w in wins:
        msg += str(len(w)) + ' ' + board[w[0]]['name'] + ' '
    return msg

def reduce_wins(wins):
    new = []
    for i in range(len(wins)):
        unknown = True
        for j in range(len(new)):
            hasit = False
            for x in wins[i]:
                if x in new[j]:
                    hasit = True
                    break
            if hasit:
                for x in wins[i]:
                    if x not in new[j]:
                        new[j].append(x)
                unknown = False
                break
        if unknown:
            new.append(wins[i])
    return new

def get_wins(board):
    wins = []
    # Horizontal
    for y in range(board_height):
        for x in range(board_width - 2):
            a = board.get((x, y))
            if not a:
                continue
            b = board.get((x - 1, y))
            if b and a == b:
                continue
            len = 1
            for t in range(1, board_width - x):
                b = board.get((x + t, y))
                if a != b:
                    break
                len += 1
            if len < 3:
                continue
            win = []
            for t in range(len):
                win.append((x + t, y))
            wins.append(win)
    # Horizontal
    for x in range(board_width):
        for y in range(board_height - 2):
            a = board.get((x, y))
            if not a:
                continue
            b = board.get((x, y - 1))
            if b and a == b:
                continue
            len = 1
            for t in range(1, board_height - y):
                b = board.get((x, y + t))
                if a != b:
                    break
                len += 1
            if len < 3:
                continue
            win = []
            for t in range(len):
                win.append((x, y + t))
            wins.append(win)
    return wins

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

def new_game():
    global board
    for y in range(board_height):
        while True:
            for x in range(board_width):
                board[(x, y)] = animals[randint(0, len(animals) - 1)]
            if not get_wins(board):
                break

# Init values
board = {}
select = (-1, -1)
level = 1

# Compute stuff
sprite_size = screen_width / board_width
tmp = screen_height / board_height
if tmp < sprite_size:
    sprite_size = tmp

# Start all the stuff
pygame.init()
window = pygame.display.set_mode((640, 480))
pygame.display.set_caption('Le meilleur jeu du monde')
background = pygame.Surface(window.get_size())
background.fill((210,200,150))

backSprites = pygame.sprite.RenderUpdates()
frontSprites = pygame.sprite.RenderUpdates()

new_game()
draw_sprites()

def main():
    global select
    need_update = True
    clock = pygame.time.Clock()
    pygame.time.get_ticks()
    while True:
        if need_update:
            while not list_moves(board):
                print 'no more moves!'
                new_game()
            draw_sprites()
            need_update = False
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
                wins = get_wins(board)
                if not wins:
                    tmp = board[(x1, y1)]
                    board[(x1, y1)] = board[(x2, y2)]
                    board[(x2, y2)] = tmp
                else:
                    score = 0
                    iter = 0
                    msg = ''
                    while wins:
                        msg += enum_wins(wins)
                        for w in wins:
                            score += (10 * level) * (2 ** (iter + len(w) - 3))
                            for p in w:
                                if board.has_key(p): del board[p]
                        fill_board()
                        wins = get_wins(board)
                        if wins:
                            msg += '+ '
                        iter += 1
                    print msg, score
                select = (-1, -1)
                need_update = True
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

