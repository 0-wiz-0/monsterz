#!/usr/bin/env python

import pygame
from pygame.locals import *
from random import randint

# constants
AI = False
TIME_MAX = 2000000

screen_width = 500
screen_height = 400

board_width = 8
board_height = 8

animals = [
    { 'color': (127, 127, 127) },
    { 'color': (127, 200, 255) },
    { 'color': (230, 230, 230) },
    { 'color': (255, 255, 63) },
    { 'color': (63, 200, 63) },
    { 'color': (250, 160, 63) },
    { 'color': (255, 63, 63) },
    { 'color': (200, 63, 200) },
    { 'color': (255, 180, 180) }
]

class AnimalSprite(pygame.sprite.Sprite):
    def __init__(self, type, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.image = animals[type]['img']
        self.rect = tmp.get_rect()

class SelectSprite(pygame.sprite.Sprite):
    def __init__(self, group=None):
        pygame.sprite.Sprite.__init__(self, group)

        tmp = pygame.Surface((sprite_size, sprite_size))
        tmp.set_colorkey(tmp.get_at((0, 0)), RLEACCEL)
        pygame.draw.rect(tmp, (20, 20, 20), (0, 0, sprite_size, sprite_size), sprite_size / 6)
        pygame.draw.rect(tmp, (255, 255, 0), (0, 0, sprite_size, sprite_size), sprite_size / 8)
        pygame.draw.rect(tmp, (0, 0, 0), (0, sprite_size / 4, sprite_size, sprite_size * 2 / 4), sprite_size / 8)
        pygame.draw.rect(tmp, (0, 0, 0), (sprite_size / 4, 0, sprite_size * 2 / 4, sprite_size), sprite_size / 8)
        self.image = tmp
        self.rect  = tmp.get_rect()

def do_move(a, b):
    global board
    tmp = board[a]
    board[a] = board[b]
    board[b] = tmp

def list_moves(board):
    moves = []
    for y in range(board_height):
        for x in range(board_width - 1):
            do_move((x, y), (x + 1, y))
            if get_wins(board):
                moves.append([(x, y), (x + 1, y)])
            do_move((x, y), (x + 1, y))
        if y == board_height - 1:
            continue
        for x in range(board_width):
            do_move((x, y), (x, y + 1))
            if get_wins(board):
                moves.append([(x, y), (x, y + 1)])
            do_move((x, y), (x, y + 1))
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

def get_wins(board):
    wins = []
    # Horizontal
    for y in range(board_height):
        for x in range(board_width - 2):
            a = board.get((x, y))
            if not a or a == 0:
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
            if not a or a == 0:
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
        tmp.rect.center = (x + sprite_size / 2, y + sprite_size / 2)
    # Draw selector
    if select:
        tmp = SelectSprite(backSprites)
        (x, y) = select
        x *= sprite_size
        y *= sprite_size
        tmp.rect.center = (x + sprite_size / 2, y + sprite_size / 2)
    # Print score
    font = pygame.font.Font(None, screen_height / 8)
    delta = 1 + screen_height / 200
    for x in range(2):
        text = font.render(str(score), 2, (x * 255, x * 255, x * 255))
        background.blit(text, (sprite_size * board_width + sprite_size / 2 - delta * x, - delta * x))
    # Print done/needed:
    font = pygame.font.Font(None, screen_height / 12)
    delta = 1 + screen_height / 300
    x = sprite_size * board_width + sprite_size / 2
    y = sprite_size / 2 + screen_height / 8
    for i in range(population):
        a = animals[i + 1]
        background.blit(a['img'], (x, y))
        for d in range(2):
            text = font.render(str(done[i + 1]) + '/' + str(needed[i + 1]), 2, (d * 255, d * 255, d * 255))
            background.blit(text, (x + sprite_size * 5 / 4 - delta * d, y + screen_height / 64 - delta * d))
        y += screen_height / 10
    # Print bonus:
    for x in bonus:
        for d in range(2):
            text = font.render(str(x[2]), 2, (d * 255, d * 255, d * 255))
            background.blit(text, (x[0] * sprite_size + sprite_size / 4 - delta * d, x[1] * sprite_size + sprite_size / 4 - delta * d))

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

def random_animal(no_special = False):
    if not no_special and randint(0, 1000) == 0:
        return 0
    return randint(1, population)

# Init values
board = {}
needed = {}
done = {}
bonus = []
select = None

# Compute stuff
sprite_size = screen_width / board_width
tmp = screen_height * 17 / 20 / board_height
if tmp < sprite_size:
    sprite_size = tmp

# Create sprites
for x in range(len(animals)):
    a = animals[x]
    tmp = pygame.Surface((sprite_size, sprite_size))
    tmp.set_colorkey(tmp.get_at((0, 0)), RLEACCEL)
    if x != 0:
        pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 2, sprite_size / 2), sprite_size * 4 / 9)
        pygame.draw.circle(tmp, a['color'], (sprite_size / 2, sprite_size / 2), sprite_size * 3 / 8)
    else:
        pygame.draw.rect(tmp, a['color'], (0, 0, sprite_size, sprite_size), sprite_size)
        pygame.draw.rect(tmp, (20, 1, 1), (0, 0, sprite_size, sprite_size), sprite_size / 8)
    pygame.draw.circle(tmp, (255, 255, 255), (sprite_size / 3, sprite_size * 3 / 8), sprite_size / 8)
    pygame.draw.circle(tmp, (20, 1, 1), (sprite_size / 3, sprite_size * 3 / 8), sprite_size / 16)
    pygame.draw.circle(tmp, (255, 255, 255), (sprite_size - sprite_size / 3, sprite_size * 3 / 8), sprite_size / 8)
    pygame.draw.circle(tmp, (20, 1, 1), (sprite_size - sprite_size / 3, sprite_size * 3 / 8), sprite_size / 16)
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
    global select, score, done, level, population, bonus, time
    level = 0
    score = 0
    resolve_wins = False
    need_update = True
    need_refresh = True
    new_level = True
    get_imput = True
    will_play = None
    clock = pygame.time.Clock()
    oldticks = pygame.time.get_ticks()
    while True:
        ticks = pygame.time.get_ticks()
        delta = (ticks - oldticks) * 400 / (11.0000001 - level) # FIXME
        oldticks = ticks
        # Compute level data
        if new_level:
            level += 1
            if level >= 8:
                population = 8
            else:
                population = 7
            for i in range(population):
                x = animals[i + 1]
                done[i + 1] = 0
                if i + 1 == 8 and level < 8:
                    needed[i + 1] = 0
                else:
                    needed[i + 1] = level + 2
            new_board()
            time = TIME_MAX / 2
            need_update = True
            new_level = False
        # Draw screen
        if need_update:
            while not list_moves(board):
                print 'no more moves!'
                new_board()
            need_refresh = True
            need_update = False
        if need_refresh:
            draw_sprites()
            need_refresh = False
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
        # Resolve winning moves and chain reactions
        if resolve_wins:
            if win_counter is 15:
                scorebonus = 0
                timebonus = 0
                for w in wins:
                    if len(w) is 1:
                        points = 10 * level
                    else:
                        points = (10 * level) * (2 ** (win_iter + len(w) - 3))
                    scorebonus += points
                    timebonus += 45000 * len(w)
                    (x, y) = (0.0, 0.0)
                    for (x2, y2) in w:
                        x += x2
                        y += y2
                        if board.has_key((x2, y2)):
                            done[board[(x2, y2)]] += 1
                            del board[(x2, y2)]
                    bonus.append([x / len(w), y / len(w), points])
                need_refresh = True
            elif win_counter is 8:
                bonus = []
                need_refresh = True
            elif win_counter is 5:
                time += timebonus
                if time > TIME_MAX:
                    time = TIME_MAX
                score += scorebonus
                fill_board()
                need_refresh = True
            elif win_counter is 0:
                wins = get_wins(board)
                if wins:
                    win_counter = 20
                    win_iter += 1
                else:
                    resolve_wins = False
                    # Check for new level
                    new_level = True
                    for i in range(population):
                        n = i + 1
                        if done[n] < needed[n]:
                            new_level = False
                            break
                need_update = True
            if win_counter:
                win_counter -= 1
                continue
        if new_level:
            continue
        if not get_imput:
            continue
        # Handle events
        played = None
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
            if time <= 0:
                continue
            #if event.type == KEYDOWN and event.key == K_n:
            #    level -= 1
            #    new_level = True
            if event.type == MOUSEBUTTONDOWN:
                (x2, y2) = event.pos
                x2 /= sprite_size
                y2 /= sprite_size
                if x2 < 0 or x2 >= board_width or y2 < 0 or y2 >= board_height:
                    continue
                played = (x2, y2)
                break
        # If animating something, continue
        # Update time
        if time <= delta:
            need_refresh = True
        time -= delta
        if AI:
            if not will_play:
                moves = list_moves(board)
                if moves:
                    will_play = moves[len(moves) - 1]
                    timer = 15 - level
            if timer is (15 - level) / 2:
                played = will_play[0] # FIXME: problem with special pieces
            elif timer is 0:
                played = will_play[1]
                will_play = None
            timer -= 1
        # Handle plays
        if played:
            if not select:
                if board[played] != 0:
                    select = played
                    need_refresh = True
                    continue
                # Deal with the special block
                wins = []
                target = random_animal(no_special = True)
                found = 0
                for y in range(board_height):
                    for x in range(board_width):
                        if board[(x, y)] == target:
                            wins.append([(x, y)])
                board[played] = target
                wins.append([played])
                win_iter = 0
                win_counter = 20
                resolve_wins = True
                need_refresh = True
                continue
            (x1, y1) = select
            (x2, y2) = played
            if x1 == x2 and y1 == y2:
                select = None
                need_refresh = True
                continue
            if abs(x1 - x2) + abs(y1 - y2) != 1:
                continue
            tmp = board[select]
            board[select] = board[played]
            board[played] = tmp
            wins = get_wins(board)
            if not wins:
                tmp = board[select]
                board[select] = board[played]
                board[played] = tmp
            select = None
            win_iter = 0
            win_counter = 20
            resolve_wins = True
            need_refresh = True

main()

