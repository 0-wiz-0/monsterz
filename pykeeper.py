#!/usr/bin/env python

import pygame
from pygame.locals import *
from random import randint

# constants
TIME_MAX = 2000000

screen_width = 800
screen_height = 600

board_width = 8
board_height = 8

animals = [
    { 'name': 'elephants', 'color': (127, 200, 255), 'img': None },
    { 'name': 'pandas', 'color': (255, 255, 255), 'img': None },
    { 'name': 'girafes', 'color': (255, 255, 63), 'img': None },
    { 'name': 'crocodiles', 'color': (63, 200, 63), 'img': None },
    { 'name': 'lions', 'color': (250, 160, 63), 'img': None },
    { 'name': 'baboons', 'color': (255, 63, 63), 'img': None },
    { 'name': 'hippos', 'color': (200, 63, 200), 'img': None },
    { 'name': 'bunnies', 'color': (255, 180, 180), 'img': None }
]

class AnimalSprite(pygame.sprite.Sprite):
    def __init__(self, type, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.image = type['img']
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
        pygame.draw.rect(tmp, (0, 0, 0), (0, sprite_size / 4, sprite_size, sprite_size * 2 / 4), sprite_size / 8)
        pygame.draw.rect(tmp, (0, 0, 0), (sprite_size / 4, 0, sprite_size * 2 / 4, sprite_size), sprite_size / 8)
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
                board[(x, y)] = random_animal()

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
    if time > 0:
        background.fill((210, 200, 150))
    else:
        background.fill((255, 20, 15))
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
    # Print score
    font = pygame.font.Font(None, screen_height / 5)
    delta = 1 + screen_height / 200
    for x in range(2):
        text = font.render(str(score), 2, (x * 255, x * 255, x * 255))
        background.blit(text, (sprite_size * board_width + sprite_size / 2 - delta * x, - delta * x))
    # Print done/needed:
    font = pygame.font.Font(None, screen_height / 8)
    delta = 1 + screen_height / 300
    x = sprite_size * board_width + sprite_size / 2
    y = sprite_size / 2 + screen_height / 10
    for a in animals:
        n = a['name']
        if needed[n] == 0:
            continue
        background.blit(a['img'], (x, y))
        for d in range(2):
            text = font.render(str(done[n]) + '/' + str(needed[n]), 2, (d * 255, d * 255, d * 255))
            background.blit(text, (x + sprite_size * 5 / 4 - delta * d, y - delta * d))
        y += screen_height / 10

def draw_time():
    x = sprite_size / 2
    y = screen_height * 18 / 20
    w = (board_width - 1) * sprite_size
    h = screen_height / 20
    w2 = w * time / 2000000
    if time <= 350000:
        color = (255, 0, 0)
    else:
        color = (255, 240, 0)
    pygame.draw.rect(background, (0, 0, 0), (x, y, w, h))
    if w2 > 0:
        pygame.draw.rect(background, color, (x, y, w * time / 2000000, h))

def new_board():
    global board
    for y in range(board_height):
        while True:
            for x in range(board_width):
                board[(x, y)] = random_animal()
            if not get_wins(board):
                break

def random_animal():
    if level < 8:
        return animals[randint(0, 6)]
    else:
        return animals[randint(0, 7)]

# Init values
board = {}
needed = {}
done = {}
select = (-1, -1)

# Compute stuff
sprite_size = screen_width / board_width
tmp = screen_height * 17 / 20 / board_height
if tmp < sprite_size:
    sprite_size = tmp

# Create sprites
for a in animals:
    tmp = pygame.Surface((sprite_size, sprite_size))
    tmp.set_colorkey(tmp.get_at((0, 0)), RLEACCEL)
    pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 2, sprite_size / 2), sprite_size * 4 / 9)
    pygame.draw.circle(tmp, a['color'], (sprite_size / 2, sprite_size / 2), sprite_size * 3 / 8)
    pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 3, sprite_size * 3 / 8), sprite_size / 8)
    pygame.draw.circle(tmp, (255, 255, 255), (sprite_size / 3, sprite_size * 3 / 8), sprite_size / 16)
    pygame.draw.circle(tmp, (20, 1, 1), (sprite_size - sprite_size / 3, sprite_size * 3 / 8), sprite_size / 8)
    pygame.draw.circle(tmp, (255, 255, 255), (sprite_size - sprite_size / 3, sprite_size * 3 / 8), sprite_size / 16)
    pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 2, sprite_size * 9 / 16), sprite_size / 16)
    pygame.draw.rect(tmp, (20, 1, 1), (sprite_size / 3, sprite_size * 11 / 16, sprite_size / 3, sprite_size / 16), sprite_size / 16)
    a['img'] = tmp

# Start all the stuff
pygame.init()
window = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Le meilleur jeu du monde')
background = pygame.Surface(window.get_size())

backSprites = pygame.sprite.RenderUpdates()
frontSprites = pygame.sprite.RenderUpdates()

def main():
    global select, score, done, level, time
    level = 0
    score = 0
    need_update = True
    new_level = True
    clock = pygame.time.Clock()
    oldticks = pygame.time.get_ticks()
    while True:
        # Compute level data
        if new_level:
            level += 1
            for a in animals:
                x = a['name']
                done[x] = 0
                if x == 'bunnies' and level < 8:
                    needed[x] = 0
                else:
                    needed[x] = level + 2
            new_board()
            time = TIME_MAX / 2
            new_level = False
        # Draw screen
        if need_update:
            while not list_moves(board):
                print 'no more moves!'
                new_board()
            draw_sprites()
            need_update = False
        draw_time()
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
        clock.tick(30)
        # Update time
        ticks = pygame.time.get_ticks()
        delta = (ticks - oldticks) * 400 / (11 - level)
        oldticks = ticks
        if time <= delta:
            need_update = True
        time -= delta
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
            if time <= 0:
                continue
            if event.type == MOUSEBUTTONDOWN:
                (x2, y2) = event.pos
                x2 /= sprite_size
                y2 /= sprite_size
                if x2 < 0 or x2 >= board_width or y2 < 0 or y2 >= board_height:
                    continue
                if select == (-1, -1):
                    select = (x2, y2)
                    need_update = True
                    continue
                (x1, y1) = select
                if x1 == x2 and y1 == y2:
                    select = (-1, -1)
                    need_update = True
                    continue
                if abs(x1 - x2) + abs(y1 - y2) != 1:
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
                    points = 0
                    iter = 0
                    msg = ''
                    while wins:
                        msg += enum_wins(wins)
                        for w in wins:
                            points += (10 * level) * (2 ** (iter + len(w) - 3))
                            time += 45000 * len(w)
                            for p in w:
                                if board.has_key(p):
                                    done[board[p]['name']] += 1
                                    del board[p]
                        fill_board()
                        wins = get_wins(board)
                        if wins:
                            msg += '+ '
                        iter += 1
                    if time > TIME_MAX:
                        time = TIME_MAX
                    #print msg, points
                    score += points
                select = (-1, -1)
                need_update = True
        # Check for new level
        new_level = True
        for a in animals:
            n = a['name']
            if done[n] < needed[n]:
                new_level = False
                break

main()

