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
screen_width = 640
screen_height = 480

class Theme:
    def __init__(self, file):
        # Load stuff
        self.tiles = pygame.image.load(file)
        (w, h) = self.tiles.get_rect().size
        if w * 9 != h * 4:
            raise 'error: ' + file + ' has wrong image size'
        self.tiles = self.tiles.convert_alpha()
        self.orig_size = w / 4
        self.tile_size = 0
        self.normal = {}
        self.tiny = {}
        self.surprised = {}
        self.angry = {}
        self.exploded = {}
        self.special = {}
        self.selector = None

    def make_sprites(self, size):
        self.tile_size = size
        # Create sprites
        for x in range(8):
            self.normal[x] = pygame.transform.scale(self.tiles.subsurface((0, (x + 1) * self.orig_size, self.orig_size, self.orig_size)), (size, size))
            self.tiny[x] = pygame.transform.scale(self.tiles.subsurface((0, (x + 1) * self.orig_size, self.orig_size, self.orig_size)), (size * 3 / 4, size * 3 / 4))
            self.surprised[x] = pygame.transform.scale(self.tiles.subsurface((self.orig_size, (x + 1) * self.orig_size, self.orig_size, self.orig_size)), (size, size))
            self.angry[x] = pygame.transform.scale(self.tiles.subsurface((self.orig_size * 2, (x + 1) * self.orig_size, self.orig_size, self.orig_size)), (size, size))
            self.exploded[x] = pygame.transform.scale(self.tiles.subsurface((self.orig_size * 3, (x + 1) * self.orig_size, self.orig_size, self.orig_size)), (size, size))
            #tmp = pygame.Surface((self.orig_size, self.orig_size))
            #tmp.blit(self.tiles.subsurface((self.orig_size, 0, self.orig_size, self.orig_size)), (0, 0))
            #tmp = self.tiles.subsurface((self.orig_size, 0, self.orig_size, self.orig_size)).copy()
            tmp = pygame.transform.scale(self.tiles.subsurface((self.orig_size, 0, self.orig_size, self.orig_size)), (self.orig_size, self.orig_size))
            tmp2 = self.tiles.subsurface((0, (x + 1) * self.orig_size, self.orig_size, self.orig_size))
            # Crappy FX
            tmp2 = pygame.transform.scale(tmp2, (self.orig_size * 7 / 8, self.orig_size * 7 / 8))
            tmp.blit(tmp2, (self.orig_size / 16, self.orig_size / 16))
            #tmp2 = pygame.transform.scale(tmp2, (self.orig_size / 4, self.orig_size / 4))
            #tmp2 = pygame.transform.scale(tmp2, (self.orig_size, self.orig_size))
            #tmp.blit(tmp2, (0, 0))
            self.special[x] = pygame.transform.scale(tmp, (size, size))
        # Create selector sprite
        self.selector = pygame.transform.scale(self.tiles.subsurface((0, 0, self.orig_size, self.orig_size)), (size, size))

# Start all the stuff
class Game:
    def __init__(self, size = (8, 8), level = 1):
        # Init values
        (self.board_width, self.board_height) = size
        self.needed = {}
        self.done = {}
        self.bonus_list = []
        self.disappear_list = []
        self.surprised_list = []
        self.select = None
        self.switch = None
        # Compute stuff
        tile_size = (screen_width - 20) / self.board_width
        tmp = (screen_height - 20) * 17 / 20 / self.board_height
        if tmp < tile_size:
            tile_size = tmp
        theme.make_sprites(tile_size)
        # Other initialisation stuff
        self.score = 0
        self.special_timer = 0
        self.lost_timer = 0
        self.lost_offset = {}
        for y in range(self.board_height):
            for x in range(self.board_width):
                self.lost_offset[(x, y)] = (0, 0)
        self.win_timer = 0
        self.switch_timer = 0
        self.level_timer = 25
        self.board_timer = 0
        self.missed = False
        self.check_moves = False
        self.will_play = None
        self.clock = pygame.time.Clock()
        self.oldticks = pygame.time.get_ticks()
        self.die = False
        self.level = level
        self.new_level()

    def go(self):
        while not self.die:
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
        if self.level < 8:
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
        return (x * theme.tile_size + 10, y * theme.tile_size + 10)

    def screen2board(self, coord):
        (x, y) = coord
        return ((x - 10) / theme.tile_size, (y - 10) / theme.tile_size)

    def draw_scene(self):
        background.fill((210, 200, 150))
        # Print timebar:
        x = theme.tile_size / 2
        y = screen_height * 18 / 20
        w = (self.board_width - 1) * theme.tile_size
        h = screen_height / 20
        w2 = w * self.time / 2000000
        if self.time <= 350000:
            color = (255, 0, 0)
        else:
            color = (255, 240, 0)
        pygame.draw.rect(background, (0, 0, 0), (x, y, w, h))
        if w2 > 0:
            pygame.draw.rect(background, color, (x, y, w * self.time / 2000000, h))
        # Draw pieces
        if self.level_timer:
            timer = self.level_timer
        elif self.board_timer:
            timer = self.board_timer
        else:
            timer = 0
        if timer > 25:
            xoff = 0
            yoff = (50 - timer) * (50 - timer)
        elif timer > 0:
            xoff = 0
            yoff = - timer * timer
        else:
            xoff = 0
            yoff = 0
        if self.switch_timer:
            (x1, y1) = self.board2screen(self.select)
            (x2, y2) = self.board2screen(self.switch)
            t = self.switch_timer * 1.0 / 5
        for (c, n) in self.board.items():
            # Decide the shape
            if n == 0:
                shape = theme.special[self.special_timer]
            elif c in self.surprised_list or self.board_timer > 25 or self.level_timer > 25:
                shape = theme.surprised[n - 1]
            elif c in self.disappear_list:
                shape = theme.exploded[n - 1]
            elif n == self.angry_tiles:
                shape = theme.angry[n - 1]
            else:
                shape = theme.normal[n - 1]
            # Decide the coordinates
            if c == self.switch and self.switch_timer:
                (x, y) = (x2 * t + x1 * (1 - t), y2 * t + y1 * (1 - t))
            elif c == self.select and self.switch_timer:
                (x, y) = (x1 * t + x2 * (1 - t), y1 * t + y2 * (1 - t))
            else:
                (x, y) = self.board2screen(c)
            if self.lost_timer:
                (xoff, yoff) = self.lost_offset[c]
                xoff += randint(0, 100 - self.lost_timer) - randint(0, 100 - self.lost_timer)
                yoff += randint(0, 100 - self.lost_timer) - randint(0, 100 - self.lost_timer)
                self.lost_offset[c] = (xoff, yoff)
            # Print the shit
            background.blit(shape, (x + xoff, y + yoff))
            # Remember the selector coordinates
            if c == self.select and not self.missed \
            or c == self.switch and self.missed:
                select_coord = (x, y)
        # Draw selector if necessary
        if self.select:
            background.blit(theme.selector, select_coord)
        # Print score
        font = pygame.font.Font(None, screen_height / 8)
        delta = 1 + screen_height / 200
        for x in range(2):
            text = font.render(str(self.score), 2, (x * 255, x * 255, x * 255))
            background.blit(text, (theme.tile_size * self.board_width + theme.tile_size / 2 - delta * x, 10 - delta * x))
        # Print new level stuff
        if self.level_timer and self.level_timer < 25:
            font = pygame.font.Font(None, screen_height / 4)
            delta = 1 + screen_height / 100
            for x in range(2):
                text = font.render('level ' + str(self.level), 2, (x * 255, x * 255, x * 255))
                (w, h) = text.get_rect().size
                background.blit(text, (theme.tile_size * self.board_width / 2 - w / 2 - delta * x, theme.tile_size * self.board_height / 2 - h / 2 - delta * x))
        # Print no more moves stuff
        if self.board_timer > 25:
            font = pygame.font.Font(None, screen_height / 6)
            delta = 1 + screen_height / 150
            for x in range(2):
                text = font.render('no more moves!', 2, (x * 255, x * 255, x * 255))
                (w, h) = text.get_rect().size
                background.blit(text, (theme.tile_size * self.board_width / 2 - w / 2 - delta * x, theme.tile_size * self.board_height / 2 - h / 2 - delta * x))
        # Print bonus:
        font = pygame.font.Font(None, theme.tile_size * 3 / 4)
        for b in self.bonus_list:
            for d in range(2):
                text = font.render(str(b[1]), 2, (d * 255, d * 255, d * 255))
                (x, y) = self.board2screen(b[0])
                background.blit(text, (x + theme.tile_size / 4 - delta * d, y + theme.tile_size / 4 - delta * d))
        # Print done/needed:
        delta = 1 + screen_height / 300
        x = theme.tile_size * self.board_width + theme.tile_size / 2
        y = theme.tile_size / 2 + screen_height / 8
        for i in range(self.population):
            background.blit(theme.tiny[i], (x, y))
            for d in range(2):
                text = font.render(str(self.done[i + 1]) + '/' + str(self.needed[i + 1]), 2, (d * 255, d * 255, d * 255))
                background.blit(text, (x + theme.tile_size * 5 / 4 - delta * d, y + screen_height / 64 - delta * d))
            y += screen_height / 12

    def iterate(self):
        ticks = pygame.time.get_ticks()
        delta = (ticks - self.oldticks) * 400 / (11.0000001 - self.level) # FIXME
        self.oldticks = ticks
        self.special_timer = (self.special_timer + 1) % self.population
        # Draw screen
        if self.check_moves:
            can_play = False
            for move in self.list_moves():
                can_play = True
                break
            self.check_moves = False
            if not can_play:
                self.board_timer = 50
        self.draw_scene()
        window.blit(background, (0, 0))
        # Draw stuff here
        pygame.display.flip()
        # Resolve winning moves and chain reactions
        if self.board_timer:
            self.board_timer -= 1
            if self.board_timer is 25:
                self.new_board()
            elif self.board_timer is 0:
                self.check_moves = True # Need to check again
            return
        if self.lost_timer:
            self.lost_timer -= 1
            if self.lost_timer is 0:
                self.die = True
            return
        if self.switch_timer:
            self.switch_timer -= 1
            if self.switch_timer is 0:
                self.do_move(self.select, self.switch)
                if self.missed:
                    self.missed = False
                else:
                    self.wins = self.get_wins()
                    if not self.wins:
                        self.missed = True
                        self.switch_timer = 5
                        return
                    self.win_iter = 0
                    self.win_timer = 12
                self.select = None
                self.switch = None
            return
        if self.level_timer:
            self.level_timer -= 1
            if self.level_timer is 25:
                self.level += 1
                self.new_level()
            elif self.level_timer is 0:
                self.check_moves = True
            return
        if self.win_timer:
            self.win_timer -= 1
            if self.win_timer is 10:
                for w in self.wins:
                    for (x, y) in w:
                        self.surprised_list.append((x, y))
            elif self.win_timer is 6:
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
            elif self.win_timer is 4:
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
            elif self.win_timer is 2:
                self.time += self.timebonus
                if self.time > 2000000:
                    self.time = 2000000
                self.score += self.scorebonus
                self.fill_board()
            elif self.win_timer is 0:
                self.wins = self.get_wins()
                if self.wins:
                    self.win_timer = 12
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
                        self.level_timer = 50
                    else:
                        self.check_moves = True
            return
        # Handle events
        played = None
        for event in pygame.event.get():
            if event.type == QUIT:
                self.die = True
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                self.die = True
                return
            elif event.type == KEYDOWN and event.key == K_f:
                pygame.display.toggle_fullscreen()
                return
            elif event.type == MOUSEBUTTONDOWN:
                (x2, y2) = self.screen2board(event.pos)
                if x2 < 0 or x2 >= self.board_width or y2 < 0 or y2 >= self.board_height:
                    continue
                played = (x2, y2)
                break
        if self.time <= 0:
            self.lost_timer = 100
            return
        # Update time
        self.time -= delta
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
                played = self.will_play[0]
            elif self.ai_timer is 0:
                played = self.will_play[1]
                self.will_play = None
            self.ai_timer -= 1
        # Handle plays
        if played and self.select:
            (x1, y1) = self.select
            (x2, y2) = played
            if x1 == x2 and y1 == y2:
                self.select = None
                return
            if abs(x1 - x2) + abs(y1 - y2) != 1:
                return
            self.switch = played
            self.switch_timer = 5
            return
        if played and not self.select:
            if self.board[played] != 0:
                self.select = played
                return
            # Deal with the special block
            self.wins = []
            target = 1 + self.special_timer
            found = 0
            for y in range(self.board_height):
                for x in range(self.board_width):
                    if self.board[(x, y)] == target:
                        self.wins.append([(x, y)])
            self.board[played] = target
            self.wins.append([played])
            self.win_iter = 0
            self.win_timer = 12
            return

# Init Pygame
pygame.init()
# Sound test
#pygame.mixer.get_init()
#sound = pygame.mixer.Sound('foo.wav')
#sound.play()
# Init display
window = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Alienkeeper')
background = pygame.Surface(window.get_size())
# Read commandline (haha)
level = 1
size = (8, 8)
# Go!
theme = Theme(file = join(dirname(argv[0]), 'tiles.png'))
game = Game(size = size, level = level)
game.go()

