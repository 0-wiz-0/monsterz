#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 Monsterz: cute puzzle game
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
from sys import argv, exit, platform
from os.path import join, dirname
from os import write

# String constants
VERSION = '0.4.2'
COPYRIGHT = 'MONSTERZ - COPYRIGHT 2005 SAM HOCEVAR - MONSTERZ IS ' \
            'FREE SOFTWARE, YOU CAN REDISTRIBUTE IT AND/OR MODIFY IT ' \
            'UNDER THE TERMS OF THE DO WHAT THE FUCK YOU WANT TO ' \
            'PUBLIC LICENSE, VERSION 2 - '

# Constants
HAVE_AI = False # broken

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
BOARD_WIDTH = 8
BOARD_HEIGHT = 8

STATUS_MENU = 0
STATUS_GAME = 1
STATUS_HELP = 2
STATUS_ABOUT = 3
STATUS_SCORES = 4
STATUS_QUIT = -1

LOST_DELAY = 40
SCROLL_DELAY = 40
WIN_DELAY = 12
SWITCH_DELAY = 4
WARNING_DELAY = 12

# Runtime flags
FLAG_FULLSCREEN = False
FLAG_MUSIC = True
FLAG_SFX = True

def compare_scores(x, y):
    if y[1] > x[1]:
        return 1
    elif y[1] < x[1]:
        return -1
    else:
        return y[2] - x[2]

def semi_grayscale(surf):
    try:
        # Convert to semi-grayscale
        pixels = pygame.surfarray.pixels3d(surf)
        alpha = pygame.surfarray.pixels_alpha(surf)
        for y, line in enumerate(pixels):
            for x, p in enumerate(line):
                r, g, b = p
                M = max(r, g, b)
                m = min(r, g, b)
                val = (r + g + b + 2 * M) / 5
                p[:] = (val + r) / 2, (val + g) / 2, (val + b) / 2
                if alpha[y][x] >= 250:
                    alpha[y][x] = 255 - (M - m) * 3 / 4
        del pixels
        del alpha
    except:
        return

def semi_transp(surf):
    try:
        # Convert to semi-transparency
        pixels = pygame.surfarray.pixels3d(surf)
        alpha = pygame.surfarray.pixels_alpha(surf)
        for y, line in enumerate(pixels):
            for x, p in enumerate(line):
                r, g, b = p
                M = max(r, g, b)
                m = min(r, g, b)
                p[:] = (m + r) / 2, (m + g) / 2, (m + b) / 2
                if alpha[y][x] >= 250:
                    alpha[y][x] = 255 - M * 2 / 3
        del pixels
        del alpha
    except:
        return

class Hiscores:
    def __init__(self, scorefile, outfd):
        self.scorefile = scorefile
        self.outfd = outfd
        self.scores = {}
        # Get username
        if platform == 'win32':
            try:
                from win32api import GetUserName
                self.name = GetUserName().upper()
            except:
                self.name = 'YOU'
        else:
            from pwd import getpwuid
            from os import geteuid
            self.name = getpwuid(geteuid())[0].upper()
        # Load current score file
        try:
            file = open(self.scorefile, 'r')
            lines = file.readlines()
            file.close()
            for l in [line.split(':') for line in lines]:
                if len(l) == 4:
                    self._addscore(l[0], l[1], int(l[2]), int(l[3]))
        except:
            pass
        # Add dummy scores to make sure our score list is full
        for game in ['CLASSIC']:
            if not self.scores.has_key(game):
                self.scores[game] = []
            for x in range(20): self._addscore(game, 'NOBODY', 0, 1)

    def _addscore(self, game, name, score, level):
        if not self.scores.has_key(game):
            self.scores[game] = []
        self.scores[game].append((name, score, level))
        self.scores[game].sort(compare_scores)
        self.scores[game] = self.scores[game][0:19]

    def add(self, game, score, level):
        self._addscore(game, self.name, score, level)
        # Immediately save
        msg = ''
        for type, list in self.scores.items():
            for name, score, level in list:
                msg += type + ':' + name + ':' + str(score) + ':' + str(level)
                msg += '\n'
        if self.outfd is not None:
            write(self.outfd, msg + '\n')
        else:
            try:
                file = open(self.scorefile, 'w')
                file.write(msg)
                file.close()
            except:
                pass # Cannot save scores, do nothing...

class Data:
    def __init__(self, dir):
        # Load stuff
        tiles = pygame.image.load(join(dir, 'tiles.png')).convert_alpha()
        w, h = tiles.get_rect().size
        self.tiles = tiles
        icon = pygame.image.load(join(dir, 'icon.png')).convert_alpha()
        pygame.display.set_icon(icon)
        self.background = pygame.image.load(join(dir, 'background.png')).convert()
        self.board = pygame.image.load(join(dir, 'board.png')).convert()
        self.logo = pygame.image.load(join(dir, 'logo.png')).convert_alpha()
        self.orig_size = w / 5
        self.tile_size = min((SCREEN_WIDTH - 20) / BOARD_WIDTH,
                             (SCREEN_HEIGHT - 20) * 17 / 20 / BOARD_HEIGHT)
        self.normal = [None] * 8
        self.blink = [None] * 8
        self.tiny = [None] * 8
        self.shaded = [None] * 8
        self.surprise = [None] * 8
        self.angry = [None] * 8
        self.exploded = [None] * 8
        self.special = [None] * 8
        self.selector = None
        # Load sound stuff
        if system.have_sound:
            self.wav = {}
            for s in ['click', 'grunt', 'ding', 'whip', 'pop', 'duh', \
                      'boing', 'applause', 'laugh', 'warning']:
                self.wav[s] = pygame.mixer.Sound(join(dir, s + '.wav'))
            pygame.mixer.music.load(join(dir, 'music.s3m'))
            pygame.mixer.music.set_volume(0.9)
            # Play immediately
            pygame.mixer.music.play(-1, 0.0)
            if not FLAG_MUSIC:
                pygame.mixer.music.pause()
        # Initialise tiles stuff
        t = self.tile_size
        s = self.orig_size
        scale = self._scale
        tile_at = lambda x, y: self.tiles.subsurface((x * s, y * s, s, s))
        # Create sprites
        for i in range(8):
            self.normal[i] = scale(tile_at(0, i + 2), (t, t))
            self.tiny[i] = scale(tile_at(0, i + 2), (t * 3 / 4, t * 3 / 4))
            self.shaded[i] = scale(tile_at(3, i + 2), (t * 3 / 4, t * 3 / 4))
            semi_grayscale(self.shaded[i])
            self.blink[i] = scale(tile_at(1, i + 2), (t, t))
            self.surprise[i] = scale(tile_at(2, i + 2), (t, t))
            self.angry[i] = scale(tile_at(3, i + 2), (t, t))
            self.exploded[i] = scale(tile_at(4, i + 2), (t, t))
            #tmp = tile_at(1, 0).copy() # marche pas !
            tmp = scale(tile_at(1, 0), (t, t)) # marche...
            mini = tile_at(0, i + 2)
            mini = scale(mini, (t * 7 / 8 - 1, t * 7 / 8 - 1))
            tmp.blit(mini, (s / 16, s / 16))
            self.special[i] = scale(tmp, (t, t))
        self.led_off = scale(self.tiles.subsurface((3 * s, 0, s / 2, s / 2)), (t / 2, t / 2))
        self.led_on = scale(self.tiles.subsurface((3 * s + s / 2, 0, s / 2, s / 2)), (t / 2, t / 2))
        self.eye = scale(tile_at(2, 0), (t * 3 / 4, t * 3 / 4))
        self.shadeye = scale(tile_at(2, 0), (t * 3 / 4, t * 3 / 4))
        semi_transp(self.shadeye)
        self.arrow = tile_at(4, 0)
        self.selector = scale(tile_at(0, 0), (t, t))

    def _scale(self, surf, size):
        w, h = surf.get_size()
        if (w, h) == size:
            return pygame.transform.scale(surf, size)
        return pygame.transform.rotozoom(surf, 0.0, 1.0 * size[0] / w)

    def board2screen(self, coord):
        x, y = coord
        return (x * data.tile_size + 24, y * data.tile_size + 24)

    def screen2board(self, coord):
        x, y = coord
        return ((x - 24) / data.tile_size, (y - 24) / data.tile_size)

class System:
    def __init__(self):
        if FLAG_FULLSCREEN:
            f = pygame.FULLSCREEN
        else:
            f = 0
        pygame.init()
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), f)
        self.background = pygame.Surface(self.window.get_size())
        try:
            self.have_sound = pygame.mixer.get_init()
        except:
            self.have_sound = False
        pygame.display.set_caption('Monsterz')

    def blit(self, surf, coords):
        self.background.blit(surf, coords)

    def blit_board(self, (x1, y1, x2, y2)):
        x1, y1 = x1 * 48, y1 * 48
        x2, y2 = x2 * 48 - x1, y2 * 48 - y1
        surf = data.board.subsurface((x1, y1, x2, y2))
        self.background.blit(surf, (x1 + 24, y1 + 24))

    def flip(self):
        self.window.blit(self.background, (0, 0))
        pygame.display.flip()

    def play(self, sound):
        if self.have_sound and FLAG_SFX: data.wav[sound].play()

    def toggle_fullscreen(self):
        global FLAG_FULLSCREEN
        self.play('whip')
        FLAG_FULLSCREEN = not FLAG_FULLSCREEN
        pygame.display.toggle_fullscreen()

    def toggle_sfx(self):
        global FLAG_SFX
        self.play('whip')
        FLAG_SFX = not FLAG_SFX
        self.play('whip')

    def toggle_music(self):
        global FLAG_MUSIC
        self.play('whip')
        if FLAG_MUSIC:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
        FLAG_MUSIC = not FLAG_MUSIC

class Fonter:
    def __init__(self, size = 48):
        # Keep 48 items in our cache, we need 31 for the high scores
        self.cache = []
        self.size = size

    def render(self, msg, size, color = (255, 255, 255)):
        for i, (m, s, c, t) in enumerate(self.cache):
            if s == size and m == msg and c == color:
                del self.cache[i]
                self.cache.append((m, s, c, t))
                return t
        font = pygame.font.Font(None, size * 2)
        delta = 2 + size / 8
        black = font.render(msg, 2, (0, 0, 0))
        w, h = black.get_size()
        text = pygame.Surface((w + delta, h + delta)).convert_alpha()
        text.fill((0, 0, 0, 0))
        for x, y in [(5, 5), (6, 3), (5, 1), (3, 0),
                     (1, 1), (0, 3), (1, 5), (3, 6)]:
            text.blit(black, (x * delta / 6, y * delta / 6))
        white = font.render(msg, 2, color)
        text.blit(white, (delta / 2, delta / 2))
        text = pygame.transform.rotozoom(text, 0.0, 0.5)
        self.cache.append((msg, size, color, text))
        if len(self.cache) > self.size:
            self.cache.pop(0)
        return text

class Game:
    # Nothing here yet
    def __init__(self):
        self.needed = [0] * 9
        self.done = [0] * 9
        self.bonus_list = []
        self.blink_list = {}
        self.disappear_list = []
        self.surprised_list = []
        self.clicks = []
        self.select = None
        self.switch = None
        self.score = 0
        self.lost_timer = 0
        self.extra_offset = [[(0, 0)] * BOARD_WIDTH for x in range(BOARD_HEIGHT)]
        self.win_timer = 0
        self.warning_timer = 0
        self.switch_timer = 0
        self.level_timer = SCROLL_DELAY / 2
        self.board_timer = 0
        self.missed = False
        self.check_moves = False
        self.will_play = None
        self.paused = False
        self.pause_bitmap = None
        self.play_again = False
        self.eyes = 3
        self.show_move = False
        self.level = 1
        self.new_level()
        self.oldticks = pygame.time.get_ticks()

    def get_random(self, no_special = False):
        if not no_special and randint(0, 500) == 0:
            return 0
        return randint(1, self.population)

    def new_board(self):
        self.board = {}
        for y in range(BOARD_HEIGHT):
            while True:
                for x in range(BOARD_WIDTH):
                    self.board[(x, y)] = self.get_random()
                if not self.get_wins(): break

    def fill_board(self):
        for y in xrange(BOARD_HEIGHT - 1, -1, -1):
            for x in xrange(BOARD_WIDTH - 1, -1, -1):
                if self.board.has_key((x, y)):
                    continue
                for y2 in xrange(y - 1, -1, -1):
                    if self.board.has_key((x, y2)):
                        self.board[(x, y)] = self.board[(x, y2)]
                        self.extra_offset[x][y] = (0, 48 * (y2 - y))
                        del self.board[(x, y2)]
                        break
                else:
                    self.board[(x, y)] = self.get_random()
                    self.extra_offset[x][y] = ((0, 48 * (-2 - y)))

    def get_wins(self):
        wins = []
        # Horizontal
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH - 2):
                a = self.board.get((x, y))
                if a is None or a == 0: continue
                b = self.board.get((x - 1, y))
                if b and a == b: continue
                len = 1
                for t in range(1, BOARD_WIDTH - x):
                    b = self.board.get((x + t, y))
                    if a != b: break
                    len += 1
                if len < 3: continue
                win = []
                for t in range(len):
                    win.append((x + t, y))
                wins.append(win)
        # Horizontal
        for x in range(BOARD_WIDTH):
            for y in range(BOARD_HEIGHT - 2):
                a = self.board.get((x, y))
                if a is None or a == 0: continue
                b = self.board.get((x, y - 1))
                if b and a == b: continue
                len = 1
                for t in range(1, BOARD_HEIGHT - y):
                    b = self.board.get((x, y + t))
                    if a != b: break
                    len += 1
                if len < 3: continue
                win = []
                for t in range(len):
                    win.append((x, y + t))
                wins.append(win)
        return wins

    def list_moves(self):
        checkme = [[(+2,  0), (+3,  0)],
                   [(+1, -1), (+1, -2)],
                   [(+1, -1), (+1, +1)],
                   [(+1, +1), (+1, +2)]]
        delta = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                a = self.board.get((x, y))
                if a == 0:
                   continue # We don’t want no special piece
                for [(a1, b1), (a2, b2)] in checkme:
                    for dx, dy in delta:
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
            if self.level < 10:
                self.needed[i + 1] = self.level + 2
            else:
                self.needed[i + 1] = 0 # level 10 is the highest
        self.angry_tiles = -1
        self.new_board()
        self.time = 1000000

    def board_draw(self):
        # Draw checkered board
        system.blit(data.board, (24, 24))
        # Have a random piece blink
        c = randint(0, BOARD_WIDTH - 1), randint(0, BOARD_HEIGHT - 1)
        if randint(0, 5) is 0 and not self.blink_list.has_key(c):
            self.blink_list[c] = 5
        # Handle special scrolling cases
        if self.level_timer:
            timer = self.level_timer
        elif self.board_timer:
            timer = self.board_timer
        else:
            timer = 0
        if timer > SCROLL_DELAY / 2:
            global_xoff = 0
            yoff = (SCROLL_DELAY - timer) * (SCROLL_DELAY - timer)
            global_yoff = yoff * 50 * 50 / SCROLL_DELAY / SCROLL_DELAY
        elif timer > 0:
            global_xoff = 0
            yoff = - timer * timer
            global_yoff = yoff * 50 * 50 / SCROLL_DELAY / SCROLL_DELAY
        else:
            global_xoff = 0
            global_yoff = 0
        if self.switch_timer:
            x1, y1 = data.board2screen(self.select)
            x2, y2 = data.board2screen(self.switch)
            t = self.switch_timer * 1.0 / SWITCH_DELAY
        for c, n in self.board.items():
            # Decide the coordinates
            if c == self.switch and self.switch_timer:
                x, y = x2 * t + x1 * (1 - t), y2 * t + y1 * (1 - t)
            elif c == self.select and self.switch_timer:
                x, y = x1 * t + x2 * (1 - t), y1 * t + y2 * (1 - t)
            else:
                x, y = data.board2screen(c)
            i, j = c
            xoff, yoff = self.extra_offset[i][j]
            if self.lost_timer:
                d = LOST_DELAY - self.lost_timer
                xoff += (randint(0, d) - randint(0, d)) * randint(0, d) / 4
                yoff += (randint(0, d) - randint(0, d)) * randint(0, d) / 4
                self.extra_offset[i][j] = xoff, yoff
            elif yoff and self.win_timer:
                yoff = yoff * (self.win_timer - 1) / (WIN_DELAY * 2 / 3)
                self.extra_offset[i][j] = xoff, yoff
            xoff += global_xoff
            yoff += global_yoff
            # Decide the shape
            if n == 0:
                shape = data.special[monsterz.timer % self.population]
            elif self.level_timer and self.level_timer < SCROLL_DELAY / 2:
                shape = data.blink[n - 1]
            elif c in self.surprised_list \
              or self.board_timer > SCROLL_DELAY / 2 \
              or self.level_timer > SCROLL_DELAY / 2:
                shape = data.surprise[n - 1]
            elif c in self.disappear_list:
                shape = data.exploded[n - 1]
            elif n == self.angry_tiles:
                shape = data.angry[n - 1]
            elif self.blink_list.has_key(c):
                shape = data.blink[n - 1]
                self.blink_list[c] -= 1
                if self.blink_list[c] is 0: del self.blink_list[c]
            else:
                shape = data.normal[n - 1]
            # Remember the selector coordinates
            if c == self.select and not self.missed \
            or c == self.switch and self.missed:
                select_coord = (x, y)
                shape = data.blink[n - 1] # Not sure if it looks nice
            # Print the shit
            self.piece_draw(shape, (x + xoff, y + yoff))
        # Draw selector if necessary
        if self.select:
            system.blit(data.selector, select_coord)

    def piece_draw(self, sprite, (x, y)):
        width = data.tile_size
        crop = sprite.subsurface
        # Constrain X
        if x < 10 - data.tile_size or x > 24 + 8 * data.tile_size + 14:
            return
        elif x < 10:
            delta = 10 - x
            sprite = crop((delta, 0, data.tile_size - delta, data.tile_size))
            crop = sprite.subsurface
            x += delta
            width -= delta
        elif x > 24 + 7 * data.tile_size + 14:
            delta = x - 24 - 7 * data.tile_size - 14
            sprite = crop((0, 0, data.tile_size - delta, data.tile_size))
            crop = sprite.subsurface
            width -= delta
        # Constrain Y
        if y < 10 - data.tile_size or y > 24 + 8 * data.tile_size + 14:
            return
        elif y < 10:
            delta = 10 - y
            sprite = crop((0, delta, width, data.tile_size - delta))
            y += delta
        elif y > 24 + 7 * data.tile_size + 14:
            delta = y - 24 - 7 * data.tile_size - 14
            sprite = crop((0, 0, width, data.tile_size - delta))
        system.blit(sprite, (x, y))

    psat = [0] * 2
    parea = None
    def game_draw(self):
        # Draw timebar
        timebar = pygame.Surface((406, 32)).convert_alpha()
        timebar.fill((0, 0, 0, 155))
        w = 406 * self.time / 2000000
        if w > 0:
            if self.warning_timer:
                ratio = 1.0 * abs(2 * self.warning_timer - WARNING_DELAY) \
                            / WARNING_DELAY
                c = (200 * ratio, 0, 0, 155)
            elif self.time <= 350000:
                c = (200, 0, 0, 155)
            elif self.time <= 700000:
                ratio = 1.0 * (self.time - 350000) / 350000
                c = (200, 180 * ratio, 0, 155)
            elif self.time <= 1000000:
                ratio = 1.0 * (1000000 - self.time) / 300000
                c = (200 * ratio, 200 - 20 * ratio, 0, 155)
            else:
                c = (0, 200, 0, 155)
            pygame.draw.rect(timebar, c, (0, 0, w, 32))
        try:
            alpha = pygame.surfarray.pixels_alpha(timebar)
            for x in range(4):
                for y, p in enumerate(alpha[x]):
                    alpha[x][y] = p * x / 4
                for y, p in enumerate(alpha[406 - x - 1]):
                    alpha[406 - x - 1][y] = p * x / 4
            for col in alpha:
                l = len(col)
                for y in range(4):
                    col[y] = col[y] * y / 4
                    col[l - y - 1] = col[l - y - 1] * y / 4
                del col
            del alpha
        except:
            pass
        system.blit(timebar, (13, 436))
        # Draw pieces
        if self.paused:
            system.blit(self.pause_bitmap, (72, 24))
            text = fonter.render('PAUSED', 120)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w / 2, 24 + 336 - h / 2))
        elif self.lost_timer >= 0:
            self.board_draw()
        # Print play again message
        if self.lost_timer < 0:
            text = fonter.render('GAME OVER', 80)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
            if self.score < 5000:
                msg = 'YUO = TEH L0SER'
            elif self.score < 15000:
                msg = 'WELL, AT LEAST YOU TRIED'
            elif self.score < 30000:
                msg = 'W00T! YUO IS TEH R0X0R'
            else:
                msg = 'ZOMFG!!!111!!! YUO PWND!!!%$#@%@#'
            text = fonter.render(msg, 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w / 2, 24 + 240 - h / 2))
        # Print new level stuff
        if self.level_timer > SCROLL_DELAY / 2:
            text = fonter.render('LEVEL UP!', 80)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # When no more moves are possible
        if self.board_timer > SCROLL_DELAY / 2:
            text = fonter.render('NO MORE MOVES!', 60)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # Print bonus
        for b in self.bonus_list:
            text = fonter.render(str(b[1]), 36)
            w, h = text.get_rect().size
            x, y = data.board2screen(b[0])
            system.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        # Print hint arrow
        if self.show_move:
            lookup = [0, 1, 5, 16, 27, 31, 32, 31, 27, 16, 5, 1]
            for (src, dst) in self.list_moves():
                x1, y1 = data.board2screen(src)
                x2, y2 = data.board2screen(dst)
                delta = lookup[monsterz.timer % 12]
                x = -32 + (x1 * delta + x2 * (32 - delta)) / 32
                y = 32 + (y1 * delta + y2 * (32 - delta)) / 32
                system.blit(data.arrow, (x, y))
                break # Only show one move
        # Print score
        text = fonter.render(str(self.score), 60)
        w, h = text.get_rect().size
        system.blit(text, (624 - w, 10))
        # Print done/needed
        for i in range(self.population):
            if self.done[i + 1] >= self.needed[i + 1]:
                surf = data.tiny[i]
            else:
                surf = data.shaded[i]
            x = 440 + i / 4 * 90
            y = 64 + (i % 4) * 38
            system.blit(surf, (x, y))
            text = fonter.render(str(self.done[i + 1]), 36)
            system.blit(text, (x + 44, y + 2))
        # Print eyes
        for i in range(3):
            x, y = 440 + 36 * i, 252
            if(i < self.eyes):
                system.blit(data.eye, (x, y))
            else:
                system.blit(data.shadeye, (x, y))
        # Print pause and abort buttons
        if self.lost_timer >= 0:
            r = (255, 127, 127)
            if self.paused:
                led, color = data.led_on, (255, 255, 255)
            else:
                led, color = data.led_off, (180, 150, 127)
            c = map(lambda a, b: b - (b - a) * self.psat[0] / 255, r, color)
            system.blit(led, (440, 298))
            system.blit(fonter.render('PAUSE', 30, c), (470, 296))
            color = (180, 150, 127)
            c = map(lambda a, b: b - (b - a) * self.psat[1] / 255, r, color)
            system.blit(fonter.render('ABORT', 30, c), (470, 326))
            for x in range(2):
                if self.psat[x]:
                    self.psat[x] = self.psat[x] * 8 / 10
        # Print level
        msg = 'LEVEL ' + str(self.level)
        if self.needed[1]: msg += ': ' + str(self.needed[1]) + 'x'
        text = fonter.render(msg, 40)
        system.blit(text, (444, 216))

    def pause(self):
        # TODO: prevent cheating by not allowing less than 1 second
        # since the last pause
        self.paused = not self.paused
        system.play('whip')
        if self.paused:
            self.pause_bitmap = pygame.transform.scale(data.normal[self.get_random(no_special = True) - 1], (6 * data.tile_size, 6 * data.tile_size))
            #self.pause_bitmap = pygame.transform.rotozoom(data.normal[self.get_random(no_special = True) - 1], 0.0, 6.0)
        else:
            del self.pause_bitmap
        self.clicks = []

    def update(self):
        ticks = pygame.time.get_ticks()
        delta = (ticks - self.oldticks) * 450 / (12 - self.level)
        self.oldticks = ticks
        # If paused, do nothing
        if self.paused:
            return
        # Resolve winning moves and chain reactions
        if self.board_timer:
            self.board_timer -= 1
            if self.board_timer is SCROLL_DELAY / 2:
                self.new_board()
            elif self.board_timer is 0:
                system.play('boing')
                self.check_moves = True # Need to check again
            return
        if self.lost_timer:
            self.lost_timer -= 1
            if self.lost_timer is 0:
                hiscores.add('CLASSIC', self.score, self.level)
                self.lost = True
                self.lost_timer = -1 # Continue forever
            return
        if self.switch_timer:
            self.switch_timer -= 1
            if self.switch_timer is 0:
                self.board[self.select], self.board[self.switch] = \
                    self.board[self.switch], self.board[self.select]
                if self.missed:
                    self.clicks = []
                    self.missed = False
                else:
                    self.wins = self.get_wins()
                    if not self.wins:
                        system.play('whip')
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
                system.play('boing')
                self.blink_list = {}
                self.check_moves = True
            return
        if self.win_timer:
            self.win_timer -= 1
            if self.win_timer is WIN_DELAY - 1:
                system.play('duh')
                for w in self.wins:
                    for x, y in w:
                        self.surprised_list.append((x, y))
            elif self.win_timer is WIN_DELAY * 4 / 5:
                system.play('pop')
                self.scorebonus = 0
                self.timebonus = 0
                for w in self.wins:
                    if len(w) is 1:
                        points = 10 * self.level
                    else:
                        points = (10 * self.level) * (2 ** (self.win_iter + len(w) - 3))
                    self.scorebonus += points
                    self.timebonus += 45000 * len(w)
                    x2, y2 = 0.0, 0.0
                    for x, y in w:
                        x2 += x
                        y2 += y
                    self.bonus_list.append([(x2 / len(w), y2 / len(w)), points])
                self.disappear_list = self.surprised_list
                self.surprised_list = []
            elif self.win_timer is WIN_DELAY * 3 / 5:
                for x, y in self.disappear_list:
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
                        system.play('grunt')
                        self.angry_tiles = angry
                self.disappear_list = []
                self.bonus_list = []
            elif self.win_timer is WIN_DELAY * 2 / 5:
                self.time += self.timebonus
                if self.time > 2000000:
                    self.time = 2000000
                # Get a new eye each 10000 points, but no more than 3
                if (self.score % 10000) + self.scorebonus >= 10000 \
                  and self.eyes < 3:
                    self.eyes += 1
                self.score += self.scorebonus
                self.fill_board()
            elif self.win_timer is 0:
                system.play('boing')
                self.wins = self.get_wins()
                if self.wins:
                    self.win_timer = WIN_DELAY
                    self.win_iter += 1
                elif self.needed[1]:
                    # Check for new level
                    for i in range(self.population):
                        if self.done[i + 1] < self.needed[i + 1]:
                            self.check_moves = True
                            break
                    else:
                        system.play('applause')
                        self.select = None
                        self.level_timer = SCROLL_DELAY
                else:
                    self.check_moves = True
            return
        if self.show_move and (monsterz.timer % 6) == 0:
            system.play('click')
        if self.warning_timer:
            self.warning_timer -= 1
        elif self.time <= 200000:
            system.play('warning')
            self.warning_timer = WARNING_DELAY
        # Update time
        self.time -= delta
        if self.time <= 0:
            system.play('laugh')
            self.select = None
            self.show_move = False
            self.lost_timer = LOST_DELAY
            return
        # Handle moves from the AI:
        if HAVE_AI:
            if not self.will_play:
                self.will_play = None
                # Special piece?
                if randint(0, 3) == 0:
                    special = None
                    for y in range(BOARD_HEIGHT):
                        for x in range(BOARD_WIDTH):
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
            if played == (99, 99):
                system.play('whip')
                self.select = None
                self.eyes -= 1
                # show_move is removed when we click, or when we lose
                self.show_move = True
                return
            self.show_move = False
            if self.select:
                if self.select == played:
                    system.play('click')
                    self.select = None
                    return
                x1, y1 = self.select
                x2, y2 = played
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    return
                system.play('whip')
                self.switch = played
                self.switch_timer = SWITCH_DELAY
            else:
                if self.board[played] != 0:
                    system.play('click')
                    self.select = played
                    return
                # Deal with the special block
                self.wins = []
                target = 1 + (monsterz.timer % self.population)
                found = 0
                for y in range(BOARD_HEIGHT):
                    for x in range(BOARD_WIDTH):
                        if self.board[(x, y)] == target:
                            self.wins.append([(x, y)])
                self.board[played] = target
                self.wins.append([played])
                self.win_iter = 0
                self.win_timer = WIN_DELAY
            return

class Monsterz:
    def __init__(self):
        # Init values
        self.status = STATUS_MENU
        self.clock = pygame.time.Clock()
        self.timer = 0

    def go(self):
        while True:
            if self.status == STATUS_MENU:
                self.marea = None
                iterator = self.iterate_menu
            elif self.status == STATUS_GAME:
                self.game = Game()
                iterator = self.iterate_game
            elif self.status == STATUS_HELP:
                self.page = 1
                iterator = self.iterate_help
            elif self.status == STATUS_SCORES:
                iterator = self.iterate_scores
            elif self.status == STATUS_QUIT:
                break
            self.status = None
            iterator()
            system.flip()
            self.timer += 1
            self.clock.tick(12)
        # Close the display, but give time to hear the last sample
        pygame.display.quit()
        self.clock.tick(2)

    def copyright_draw(self):
        scroll = pygame.Surface((406, 40)).convert_alpha()
        scroll.fill((0, 0, 0, 0))
        # This very big text surface will be cached by the font system
        text = fonter.render(COPYRIGHT, 30)
        w, h = text.get_size()
        d = (self.timer * 2) % w
        scroll.blit(text, (0 - d, 0))
        scroll.blit(text, (w - d, 0))
        try:
            alpha = pygame.surfarray.pixels_alpha(scroll)
            for x in range(10):
                for y, p in enumerate(alpha[x]):
                    alpha[x][y] = p * x / 12
                for y, p in enumerate(alpha[406 - x - 1]):
                    alpha[406 - x - 1][y] = p * x / 12
            del alpha
        except:
            pass
        system.blit(scroll, (13, 437))

    gsat = [0] * 3
    garea = None
    def generic_draw(self):
        x, y = pygame.mouse.get_pos()
        garea = None
        if system.have_sound:
            if 440 < x < 440 + 180 and 378 < y < 378 + 24:
                garea = 1
                self.gsat[0] = 255
            elif 440 < x < 440 + 180 and 408 < y < 408 + 24:
                garea = 2
                self.gsat[1] = 255
        if 440 < x < 440 + 180 and 438 < y < 438 + 24:
            garea = 3
            self.gsat[2] = 255
        if garea and garea != self.garea:
            system.play('click')
        self.garea = garea
        system.blit(data.background, (0, 0))
        # Print various buttons
        r = (255, 127, 127)
        if system.have_sound:
            if FLAG_SFX:
                led, color = data.led_on, (255, 255, 255)
            else:
                led, color = data.led_off, (180, 150, 127)
            c = map(lambda a, b: b - (b - a) * self.gsat[0] / 255, r, color)
            system.blit(led, (440, 378))
            system.blit(fonter.render('SOUND FX', 30, c), (470, 376))
            if FLAG_MUSIC:
                led, color = data.led_on, (255, 255, 255)
            else:
                led, color = data.led_off, (180, 150, 127)
            c = map(lambda a, b: b - (b - a) * self.gsat[1] / 255, r, color)
            system.blit(led, (440, 408))
            system.blit(fonter.render('MUSIC', 30, c), (470, 406))
        if FLAG_FULLSCREEN:
            led, color = data.led_on, (255, 255, 255)
        else:
            led, color = data.led_off, (180, 150, 127)
        c = map(lambda a, b: b - (b - a) * self.gsat[2] / 255, r, color)
        system.blit(led, (440, 438))
        system.blit(fonter.render('FULLSCREEN', 30, c), (470, 436))
        for x in range(3):
            if self.gsat[x]:
                self.gsat[x] = self.gsat[x] * 8 / 10

    def generic_event(self, event):
        if event.type == QUIT:
            self.status = STATUS_QUIT
            return True
        elif event.type == KEYDOWN and event.key == K_f:
            system.toggle_fullscreen()
            return True
        if system.have_sound:
            if event.type == KEYDOWN and event.key == K_s:
                system.toggle_sfx()
                return True
            elif event.type == KEYDOWN and event.key == K_m:
                system.toggle_music()
                return True
        if event.type == MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if system.have_sound:
                if 440 < x < 440 + 180 and 378 < y < 378 + 24:
                    system.toggle_sfx()
                    return True
                elif 440 < x < 440 + 180 and 408 < y < 408 + 24:
                    system.toggle_music()
                    return True
            if 440 < x < 440 + 180 and 438 < y < 438 + 24:
                system.toggle_fullscreen()
                return True
        return False

    msat = [0] * 4
    marea = None
    def iterate_menu(self):
        self.generic_draw()
        self.copyright_draw()
        colors = [[0, 255, 0], [255, 0, 255], [255, 255, 0], [255, 0, 0]]
        shapes = [2, 3, 4, 0]
        messages = ['NEW GAME', 'HELP', 'SCORES', 'QUIT']
        x, y = data.screen2board(pygame.mouse.get_pos())
        if y == 4 and 1 <= x <= 6:
            marea = STATUS_GAME
            self.msat[0] = 255
        elif y == 5 and 1 <= x <= 4:
            marea = STATUS_HELP
            self.msat[1] = 255
        elif y == 6 and 1 <= x <= 5:
            marea = STATUS_SCORES
            self.msat[2] = 255
        elif y == 7 and 1 <= x <= 4:
            marea = STATUS_QUIT
            self.msat[3] = 255
        else:
            marea = None
        if marea and marea != self.marea:
            system.play('click')
        self.marea = marea
        # Print logo and menu
        w, h = data.logo.get_size()
        system.blit(data.logo, (24 + 192 - w / 2, 24 + 96 - h / 2))
        for x in range(4):
            if self.msat[x] > 180:
                monster = data.surprise[shapes[x]]
            elif self.msat[x] > 40:
                monster = data.normal[shapes[x]]
            else:
                monster = data.blink[shapes[x]]
            system.blit(monster, data.board2screen((1, 4 + x)))
            c = map(lambda a: 255 - (255 - a) * self.msat[x] / 255, colors[x])
            text = fonter.render(messages[x], 48, c)
            w, h = text.get_rect().size
            system.blit(text, (24 + 102, 24 + 216 + 48 * x - h / 2))
            if self.msat[x]:
                self.msat[x] = self.msat[x] * 8 / 10
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                system.play('whip')
                self.status = STATUS_QUIT
                return
            elif event.type == KEYDOWN and event.key == K_n:
                system.play('whip')
                self.status = STATUS_GAMES
                return
            elif event.type == KEYDOWN and event.key == K_h:
                system.play('whip')
                self.status = STATUS_HELP
                return
            elif event.type == KEYDOWN and event.key == K_q:
                system.play('whip')
                self.status = STATUS_QUIT
                return
            elif event.type == MOUSEBUTTONDOWN and marea:
                system.play('whip')
                self.status = marea
                return

    def iterate_game(self):
        x, y = pygame.mouse.get_pos()
        parea = None
        if self.game.lost_timer >= 0:
            if 440 < x < 440 + 180 and 298 < y < 298 + 24:
                parea = 1
                self.game.psat[0] = 255
            elif 440 < x < 440 + 180 and 328 < y < 328 + 24:
                parea = 2
                self.game.psat[1] = 255
        if parea and parea != self.game.parea:
            system.play('click')
        self.game.parea = parea
        # Draw screen
        self.generic_draw()
        if self.game.check_moves:
            for move in self.game.list_moves():
                break
            else:
                system.play('ding')
                self.game.board_timer = SCROLL_DELAY
            self.game.check_moves = False
            self.game.clicks = []
        self.game.game_draw()
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                # FIXME: remove board nicely, add score to hiscore list
                system.play('whip')
                self.status = STATUS_MENU
                return
            elif event.type == KEYDOWN and (event.key == K_p or event.key == K_SPACE) and self.game.lost_timer >= 0:
                self.game.pause()
            elif event.type == MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if 440 < x < 440 + 180 and 298 < y < 298 + 24:
                    system.play('whip')
                    self.game.pause()
                    return
                elif 440 < x < 440 + 180 and 328 < y < 328 + 24:
                    system.play('whip')
                    self.status = STATUS_MENU
                    return
                if self.game.lost_timer < 0:
                    self.status = STATUS_MENU
                    return
                if 440 < x < 440 + 36 * 3 and 252 < y < 252 + 36:
                    if self.game.eyes >= 1 and not self.game.show_move:
                        self.game.clicks.append((99, 99))
                    return
                x, y = data.screen2board(event.pos)
                if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT:
                    continue
                self.game.clicks.append((x, y))
        self.game.update()

    page = 1
    def iterate_help(self):
        self.generic_draw()
        self.copyright_draw()
        # Title
        text = fonter.render('INSTRUCTIONS (' + str(self.page) + ')', 60)
        w, h = text.get_rect().size
        system.blit(text, (24 + 192 - w / 2, 24 + 24 - h / 2))
        if self.page == 1:
            # Explanation 1
            text = fonter.render('SWAP ADJACENT MONSTERS TO CREATE', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h / 2))
            text = fonter.render('ALIGNMENTS OF THREE OR MORE. NEW', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h / 2))
            text = fonter.render('MONSTERS WILL FILL THE HOLES.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h / 2))
            # Iter 1
            system.blit_board((0, 3, 2, 7))
            system.blit(data.normal[2], data.board2screen((0, 3)))
            system.blit(data.normal[5], data.board2screen((0, 4)))
            system.blit(data.blink[0], data.board2screen((0, 5)))
            system.blit(data.normal[3], data.board2screen((0, 6)))
            system.blit(data.normal[0], data.board2screen((1, 3)))
            system.blit(data.normal[0], data.board2screen((1, 4)))
            system.blit(data.normal[4], data.board2screen((1, 5)))
            system.blit(data.normal[6], data.board2screen((1, 6)))
            system.blit(data.selector, data.board2screen((0, 5)))
            # Iter 2
            system.blit_board((3, 3, 5, 7))
            system.blit(data.normal[2], data.board2screen((3, 3)))
            system.blit(data.normal[5], data.board2screen((3, 4)))
            system.blit(data.normal[4], data.board2screen((3, 5)))
            system.blit(data.normal[3], data.board2screen((3, 6)))
            system.blit(data.surprise[0], data.board2screen((4, 3)))
            system.blit(data.surprise[0], data.board2screen((4, 4)))
            system.blit(data.surprise[0], data.board2screen((4, 5)))
            system.blit(data.normal[6], data.board2screen((4, 6)))
            system.blit(data.selector, data.board2screen((4, 5)))
            # Iter 2
            system.blit_board((6, 3, 8, 7))
            system.blit(data.normal[2], data.board2screen((6, 3)))
            system.blit(data.normal[5], data.board2screen((6, 4)))
            system.blit(data.normal[4], data.board2screen((6, 5)))
            system.blit(data.normal[3], data.board2screen((6, 6)))
            system.blit(data.exploded[0], data.board2screen((7, 3)))
            system.blit(data.exploded[0], data.board2screen((7, 4)))
            system.blit(data.exploded[0], data.board2screen((7, 5)))
            system.blit(data.normal[6], data.board2screen((7, 6)))
            # Bonus
            text = fonter.render('10', 36)
            w, h = text.get_rect().size
            x, y = data.board2screen((7, 4))
            system.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
            # Explanation 2
            text = fonter.render('CREATE CHAIN REACTIONS TO GET TWICE', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 348 - h / 2))
            text = fonter.render('AS MANY POINTS, THEN 4x, 8x ETC.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 372 - h / 2))
        elif self.page == 2:
            # Explanation 1
            text = fonter.render('YOU CAN ALWAYS PERFORM A VALID MOVE.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h / 2))
            text = fonter.render('WHEN NO MORE MOVES ARE POSSIBLE, YOU', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h / 2))
            text = fonter.render('GET A COMPLETE NEW BOARD.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h / 2))
            # Surprised
            system.blit_board((0, 3, 8, 5))
            for x in range(8):
                system.blit(data.surprise[(x * 3 + 2) % 8], data.board2screen((x, 3)))
                system.blit(data.surprise[(x * 7) % 8], data.board2screen((x, 4)))
            text = fonter.render('NO MORE MOVES!', 60)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
            # Explanation 2
            text = fonter.render('USE THE EYE TO FIND WHERE TO PLAY.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6 + 48, 24 + 300 - h / 2))
            text = fonter.render('EACH 10,000 POINTS YOU GET A NEW', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6 + 48, 24 + 324 - h / 2))
            text = fonter.render('EYE. YOU CAN\'T HAVE MORE THAN 3.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6 + 48, 24 + 348 - h / 2))
            system.blit(data.eye, (24 + 6, 24 + 306))
        elif self.page == 3:
            # Explanation 1
            text = fonter.render('WHEN ONLY ONE KIND OF MONSTER IS', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h / 2))
            text = fonter.render('NEEDED TO FINISH THE LEVEL, MONSTERS', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h / 2))
            text = fonter.render('OF THAT KIND GET AN ANGRY FACE.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h / 2))
            # Print done/needed
            system.blit_board((0, 3, 4, 5))
            for i in range(4):
                if i > 0:
                    surf = data.tiny[i + 4]
                    big = data.normal[i + 4]
                else:
                    surf = data.shaded[i + 4]
                    big = data.angry[i + 4]
                system.blit(big, data.board2screen((i, 3 + (i % 2))))
                system.blit(big, data.board2screen(((i + 2) % 4, 3 + ((i + 1) % 2))))
                x = 24 + 240 + 4 + i / 2 * 70
                y = 172 + (i % 2) * 38
                system.blit(surf, (x, y))
                text = fonter.render(str(i * 3), 36)
                system.blit(text, (x + 44, y + 2))
            # Explanation 2
            text = fonter.render('CLICK ON THE BONUS TO REMOVE ALL', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 252 - h / 2))
            text = fonter.render('MONSTERS OF A RANDOM KIND.', 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 276 - h / 2))
            shape = data.special[self.timer % 7]
            # Iter 1
            system.blit_board((0, 6, 3, 8))
            system.blit(data.normal[1], data.board2screen((0, 6)))
            system.blit(data.normal[2], data.board2screen((0, 7)))
            system.blit(shape, data.board2screen((1, 6)))
            system.blit(data.normal[5], data.board2screen((1, 7)))
            system.blit(data.normal[2], data.board2screen((2, 6)))
            system.blit(data.normal[0], data.board2screen((2, 7)))
            # Iter 2
            system.blit_board((4, 6, 7, 8))
            system.blit(data.normal[1], data.board2screen((4, 6)))
            system.blit(data.exploded[2], data.board2screen((4, 7)))
            system.blit(data.normal[5], data.board2screen((5, 7)))
            system.blit(data.exploded[2], data.board2screen((6, 6)))
            system.blit(data.normal[0], data.board2screen((6, 7)))
            # Print bonus
            text = fonter.render('10', 36)
            w, h = text.get_rect().size
            x, y = data.board2screen((4, 7))
            system.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
            x, y = data.board2screen((5, 6))
            system.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
            x, y = data.board2screen((6, 6))
            system.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                system.play('whip')
                self.status = STATUS_MENU
                return
            elif event.type == MOUSEBUTTONDOWN:
                system.play('whip')
                self.page += 1
                if self.page >= 4:
                    self.status = STATUS_MENU
                return

    def iterate_scores(self):
        self.generic_draw()
        self.copyright_draw()
        text = fonter.render('HIGH SCORES', 60)
        w, h = text.get_rect().size
        system.blit(text, (24 + 192 - w / 2, 24 + 24 - h / 2))
        # Dummy scores list
        scores = [['UNIMPLEMENTED', 100 - x * 10, 1] for x in range(10)]
        # Print our list
        for x in range(10):
            name, score, level = hiscores.scores['CLASSIC'][x]
            text = fonter.render(str(x + 1) + '. ' + name, 32)
            w, h = text.get_rect().size
            system.blit(text, (24 + 24, 24 + 72 + 32 * x - h / 2))
            text = fonter.render(str(score), 32)
            w, h = text.get_rect().size
            system.blit(text, (24 + 324 - w, 24 + 72 + 32 * x - h / 2))
            text = fonter.render(str(level), 32)
            w, h = text.get_rect().size
            system.blit(text, (24 + 360 - w, 24 + 72 + 32 * x - h / 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                system.play('whip')
                self.status = STATUS_MENU
                return
            elif event.type == MOUSEBUTTONDOWN:
                system.play('whip')
                self.status = STATUS_MENU
                return

def version():
    print 'monsterz ' + VERSION
    print 'Written by Sam Hocevar, music by MenTaLguY, sound effects by Castle Music'
    print 'Productions, Koumis Productions and Sam Hocevar.'
    print
    print 'Copyright (C) 2005 Sam Hocevar <sam@zoy.org>'
    print '          (C) 2004 Koumis Productions <info@koumis.com>'
    print '          (C) 2002 Castles Music Productions <info@castlesmusic.co.nz>'
    print '          (C) 1998 MenTaLguY <mental@rydia.net>'
    print 'This is free software; you can redistribute it and/or modify it under the terms'
    print 'of the Do What The Fuck You Want To Public License, Version 2, as published'
    print 'by Sam Hocevar. See http://sam.zoy.org/projects/COPYING.WTFPL for more details.'

def usage():
    print 'Usage: monsterz [OPTION]...'
    print
    print 'Options'
    print ' -h, --help         display this help and exit'
    print ' -v, --version      display version information and exit'
    print ' -f, --fullscreen   start in full screen mode'
    print ' -m, --nomusic      disable music'
    print ' -s, --nosfx        disable sound effects'
    print '     --outfd <fd>   output scores to file descriptor <fd>'
    print '     --data <dir>   set alternate data directory to <dir>'
    print '     --score <file> set score file to <file>'
    print
    print 'Report bugs or suggestions to <sam@zoy.org>.'

def main():
    from getopt import getopt, GetoptError
    global system, data, hiscores, fonter, monsterz
    global FLAG_FULLSCREEN, FLAG_MUSIC, FLAG_SFX
    sharedir = dirname(argv[0])
    scorefile = join(sharedir, "scores")
    outfd = None
    try:
        long = ['help', 'version', 'music', 'sound', 'fullscreen',
                'outfd=', 'data=', 'score=']
        opts = getopt(argv[1:], 'hvmsf', long)[0]
    except GetoptError:
        usage()
        exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            exit()
        elif opt in ('-v', '--version'):
            version()
            exit()
        elif opt in ('-m', '--nomusic'):
            FLAG_MUSIC = False
        elif opt in ('-s', '--nosfx'):
            FLAG_SFX = False
        elif opt in ('-f', '--fullscreen'):
            FLAG_FULLSCREEN = True
        elif opt in ('--outfd'):
            try:
                outfd = int(arg)
                write(outfd, '\n')
            except:
                outfd = None
        elif opt in ('--data'):
            sharedir = arg
        elif opt in ('--score'):
            scorefile = arg
    # Init everything and launch the game
    system = System()
    try:
        data = Data(sharedir)
    except:
        print argv[0] + ': could not open data from `' + sharedir + "'."
        exit(1)
    hiscores = Hiscores(scorefile, outfd)
    fonter = Fonter()
    monsterz = Monsterz()
    monsterz.go()
    exit()

if __name__ == '__main__':
    main()

