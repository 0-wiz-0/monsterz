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
from sys import argv
from os.path import join, dirname

# constants
HAVE_SOUND = True
HAVE_AI = False # broken

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
BOARD_WIDTH = 8
BOARD_HEIGHT = 8

STATUS_MENU = 0
STATUS_PLAY = 1
STATUS_HELP = 2
STATUS_ABOUT = 3
STATUS_SCORES = 4
STATUS_QUIT = -1

LOST_DELAY = 40
SCROLL_DELAY = 40
WIN_DELAY = 10
SWITCH_DELAY = 4
WARNING_DELAY = 12

class Data:
    def __init__(self, dir = dirname(argv[0])):
        # Load stuff
        tiles = pygame.image.load(join(dir, 'tiles.png')).convert_alpha()
        w, h = tiles.get_rect().size
        if w * 9 != h * 5:
            raise 'error: ' + file + ' has wrong image size'
        self.tiles = tiles
        self.board = pygame.image.load(join(dir, 'board.png')).convert()
        self.logo = pygame.image.load(join(dir, 'logo.png')).convert_alpha()
        self.orig_size = w / 5
        self.tile_size = min((SCREEN_WIDTH - 20) / BOARD_WIDTH,
                             (SCREEN_HEIGHT - 20) * 17 / 20 / BOARD_HEIGHT)
        self.normal = {}
        self.blink = {}
        self.tiny = {}
        self.shaded = {}
        self.surprise = {}
        self.angry = {}
        self.exploded = {}
        self.special = {}
        self.selector = None
        self.wav = {}
        if HAVE_SOUND:
            pygame.mixer.music.load(join(dir, 'music.s3m'))
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play(-1, 0.0)
            for s in ['click', 'grunt', 'ding', 'whip', 'pop', 'duh', \
                      'boing', 'applause', 'laugh', 'warning']:
                self.wav[s] = pygame.mixer.Sound(join(dir, s + '.wav'))

    def _scale(self, surf, size):
        w, h = surf.get_size()
        if (w, h) == size:
            return pygame.transform.scale(surf, size)
        return pygame.transform.rotozoom(surf, 0.0, 1.0 * size[0] / w)

    def play_sound(self, sound):
        if HAVE_SOUND: self.wav[sound].play()

    def make_sprites(self):
        t = self.tile_size
        s = self.orig_size
        scale = self._scale
        crop = self.tiles.subsurface
        # Create sprites
        for i in range(8):
            self.normal[i] = scale(crop((0, (i + 1) * s, s, s)), (t, t))
            self.tiny[i] = scale(self.normal[i], (t * 3 / 4, t * 3 / 4))
            self.shaded[i] = scale(self.normal[i], (t * 3 / 4, t * 3 / 4))
            try:
                pixels = pygame.surfarray.pixels3d(self.shaded[i])
                alpha = pygame.surfarray.pixels_alpha(self.shaded[i])
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
                pass
            self.blink[i] = scale(crop((s, (i + 1) * s, s, s)), (t, t))
            self.surprise[i] = scale(crop((s * 2, (i + 1) * s, s, s)), (t, t))
            self.angry[i] = scale(crop((s * 3, (i + 1) * s, s, s)), (t, t))
            self.exploded[i] = scale(crop((s * 4, (i + 1) * s, s, s)), (t, t))
            #tmp = crop((s, 0, s, s)).copy() # marche pas !
            special = scale(crop((s, 0, s, s)), (t, t)) # marche...
            mini = crop((0, (i + 1) * s, s, s))
            mini = scale(mini, (t * 7 / 8 - 1, t * 7 / 8 - 1))
            special.blit(mini, (s / 16, s / 16))
            self.special[i] = scale(special, (t, t))
        # Create selector sprite
        self.selector = scale(crop((0, 0, s, s)), (t, t))

    def board2screen(self, coord):
        x, y = coord
        return (x * data.tile_size + 24, y * data.tile_size + 24)

    def screen2board(self, coord):
        x, y = coord
        return ((x - 24) / data.tile_size, (y - 24) / data.tile_size)

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
        text.fill(black.get_at((0, 0)))
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
        self.needed = {}
        self.done = {}
        self.bonus_list = []
        self.blink_list = {}
        self.disappear_list = []
        self.surprised_list = []
        self.clicks = []
        self.select = None
        self.switch = None
        self.score = 0
        self.lost_timer = 0
        self.lost_offset = {}
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                self.lost_offset[(x, y)] = (0, 0)
        self.win_timer = 0
        self.warning_timer = 0
        self.switch_timer = 0
        self.level_timer = SCROLL_DELAY / 2
        self.board_timer = 0
        self.missed = False
        self.check_moves = False
        self.will_play = None
        self.pause = False
        self.pause_bitmap = None
        self.play_again = False
        self.level = 1
        self.new_level()
        self.oldticks = pygame.time.get_ticks()

    def get_random(self, no_special = False):
        if not no_special and randint(0, 1000) == 0:
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
        for z in range(BOARD_HEIGHT):
            y = BOARD_HEIGHT - z - 1
            for x in range(BOARD_WIDTH):
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
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH - 2):
                a = self.board.get((x, y))
                if not a or a == 0: continue
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
                if not a or a == 0: continue
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
            xoff = 0
            yoff = (SCROLL_DELAY - timer) * (SCROLL_DELAY - timer)
            yoff = yoff * 50 * 50 / SCROLL_DELAY / SCROLL_DELAY
        elif timer > 0:
            xoff = 0
            yoff = - timer * timer
            yoff = yoff * 50 * 50 / SCROLL_DELAY / SCROLL_DELAY
        else:
            xoff = 0
            yoff = 0
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
            if self.lost_timer:
                xoff, yoff = self.lost_offset[c]
                d = LOST_DELAY - self.lost_timer
                xoff += (randint(0, d) - randint(0, d)) * randint(0, d) / 4
                yoff += (randint(0, d) - randint(0, d)) * randint(0, d) / 4
                self.lost_offset[c] = (xoff, yoff)
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
            self.pieces_draw(shape, (x + xoff, y + yoff))
        # Draw selector if necessary
        if self.select:
            bg.blit(data.selector, select_coord)

    def pieces_draw(self, sprite, (x, y)):
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
        bg.blit(sprite, (x, y))

    def game_draw(self):
        # Draw timebar
        timebar = pygame.Surface((400, 24)).convert_alpha()
        timebar.fill((0, 0, 0, 127))
        w = 400 * self.time / 2000000
        if w > 0:
            if self.warning_timer:
                ratio = 1.0 * abs(2 * self.warning_timer - WARNING_DELAY) \
                            / WARNING_DELAY
                c = (200 * ratio, 0, 0, 127)
            elif self.time <= 350000:
                c = (200, 0, 0, 127)
            elif self.time <= 700000:
                ratio = 1.0 * (self.time - 350000) / 350000
                c = (200, 180 * ratio, 0, 127)
            elif self.time <= 1000000:
                ratio = 1.0 * (1000000 - self.time) / 300000
                c = (200 * ratio, 200 - 20 * ratio, 0, 127)
            else:
                c = (0, 200, 0, 127)
            pygame.draw.rect(timebar, c, (0, 0, w, 24))
        bg.blit(timebar, (16, 440))
        # Draw pieces
        if self.pause:
            bg.blit(self.pause_bitmap, (72, 24))
            text = fonter.render('PAUSED', 120)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 336 - h / 2))
        elif self.lost_timer >= 0:
            self.board_draw()
        # Print play again message
        if self.lost_timer < 0:
            text = fonter.render('GAME OVER', 80)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
            text = fonter.render('CLICK TO CONTINUE', 24)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 240 - h / 2))
        # Print new level stuff
        if self.level_timer > SCROLL_DELAY / 2:
            text = fonter.render('LEVEL UP!', 80)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # When no more moves are possible
        if self.board_timer > SCROLL_DELAY / 2:
            text = fonter.render('NO MORE MOVES!', 60)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # Print bonus
        for b in self.bonus_list:
            text = fonter.render(str(b[1]), 36)
            w, h = text.get_rect().size
            x, y = data.board2screen(b[0])
            bg.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        # Print score
        bg.blit(fonter.render(str(self.score), 60), (444, 10))
        # Print level
        msg = 'LEVEL ' + str(self.level)
        if self.needed[1]: msg += ' - ' + str(self.needed[1])
        text = fonter.render(msg, 36)
        bg.blit(text, (444, 58))
        # Print done/needed
        for i in range(self.population):
            if not self.needed[i + 1]:
                break
            if self.done[i + 1] >= self.needed[i + 1]:
                surf = data.tiny[i]
            else:
                surf = data.shaded[i]
            bg.blit(surf, (444, 100 + i * 38))
            text = fonter.render(str(self.done[i + 1]), 36)
            bg.blit(text, (488, 102 + i * 38))

    def toggle_pause(self):
        self.pause = not self.pause
        if self.pause:
            self.pause_bitmap = pygame.transform.scale(data.normal[self.get_random(no_special = True) - 1], (6 * data.tile_size, 6 * data.tile_size))
        else:
            del self.pause_bitmap

class Monsterz:
    def __init__(self):
        # Compute stuff
        data.make_sprites()
        # Init values
        self.status = STATUS_MENU
        self.clock = pygame.time.Clock()
        self.timer = 0

    def go(self):
        while True:
            if self.status == STATUS_MENU:
                iterator = self.iterate_menu
            elif self.status == STATUS_PLAY:
                self.game = Game()
                iterator = self.iterate_play
            elif self.status == STATUS_HELP:
                iterator = self.iterate_help
            elif self.status == STATUS_SCORES:
                iterator = self.iterate_scores
            elif self.status == STATUS_QUIT:
                return
            self.status = None
            iterator()
            win.blit(bg, (0, 0))
            pygame.display.flip()
            self.timer += 1
            self.clock.tick(12)

    def generic_draw(self):
        bg.blit(data.board, (0, 0))

    def generic_event(self, event):
        if event.type == QUIT:
            self.status = STATUS_QUIT
            return True
        elif event.type == KEYDOWN and event.key == K_f:
            pygame.display.toggle_fullscreen()
            return True
        return False

    def iterate_menu(self):
        self.generic_draw()
        x, y = data.screen2board(pygame.mouse.get_pos())
        colors = [(255, 255, 255)] * 4
        shapes = [data.blink[2], data.blink[3], data.blink[4], data.blink[0]]
        messages = ['NEW GAME', 'HELP', 'SCORES', 'QUIT']
        if y == 4 and x >= 1 and x <= 6:
            area = STATUS_PLAY
            colors[0] = (0, 255, 0)
            shapes[0] = data.surprise[2]
        elif y == 5 and x >= 1 and x <= 4:
            area = STATUS_HELP
            colors[1] = (255, 0, 255)
            shapes[1] = data.surprise[3]
        elif y == 6 and x >= 1 and x <= 5:
            area = STATUS_SCORES
            colors[2] = (255, 255, 0)
            shapes[2] = data.surprise[4]
        elif y == 7 and x >= 1 and x <= 4:
            area = STATUS_QUIT
            colors[3] = (255, 0, 0)
            shapes[3] = data.surprise[0]
        else:
            area = None
        w, h = data.logo.get_size()
        bg.blit(data.logo, (24 + 192 - w / 2, 24 + 96 - h / 2))
        for x in range(4):
            bg.blit(shapes[x], data.board2screen((1, 4 + x)))
            text = fonter.render(messages[x], 48, colors[x])
            w, h = text.get_rect().size
            bg.blit(text, (24 + 102, 24 + 216 + 48 * x - h / 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                self.status = STATUS_QUIT
                return
            elif event.type == MOUSEBUTTONDOWN and area:
                self.status = area
                return

    def iterate_play(self):
        game = self.game
        ask_pause = False
        ticks = pygame.time.get_ticks()
        delta = (ticks - game.oldticks) * 400 / (11 - game.level)
        game.oldticks = ticks
        # Draw screen
        self.generic_draw()
        if game.check_moves:
            for move in game.list_moves():
                break
            else:
                data.play_sound('ding')
                game.board_timer = SCROLL_DELAY
            game.check_moves = False
            game.clicks = []
        game.game_draw()
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                self.status = STATUS_MENU
                return
            elif event.type == KEYDOWN and (event.key == K_p or event.key == K_SPACE):
                ask_pause = True
            elif event.type == MOUSEBUTTONDOWN:
                if game.lost_timer < 0:
                    self.status = STATUS_MENU
                    return
                x, y = data.screen2board(event.pos)
                if x < 0 or x >= BOARD_WIDTH or y < 0 or y >= BOARD_HEIGHT:
                    continue
                game.clicks.append((x, y))
        # If paused, do nothing
        if game.pause and not ask_pause:
            return
        # Resolve winning moves and chain reactions
        if game.board_timer:
            game.board_timer -= 1
            if game.board_timer is SCROLL_DELAY / 2:
                game.new_board()
            elif game.board_timer is 0:
                data.play_sound('boing')
                game.check_moves = True # Need to check again
            return
        if game.lost_timer:
            game.lost_timer -= 1
            if game.lost_timer is 0:
                print str(game.level) + ':' + str(game.score)
                game.lost = True
                game.lost_timer = -1 # Continue forever
            return
        if game.switch_timer:
            game.switch_timer -= 1
            if game.switch_timer is 0:
                game.board[game.select], game.board[game.switch] = \
                    game.board[game.switch], game.board[game.select]
                if game.missed:
                    game.clicks = []
                    game.missed = False
                else:
                    game.wins = game.get_wins()
                    if not game.wins:
                        data.play_sound('whip')
                        game.missed = True
                        game.switch_timer = SWITCH_DELAY
                        return
                    game.win_iter = 0
                    game.win_timer = WIN_DELAY
                game.select = None
                game.switch = None
            return
        if game.level_timer:
            game.level_timer -= 1
            if game.level_timer is SCROLL_DELAY / 2:
                game.level += 1
                game.new_level()
            elif game.level_timer is 0:
                data.play_sound('boing')
                game.blink_list = {}
                game.check_moves = True
            return
        if game.win_timer:
            game.win_timer -= 1
            if game.win_timer is WIN_DELAY - 1:
                data.play_sound('duh')
                for w in game.wins:
                    for x, y in w:
                        game.surprised_list.append((x, y))
            elif game.win_timer is WIN_DELAY * 3 / 6:
                data.play_sound('pop')
                game.scorebonus = 0
                game.timebonus = 0
                for w in game.wins:
                    if len(w) is 1:
                        points = 10 * game.level
                    else:
                        points = (10 * game.level) * (2 ** (game.win_iter + len(w) - 3))
                    game.scorebonus += points
                    game.timebonus += 45000 * len(w)
                    x2, y2 = 0.0, 0.0
                    for x, y in w:
                        x2 += x
                        y2 += y
                    game.bonus_list.append([(x2 / len(w), y2 / len(w)), points])
                game.disappear_list = game.surprised_list
                game.surprised_list = []
            elif game.win_timer is WIN_DELAY * 2 / 6:
                game.bonus_list = []
                for x, y in game.disappear_list:
                    if game.board.has_key((x, y)):
                        game.done[game.board[(x, y)]] += 1
                        del game.board[(x, y)]
                if game.angry_tiles == -1:
                    unfinished = 0
                    for i in range(game.population):
                        if game.done[i + 1] < game.needed[i + 1]:
                            unfinished += 1
                            angry = i + 1
                    if unfinished == 1:
                        data.play_sound('grunt')
                        game.angry_tiles = angry
                game.disappear_list = []
            elif game.win_timer is WIN_DELAY / 6:
                game.time += game.timebonus
                if game.time > 2000000:
                    game.time = 2000000
                game.score += game.scorebonus
                game.fill_board()
                data.play_sound('boing')
            elif game.win_timer is 0:
                game.wins = game.get_wins()
                if game.wins:
                    game.win_timer = WIN_DELAY
                    game.win_iter += 1
                elif game.needed[1]:
                    # Check for new level
                    for i in range(game.population):
                        if game.done[i + 1] < game.needed[i + 1]:
                            game.check_moves = True
                            break
                    else:
                        data.play_sound('applause')
                        game.select = None
                        game.level_timer = SCROLL_DELAY
            return
        if game.warning_timer:
            game.warning_timer -= 1
        elif game.time <= 200000:
            data.play_sound('warning')
            game.warning_timer = WARNING_DELAY
        # Update time
        game.time -= delta
        if game.time <= 0:
            data.play_sound('laugh')
            game.select = None
            game.lost_timer = LOST_DELAY
            return
        # Honour pause request
        if ask_pause:
            game.toggle_pause()
            return
        # Handle moves from the AI:
        if HAVE_AI:
            if not game.will_play:
                game.will_play = None
                # Special piece?
                if randint(0, 3) == 0:
                    special = None
                    for y in range(BOARD_HEIGHT):
                        for x in range(BOARD_WIDTH):
                            if game.board[(x, y)] == 0:
                                special = (x, y)
                                break
                        if special:
                            break
                    if special:
                        incomplete = 0
                        for i in range(game.population):
                            if game.done[i + 1] >= game.needed[i + 1]:
                                incomplete += 1
                                if incomplete == 2:
                                    break
                        if incomplete == 2 or randint(0, 3) == 0:
                            game.will_play = [None, special]
                # Normal piece
                if not game.will_play:
                    min = 0
                    for move in game.list_moves():
                        color = game.board.get(move[0])
                        if game.done[color] >= min or \
                           game.done[color] >= game.needed[color]:
                            game.will_play = move
                            min = game.done[color]
                game.ai_timer = 15 - game.level
            if game.ai_timer is (15 - game.level) / 2:
                game.clicks.append(game.will_play[0])
            elif game.ai_timer is 0:
                game.clicks.append(game.will_play[1])
                game.will_play = None
            game.ai_timer -= 1
        # Handle moves from the player or the AI
        if game.clicks:
            played = game.clicks.pop(0)
            if game.select:
                x1, y1 = game.select
                x2, y2 = played
                if x1 == x2 and y1 == y2:
                    data.play_sound('click')
                    game.select = None
                    return
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    return
                data.play_sound('whip')
                game.switch = played
                game.switch_timer = SWITCH_DELAY
            else:
                if game.board[played] != 0:
                    data.play_sound('click')
                    game.select = played
                    return
                # Deal with the special block
                game.wins = []
                target = 1 + (monsterz.timer % game.population)
                found = 0
                for y in range(BOARD_HEIGHT):
                    for x in range(BOARD_WIDTH):
                        if game.board[(x, y)] == target:
                            game.wins.append([(x, y)])
                game.board[played] = target
                game.wins.append([played])
                game.win_iter = 0
                game.win_timer = WIN_DELAY
            return

    def iterate_help(self):
        self.generic_draw()
        # Title
        text = fonter.render('INSTRUCTIONS', 60)
        w, h = text.get_rect().size
        bg.blit(text, (24 + 192 - w / 2, 24 + 24 - h / 2))
        # Explanation 1
        text = fonter.render('SWAP ADJACENT MONSTERS TO CREATE', 24)
        w, h = text.get_rect().size
        bg.blit(text, (24 + 6, 24 + 60 - h / 2))
        text = fonter.render('ALIGNMENTS OF THREE OR MORE.', 24)
        w, h = text.get_rect().size
        bg.blit(text, (24 + 6, 24 + 84 - h / 2))
        # Iter 1
        bg.blit(data.normal[2], data.board2screen((0, 2)))
        bg.blit(data.normal[3], data.board2screen((0, 3)))
        bg.blit(data.blink[0], data.board2screen((0, 4)))
        bg.blit(data.normal[0], data.board2screen((1, 2)))
        bg.blit(data.normal[0], data.board2screen((1, 3)))
        bg.blit(data.normal[4], data.board2screen((1, 4)))
        bg.blit(data.selector, data.board2screen((0, 4)))
        # Iter 2
        bg.blit(data.normal[2], data.board2screen((3, 2)))
        bg.blit(data.normal[3], data.board2screen((3, 3)))
        bg.blit(data.normal[4], data.board2screen((3, 4)))
        bg.blit(data.surprise[0], data.board2screen((4, 2)))
        bg.blit(data.surprise[0], data.board2screen((4, 3)))
        bg.blit(data.surprise[0], data.board2screen((4, 4)))
        bg.blit(data.selector, data.board2screen((4, 4)))
        # Iter 2
        bg.blit(data.normal[2], data.board2screen((6, 2)))
        bg.blit(data.normal[3], data.board2screen((6, 3)))
        bg.blit(data.normal[4], data.board2screen((6, 4)))
        bg.blit(data.exploded[0], data.board2screen((7, 2)))
        bg.blit(data.exploded[0], data.board2screen((7, 3)))
        bg.blit(data.exploded[0], data.board2screen((7, 4)))
        # Explanation 2
        text = fonter.render('CLICK ON THE BONUS TO REMOVE ALL', 24)
        w, h = text.get_rect().size
        bg.blit(text, (24 + 6, 24 + 252 - h / 2))
        text = fonter.render('MONSTERS OF A RANDOM KIND.', 24)
        w, h = text.get_rect().size
        bg.blit(text, (24 + 6, 24 + 276 - h / 2))
        shape = data.special[self.timer % 7]
        # Iter 1
        bg.blit(data.normal[1], data.board2screen((0, 6)))
        bg.blit(data.normal[2], data.board2screen((0, 7)))
        bg.blit(shape, data.board2screen((1, 6)))
        bg.blit(data.normal[5], data.board2screen((1, 7)))
        bg.blit(data.normal[2], data.board2screen((2, 6)))
        bg.blit(data.normal[4], data.board2screen((2, 7)))
        # Iter 2
        bg.blit(data.normal[1], data.board2screen((4, 6)))
        bg.blit(data.exploded[2], data.board2screen((4, 7)))
        bg.blit(data.normal[5], data.board2screen((5, 7)))
        bg.blit(data.exploded[2], data.board2screen((6, 6)))
        bg.blit(data.normal[4], data.board2screen((6, 7)))
        # Print bonus
        text = fonter.render('10', 36)
        w, h = text.get_rect().size
        x, y = data.board2screen((7, 3))
        bg.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        x, y = data.board2screen((4, 7))
        bg.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        x, y = data.board2screen((5, 6))
        bg.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        x, y = data.board2screen((6, 6))
        bg.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                self.status = STATUS_MENU
                return
            elif event.type == MOUSEBUTTONDOWN:
                self.status = STATUS_MENU
                return

    def iterate_scores(self):
        self.generic_draw()
        text = fonter.render('SCORES', 60)
        w, h = text.get_rect().size
        bg.blit(text, (24 + 192 - w / 2, 24 + 24 - h / 2))
        for x in range(10):
            text = fonter.render(str(x + 1) + '. UNIMPLEMENTED', 32)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 24, 24 + 72 + 32 * x - h / 2))
            text = fonter.render(str(100 - x * 10), 32)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 324 - w, 24 + 72 + 32 * x - h / 2))
            text = fonter.render(str(1), 32)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 360 - w, 24 + 72 + 32 * x - h / 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                self.status = STATUS_MENU
                return
            elif event.type == MOUSEBUTTONDOWN:
                self.status = STATUS_MENU
                return

# Pygame init
pygame.init()
# Sound init
if HAVE_SOUND:
    try:
        HAVE_SOUND = pygame.mixer.get_init()
    except:
        HAVE_SOUND = False
# Display init
win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
bg = pygame.Surface(win.get_size())
pygame.display.set_caption('Monsterz')
data = Data()
fonter = Fonter()
# Go!
monsterz = Monsterz()
monsterz.go()

