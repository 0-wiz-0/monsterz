#!/usr/bin/env python

"""
 alienkeeper: puzzle game
 $Id$

 Copyright: (c) 2005 Sam Hocevar <sam@zoy.org>
   This program is free software; you can redistribute it and/or
   modify it under the terms of the Do What The Fuck You Want To
   Public License, Version 2, as published by Sam Hocevar. See
   http://sam.zoy.org/projects/COPYING.WTFPL for more details.
"""

import pygame
from pygame.locals import *
from random import randint
from sys import argv
from os.path import join, dirname

# constants
AI = False
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

EXIT_QUIT = -1
EXIT_REPLAY = -2

LOST_DELAY = 50
SCROLL_DELAY = 50
WIN_DELAY = 12
SWITCH_DELAY = 5

class Theme:
    def __init__(self, dir = dirname(argv[0])):
        # Load stuff
        tiles = pygame.image.load(join(dir, 'tiles.png'))
        (w, h) = tiles.get_rect().size
        if w * 9 != h * 5:
            raise 'error: ' + file + ' has wrong image size'
        self.board = pygame.image.load(join(dir, 'board.png'))
        self.tiles = tiles.convert_alpha()
        self.orig_size = w / 5
        self.tile_size = None
        self.normal = {}
        self.blink = {}
        self.tiny = {}
        self.surprise = {}
        self.angry = {}
        self.exploded = {}
        self.special = {}
        self.selector = None

    def make_sprites(self, t):
        self.tile_size = t
        s = self.orig_size
        scale = pygame.transform.scale
        crop = self.tiles.subsurface
        # Create sprites
        for x in range(8):
            self.normal[x] = scale(crop((0, (x+1) * s, s, s)), (t, t))
            self.tiny[x] = scale(crop((0, (x+1) * s, s, s)), (t * 3 / 4, t * 3 / 4))
            self.blink[x] = scale(crop((s, (x+1) * s, s, s)), (t, t))
            self.surprise[x] = scale(crop((s * 2, (x+1) * s, s, s)), (t, t))
            self.angry[x] = scale(crop((s * 3, (x+1) * s, s, s)), (t, t))
            self.exploded[x] = scale(crop((s * 4, (x+1) * s, s, s)), (t, t))
            #tmp = crop((s, 0, s, s)).copy() # marche pas !
            spcial = scale(crop((s, 0, s, s)), (s, s))
            mini = crop((0, (x+1) * s, s, s))
            # Crappy FX
            mini = scale(mini, (s * 7 / 8, s * 7 / 8))
            spcial.blit(mini, (s / 16, s / 16))
            self.special[x] = scale(spcial, (t, t))
        # Create selector sprite
        self.selector = scale(crop((0, 0, s, s)), (t, t))

# Start all the stuff
class Game:
    def __init__(self, size = (8, 8), level = 1):
        # Init values
        (self.board_width, self.board_height) = size
        self.needed = {}
        self.done = {}
        self.bonus_list = []
        self.blink_list = {}
        self.disappear_list = []
        self.surprised_list = []
        self.clicks = []
        self.select = None
        self.switch = None
        # Compute stuff
        tile_size = (SCREEN_WIDTH - 20) / self.board_width
        tmp = (SCREEN_HEIGHT - 20) * 17 / 20 / self.board_height
        if tmp < tile_size:
            tile_size = tmp
        theme.make_sprites(tile_size)
        # Other initialisation stuff
        self.score = 0
        self.special_index = 0
        self.lost_timer = 0
        self.lost_offset = {}
        for y in range(self.board_height):
            for x in range(self.board_width):
                self.lost_offset[(x, y)] = (0, 0)
        self.win_timer = 0
        self.switch_timer = 0
        self.level_timer = SCROLL_DELAY / 2
        self.board_timer = 0
        self.missed = False
        self.check_moves = False
        self.will_play = None
        self.clock = pygame.time.Clock()
        self.oldticks = pygame.time.get_ticks()
        self.pause = False
        self.pause_bitmap = None
        self.exit = False
        self.play_again = False
        self.level = level
        self.new_level()

    def go(self):
        while not self.exit:
            self.iterate()
            self.clock.tick(15)

    def get_random(self, no_special = False):
        if not no_special and randint(0, 500) == 0:
            return 0
        return randint(1, self.population)

    def new_board(self):
        self.board = {}
        for y in range(self.board_height):
            while True:
                for x in range(self.board_width):
                    self.board[(x, y)] = self.get_random()
                if not self.get_wins():
                    break
                msg = ''
                for x in range(self.board_width):
                    msg += str(self.board[(x, y)])

    def fill_board(self):
        for z in range(self.board_height):
            y = self.board_height - z - 1
            for x in range(self.board_width):
                if self.board.has_key((x, y)):
                    continue
                found = None
                for y2 in range(0, y):
                    if self.board.has_key((x, y2)):
                        found = (x, y2)
                if found:
                    self.board[(x, y)] = self.board[found]
                    del self.board[found]
                else:
                    self.board[(x, y)] = self.get_random()

    def get_wins(self):
        wins = []
        # Horizontal
        for y in range(self.board_height):
            for x in range(self.board_width - 2):
                a = self.board.get((x, y))
                if not a or a == 0:
                    continue
                b = self.board.get((x - 1, y))
                if b and a == b:
                    continue
                len = 1
                for t in range(1, self.board_width - x):
                    b = self.board.get((x + t, y))
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
        for x in range(self.board_width):
            for y in range(self.board_height - 2):
                a = self.board.get((x, y))
                if not a or a == 0:
                    continue
                b = self.board.get((x, y - 1))
                if b and a == b:
                    continue
                len = 1
                for t in range(1, self.board_height - y):
                    b = self.board.get((x, y + t))
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

    def do_move(self, a, b):
        tmp = self.board[a]
        self.board[a] = self.board[b]
        self.board[b] = tmp

    def list_moves(self):
        checkme = [[(+2,  0), (+3,  0)],
                   [(+1, -1), (+1, -2)],
                   [(+1, -1), (+1, +1)],
                   [(+1, +1), (+1, +2)]]
        delta = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for y in range(self.board_height):
            for x in range(self.board_width):
                a = self.board.get((x, y))
                if a == 0:
                   continue # We don't want no special piece
                for [(a1, b1), (a2, b2)] in checkme:
                    for (dx, dy) in delta:
                        if a == self.board.get((x + dx * a1 + dy * b1, y + dx * b1 + dy * a1)) and \
                           a == self.board.get((x + dx * a2 + dy * b2, y + dx * b2 + dy * a2)):
                            yield [(x, y), (x + dx, y + dy)]

    def new_level(self):
        # Compute level data
        if self.level < 7:
            self.population = 7
        else:
            self.population = 8
        for i in range(self.population):
            self.done[i + 1] = 0
            self.needed[i + 1] = self.level + 2
        self.angry_tiles = -1
        self.new_board()
        self.time = 1000000

    def board2screen(self, coord):
        (x, y) = coord
        return (x * theme.tile_size + 24, y * theme.tile_size + 24)

    def screen2board(self, coord):
        (x, y) = coord
        return ((x - 24) / theme.tile_size, (y - 24) / theme.tile_size)

    def draw_board(self):
        # Have a random piece blink
        if randint(0, 7) is 0:
            x, y = randint(0, self.board_width - 1), randint(0, self.board_height - 1)
            self.blink_list[(x, y)] = 5
        # Handle special scrolling cases
        if self.level_timer:
            timer = self.level_timer
        elif self.board_timer:
            timer = self.board_timer
        else:
            timer = 0
        if timer > SCROLL_DELAY / 2:
            xoff = 0
            yoff = (SCROLL_DELAY - timer) * (SCROLL_DELAY - timer)
        elif timer > 0:
            xoff = 0
            yoff = - timer * timer
        else:
            xoff = 0
            yoff = 0
        if self.switch_timer:
            (x1, y1) = self.board2screen(self.select)
            (x2, y2) = self.board2screen(self.switch)
            t = self.switch_timer * 1.0 / SWITCH_DELAY
        for (c, n) in self.board.items():
            # Decide the coordinates
            if c == self.switch and self.switch_timer:
                (x, y) = (x2 * t + x1 * (1 - t), y2 * t + y1 * (1 - t))
            elif c == self.select and self.switch_timer:
                (x, y) = (x1 * t + x2 * (1 - t), y1 * t + y2 * (1 - t))
            else:
                (x, y) = self.board2screen(c)
            if self.lost_timer:
                (xoff, yoff) = self.lost_offset[c]
                d = LOST_DELAY - self.lost_timer
                xoff += (randint(0, d) - randint(0, d)) * randint(0, d) / 4
                yoff += (randint(0, d) - randint(0, d)) * randint(0, d) / 4
                self.lost_offset[c] = (xoff, yoff)
            # Decide the shape
            if n == 0:
                shape = theme.special[self.special_index]
            elif self.level_timer and self.level_timer < SCROLL_DELAY / 2:
                shape = theme.blink[n - 1]
            elif c in self.surprised_list \
              or self.board_timer > SCROLL_DELAY / 2 \
              or self.level_timer > SCROLL_DELAY / 2:
                shape = theme.surprise[n - 1]
            elif c in self.disappear_list:
                shape = theme.exploded[n - 1]
            elif n == self.angry_tiles:
                shape = theme.angry[n - 1]
            elif self.blink_list.has_key(c):
                shape = theme.blink[n - 1]
                self.blink_list[c] -= 1
                if self.blink_list[c] is 0:
                    del self.blink_list[c]
            else:
                shape = theme.normal[n - 1]
            # Remember the selector coordinates
            if c == self.select and not self.missed \
            or c == self.switch and self.missed:
                select_coord = (x, y)
                shape = theme.blink[n - 1] # Not sure if it looks nice
            # Print the shit
            background.blit(shape, (x + xoff, y + yoff))
        # Draw selector if necessary
        if self.select:
            background.blit(theme.selector, select_coord)

    def toggle_pause(self):
        self.pause = not self.pause
        if self.pause:
            self.pause_bitmap = pygame.transform.scale(theme.normal[self.get_random(no_special = True)], (8 * theme.tile_size, 8 * theme.tile_size))
        else:
            del self.pause_bitmap

    def draw_game(self):
        # Draw background
        background.blit(theme.board, (0, 0))
        # Draw timebar
        x = 16; y = 440; w = 400; h = 24
        w2 = w * self.time / 2000000
        if self.time <= 350000:
            color = (255, 0, 0)
        else:
            color = (255, 240, 0)
        pygame.draw.rect(background, (0, 0, 0), (x, y, w, h))
        if w2 > 0:
            pygame.draw.rect(background, color, (x, y, w * self.time / 2000000, h))
        # Draw pieces
        if self.pause:
            background.blit(self.pause_bitmap, (24, 24))
            font = pygame.font.Font(None, SCREEN_HEIGHT / 4)
            delta = 1 + SCREEN_HEIGHT / 100
            for x in range(2):
                text = font.render('PAUSED', 2, (x * 255, x * 255, x * 255))
                (w, h) = text.get_rect().size
                background.blit(text, (theme.tile_size * self.board_width / 2 - w / 2 + 24 - delta * x, theme.tile_size * self.board_height * 7 / 8 - h / 2 + 24 - delta * x))
        elif self.lost_timer >= 0:
            self.draw_board()
        # Print score
        font = pygame.font.Font(None, SCREEN_HEIGHT / 8)
        delta = 1 + SCREEN_HEIGHT / 200
        for x in range(2):
            text = font.render(str(self.score), 2, (x * 255, x * 255, x * 255))
            background.blit(text, (theme.tile_size * self.board_width + theme.tile_size * 3 / 2 - delta * x, 10 - delta * x))
        # Print play again message
        if self.lost_timer < 0:
            font = pygame.font.Font(None, SCREEN_HEIGHT / 10)
            delta = 1 + SCREEN_HEIGHT / 300
            for x in range(2):
                text = font.render('CLICK TO PLAY AGAIN', 2, (x * 255, x * 255, x * 255))
                (w, h) = text.get_rect().size
                background.blit(text, (theme.tile_size * self.board_width / 2 - w / 2 + 24 - delta * x, theme.tile_size * self.board_height / 2 - h / 2 + 24 - delta * x))
        # Print new level stuff
        if self.level_timer and (self.level > 1 or self.level_timer > SCROLL_DELAY / 2):
            if self.level_timer > SCROLL_DELAY / 2:
                msg = 'LEVEL UP'
            else:
                msg = 'LEVEL ' + str(self.level)
            font = pygame.font.Font(None, SCREEN_HEIGHT / 4)
            delta = 1 + SCREEN_HEIGHT / 100
            for x in range(2):
                text = font.render(msg, 2, (x * 255, x * 255, x * 255))
                (w, h) = text.get_rect().size
                background.blit(text, (theme.tile_size * self.board_width / 2 - w / 2 + 24 - delta * x, theme.tile_size * self.board_height / 2 - h / 2 + 24 - delta * x))
        # Print 'no more moves' stuff
        if self.board_timer > SCROLL_DELAY / 2:
            font = pygame.font.Font(None, SCREEN_HEIGHT / 8)
            delta = 1 + SCREEN_HEIGHT / 300
            for x in range(2):
                text = font.render('NO MORE MOVES!', 2, (x * 255, x * 255, x * 255))
                (w, h) = text.get_rect().size
                background.blit(text, (theme.tile_size * self.board_width / 2 - w / 2 + 24 - delta * x, theme.tile_size * self.board_height / 2 - h / 2 + 24 - delta * x))
        # Print bonus
        font = pygame.font.Font(None, theme.tile_size * 3 / 4)
        for b in self.bonus_list:
            for d in range(2):
                text = font.render(str(b[1]), 2, (d * 255, d * 255, d * 255))
                (x, y) = self.board2screen(b[0])
                background.blit(text, (x + theme.tile_size / 4 - delta * d, y + theme.tile_size / 4 - delta * d))
        # Print done/needed
        delta = 1 + SCREEN_HEIGHT / 300
        x = theme.tile_size * self.board_width + theme.tile_size * 3 / 2
        y = theme.tile_size / 2 + SCREEN_HEIGHT / 8
        for i in range(self.population):
            background.blit(theme.tiny[i], (x, y))
            for d in range(2):
                text = font.render(str(self.done[i + 1]) + '/' + str(self.needed[i + 1]), 2, (d * 255, d * 255, d * 255))
                background.blit(text, (x + theme.tile_size * 5 / 4 - delta * d, y + SCREEN_HEIGHT / 64 - delta * d))
            y += SCREEN_HEIGHT / 12
        window.blit(background, (0, 0))
        pygame.display.flip()

    def iterate(self):
        ask_pause = False
        ticks = pygame.time.get_ticks()
        delta = (ticks - self.oldticks) * 400 / (11.0000001 - self.level) # FIXME
        self.oldticks = ticks
        self.special_index = (self.special_index + 1) % self.population
        # Draw screen
        if self.check_moves:
            for move in self.list_moves():
                break
            else:
                self.board_timer = SCROLL_DELAY
            self.check_moves = False
            self.clicks = []
        self.draw_game()
        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                self.exit = EXIT_QUIT
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                self.exit = EXIT_QUIT
                return
            elif event.type == KEYDOWN and event.key == K_f:
                pygame.display.toggle_fullscreen()
                return
            elif event.type == KEYDOWN and event.key == K_p:
                ask_pause = True
            elif event.type == MOUSEBUTTONDOWN:
                if self.lost_timer < 0:
                    self.exit = EXIT_REPLAY
                    return
                (x2, y2) = self.screen2board(event.pos)
                if x2 < 0 or x2 >= self.board_width or y2 < 0 or y2 >= self.board_height:
                    continue
                self.clicks.append((x2, y2))
        # If paused, do nothing
        if self.pause and not ask_pause:
            return
        # Resolve winning moves and chain reactions
        if self.board_timer:
            self.board_timer -= 1
            if self.board_timer is SCROLL_DELAY / 2:
                self.new_board()
            elif self.board_timer is 0:
                self.check_moves = True # Need to check again
            return
        if self.lost_timer:
            self.lost_timer -= 1
            if self.lost_timer is 0:
                print str(self.level) + ':' + str(self.score)
                self.lost = True
                self.lost_timer = -1 # Continue forever
            return
        if self.switch_timer:
            self.switch_timer -= 1
            if self.switch_timer is 0:
                self.do_move(self.select, self.switch)
                if self.missed:
                    self.clicks = []
                    self.missed = False
                else:
                    self.wins = self.get_wins()
                    if not self.wins:
                        self.missed = True
                        self.switch_timer = SWITCH_DELAY
                        return
                    self.win_iter = 0
                    self.win_timer = WIN_DELAY
                self.select = None
                self.switch = None
            return
        if self.level_timer:
            self.level_timer -= 1
            if self.level_timer is SCROLL_DELAY / 2:
                self.level += 1
                self.new_level()
            elif self.level_timer is 0:
                self.blink_list = {}
                self.check_moves = True
            return
        if self.win_timer:
            self.win_timer -= 1
            if self.win_timer is WIN_DELAY * 5 / 6:
                for w in self.wins:
                    for (x, y) in w:
                        self.surprised_list.append((x, y))
            elif self.win_timer is WIN_DELAY * 3 / 6:
                self.scorebonus = 0
                self.timebonus = 0
                for w in self.wins:
                    if len(w) is 1:
                        points = 10 * self.level
                    else:
                        points = (10 * self.level) * (2 ** (self.win_iter + len(w) - 3))
                    self.scorebonus += points
                    self.timebonus += 45000 * len(w)
                    (x2, y2) = (0.0, 0.0)
                    for (x, y) in w:
                        x2 += x
                        y2 += y
                    self.bonus_list.append([(x2 / len(w), y2 / len(w)), points])
                self.disappear_list = self.surprised_list
                self.surprised_list = []
            elif self.win_timer is WIN_DELAY * 2 / 6:
                self.bonus_list = []
                for (x, y) in self.disappear_list:
                    if self.board.has_key((x, y)):
                        self.done[self.board[(x, y)]] += 1
                        del self.board[(x, y)]
                if self.angry_tiles == -1:
                    unfinished = 0
                    for i in range(self.population):
                        if self.done[i + 1] < self.needed[i + 1]:
                            unfinished += 1
                            angry = i + 1
                    if unfinished == 1:
                        self.angry_tiles = angry
                self.disappear_list = []
            elif self.win_timer is WIN_DELAY / 6:
                self.time += self.timebonus
                if self.time > 2000000:
                    self.time = 2000000
                self.score += self.scorebonus
                self.fill_board()
            elif self.win_timer is 0:
                self.wins = self.get_wins()
                if self.wins:
                    self.win_timer = WIN_DELAY
                    self.win_iter += 1
                else:
                    # Check for new level
                    finished = True
                    for i in range(self.population):
                        n = i + 1
                        if self.done[n] < self.needed[n]:
                            finished = False
                            break
                    if finished:
                        self.select = None
                        self.level_timer = SCROLL_DELAY
                    else:
                        self.check_moves = True
            return
        # Update time
        self.time -= delta
        if self.time <= 0:
            self.lost_timer = LOST_DELAY
            return
        # Honour pause request
        if ask_pause:
            self.toggle_pause()
            return
        # Handle moves from the AI:
        if AI:
            if not self.will_play:
                self.will_play = None
                # Special piece?
                if randint(0, 3) == 0:
                    special = None
                    for y in range(self.board_height):
                        for x in range(self.board_width):
                            if self.board[(x, y)] == 0:
                                special = (x, y)
                                break
                        if special:
                            break
                    if special:
                        incomplete = 0
                        for i in range(self.population):
                            if self.done[i + 1] >= self.needed[i + 1]:
                                incomplete += 1
                                if incomplete == 2:
                                    break
                        if incomplete == 2 or randint(0, 3) == 0:
                            self.will_play = [None, special]
                # Normal piece
                if not self.will_play:
                    min = 0
                    for move in self.list_moves():
                        color = self.board.get(move[0])
                        if self.done[color] >= min or \
                           self.done[color] >= self.needed[color]:
                            self.will_play = move
                            min = self.done[color]
                self.ai_timer = 15 - self.level
            if self.ai_timer is (15 - self.level) / 2:
                self.clicks.append(self.will_play[0])
            elif self.ai_timer is 0:
                self.clicks.append(self.will_play[1])
                self.will_play = None
            self.ai_timer -= 1
        # Handle moves from the player or the AI
        if self.clicks:
            played = self.clicks.pop(0)
            if self.select:
                (x1, y1) = self.select
                (x2, y2) = played
                if x1 == x2 and y1 == y2:
                    self.select = None
                    return
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    return
                self.switch = played
                self.switch_timer = SWITCH_DELAY
            else:
                if self.board[played] != 0:
                    self.select = played
                    return
                # Deal with the special block
                self.wins = []
                target = 1 + self.special_index
                found = 0
                for y in range(self.board_height):
                    for x in range(self.board_width):
                        if self.board[(x, y)] == target:
                            self.wins.append([(x, y)])
                self.board[played] = target
                self.wins.append([played])
                self.win_iter = 0
                self.win_timer = WIN_DELAY
            return

# Init Pygame
pygame.init()
# Sound test
#pygame.mixer.get_init()
#sound = pygame.mixer.Sound('foo.wav')
#sound.play()
# Init display
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Alienkeeper')
background = pygame.Surface(window.get_size())
# Read commandline (haha)
level = 1
size = (8, 8)
# Go!
theme = Theme()
while True:
    game = Game(size = size, level = level)
    game.go()
    if game.exit == EXIT_QUIT:
        break
