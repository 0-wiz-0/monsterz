#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
HAVE_SOUND = True
HAVE_AI = False # broken

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

EXIT_QUIT = -1
EXIT_REPLAY = -2

LOST_DELAY = 40
SCROLL_DELAY = 40
WIN_DELAY = 10
SWITCH_DELAY = 4
WARNING_DELAY = 12

class Theme:
    def __init__(self, dir = dirname(argv[0])):
        # Load stuff
        tiles = pygame.image.load(join(dir, 'tiles.png')).convert_alpha()
        w, h = tiles.get_rect().size
        if w * 9 != h * 5:
            raise 'error: ' + file + ' has wrong image size'
        self.tiles = tiles
        self.board = pygame.image.load(join(dir, 'board.png')).convert()
        self.orig_size = w / 5
        self.tile_size = None
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

    def play(self, sound):
        if HAVE_SOUND: self.wav[sound].play()

    def _scale(self, surf, size):
        w, h = surf.get_size()
        if (w, h) == size:
            return pygame.transform.scale(surf, size)
        return pygame.transform.rotozoom(surf, 0.0, 1.0 * size[0] / w)

    def make_sprites(self, t):
        self.tile_size = t
        s = self.orig_size
        scale = self._scale
        crop = self.tiles.subsurface
        # Create sprites
        for i in range(8):
            self.normal[i] = scale(crop((0, (i + 1) * s, s, s)), (t, t))
            self.tiny[i] = scale(self.normal[i], (t * 3 / 4, t * 3 / 4))
            self.shaded[i] = scale(self.normal[i], (t * 3 / 4, t * 3 / 4))
            pixels = pygame.surfarray.pixels3d(self.shaded[i])
            alpha = pygame.surfarray.pixels_alpha(self.shaded[i])
            for y, line in enumerate(pixels):
                for x, p in enumerate(line):
                    r, g, b = p
                    M = max(r, g, b)
                    m = min(r, g, b)
                    val = (r + g + b + 2 * M) / 5
                    p[:] = (val + r) / 2, (val + g) / 2, (val + b) / 2
                    if alpha[y][x] >= 250: alpha[y][x] = 255 - (M - m) * 3 / 4
            del pixels
            del alpha
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

# Start all the stuff
class Game:
    def __init__(self, level = 1):
        # Init values
        self.board_width, self.board_height = 8, 8
        self.needed = {}
        self.done = {}
        self.bonus_list = []
        self.blink_list = {}
        self.disappear_list = []
        self.surprised_list = []
        self.clicks = []
        self.select = None
        self.switch = None
        self.text_cache = []
        # Compute stuff
        tile_size = min((SCREEN_WIDTH - 20) / self.board_width,
                        (SCREEN_HEIGHT - 20) * 17 / 20 / self.board_height)
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
        self.warning_timer = 0
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
            self.clock.tick(12)

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
                if not self.get_wins(): break

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
                if not a or a == 0: continue
                b = self.board.get((x - 1, y))
                if b and a == b: continue
                len = 1
                for t in range(1, self.board_width - x):
                    b = self.board.get((x + t, y))
                    if a != b: break
                    len += 1
                if len < 3: continue
                win = []
                for t in range(len):
                    win.append((x + t, y))
                wins.append(win)
        # Horizontal
        for x in range(self.board_width):
            for y in range(self.board_height - 2):
                a = self.board.get((x, y))
                if not a or a == 0: continue
                b = self.board.get((x, y - 1))
                if b and a == b: continue
                len = 1
                for t in range(1, self.board_height - y):
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
        for y in range(self.board_height):
            for x in range(self.board_width):
                a = self.board.get((x, y))
                if a == 0:
                   continue # We don’t want no special piece
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
            if self.level < 10:
                self.needed[i + 1] = self.level + 2
            else:
                self.needed[i + 1] = 0 # level 10 is the highest
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
        c = randint(0, self.board_width - 1), randint(0, self.board_height - 1)
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
                if self.blink_list[c] is 0: del self.blink_list[c]
            else:
                shape = theme.normal[n - 1]
            # Remember the selector coordinates
            if c == self.select and not self.missed \
            or c == self.switch and self.missed:
                select_coord = (x, y)
                shape = theme.blink[n - 1] # Not sure if it looks nice
            # Print the shit
            self.board_blit(shape, (x + xoff, y + yoff))
        # Draw selector if necessary
        if self.select:
            bg.blit(theme.selector, select_coord)

    def board_blit(self, sprite, (x, y)):
        width = theme.tile_size
        crop = sprite.subsurface
        # Constrain X
        if x < 10 - theme.tile_size or x > 24 + 8 * theme.tile_size + 14:
            return
        elif x < 10:
            delta = 10 - x
            sprite = crop((delta, 0, theme.tile_size - delta, theme.tile_size))
            crop = sprite.subsurface
            x += delta
            width -= delta
        elif x > 24 + 7 * theme.tile_size + 14:
            delta = x - 24 - 7 * theme.tile_size - 14
            sprite = crop((0, 0, theme.tile_size - delta, theme.tile_size))
            crop = sprite.subsurface
            width -= delta
        # Constrain Y
        if y < 10 - theme.tile_size or y > 24 + 8 * theme.tile_size + 14:
            return
        elif y < 10:
            delta = 10 - y
            sprite = crop((0, delta, width, theme.tile_size - delta))
            y += delta
        elif y > 24 + 7 * theme.tile_size + 14:
            delta = y - 24 - 7 * theme.tile_size - 14
            sprite = crop((0, 0, width, theme.tile_size - delta))
        bg.blit(sprite, (x, y))

    def toggle_pause(self):
        self.pause = not self.pause
        if self.pause:
            self.pause_bitmap = pygame.transform.scale(theme.normal[self.get_random(no_special = True) - 1], (6 * theme.tile_size, 6 * theme.tile_size))
        else:
            del self.pause_bitmap

    def render_text(self, msg, size):
        for i, (m, s, t) in enumerate(self.text_cache):
            if s == size and m == msg:
                del self.text_cache[i]
                self.text_cache.append((m, s, t))
                return t
        font = pygame.font.Font(None, size)
        delta = 1 + size / 16
        black = font.render(msg, 2, (0, 0, 0))
        w, h = black.get_size()
        text = pygame.Surface((w + delta, h + delta)).convert_alpha()
        text.fill(black.get_at((0, 0)))
        for x, y in [(5, 5), (6, 3), (5, 1), (3, 0),
                     (1, 1), (0, 3), (1, 5), (3, 6)]:
            text.blit(black, (x * delta / 6, y * delta / 6))
        white = font.render(msg, 2, (255, 255, 255))
        text.blit(white, (delta / 2, delta / 2))
        self.text_cache.append((msg, size, text))
        # Keep 15 items in our cache, it’s more than enough
        if len(self.text_cache) > 15:
            self.text_cache.pop(0)
        return text

    def draw_game(self):
        # Draw background
        bg.blit(theme.board, (0, 0))
        # Draw timebar
        pygame.draw.rect(bg, (60, 60, 60), (16, 440, 400, 2))
        pygame.draw.rect(bg, (40, 40, 40), (16, 442, 400, 20))
        pygame.draw.rect(bg, (0, 0, 0), (16, 462, 400, 2))
        w = 400 * self.time / 2000000
        if w > 0:
            if self.warning_timer:
                ratio = 1.0 * abs(2 * self.warning_timer - WARNING_DELAY) \
                            / WARNING_DELAY
                c0 = (60 + 195 * ratio, 60 + 40 * ratio, 60 + 40 * ratio)
                c1 = (55 + 200 * ratio, 40 - 40 * ratio, 40 - 40 * ratio)
                c2 = (220 * ratio, 0, 0)
            elif self.time <= 350000:
                c0 = (255, 100, 100)
                c1 = (255, 0, 0)
                c2 = (220, 0, 0)
            elif self.time <= 650000:
                c0 = (255, 255, 100)
                c1 = (255, 240, 0)
                c2 = (220, 180, 0)
            else:
                c0 = (100, 255, 100)
                c1 = (0, 255, 0)
                c2 = (0, 220, 0)
            pygame.draw.rect(bg, c0, (16, 440, w, 2))
            pygame.draw.rect(bg, c1, (16, 442, w, 20))
            pygame.draw.rect(bg, c2, (16, 462, w, 2))
        # Draw pieces
        if self.pause:
            bg.blit(self.pause_bitmap, (72, 24))
            text = self.render_text('PAUSED', 120)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 336 - h / 2))
        elif self.lost_timer >= 0:
            self.draw_board()
        # Print play again message
        if self.lost_timer < 0:
            text = self.render_text('CLICK TO PLAY AGAIN', 48)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # Print new level stuff
        if self.level_timer > SCROLL_DELAY / 2:
            text = self.render_text('LEVEL UP!', 80)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # When no more moves are possible
        if self.board_timer > SCROLL_DELAY / 2:
            text = self.render_text('NO MORE MOVES!', 60)
            w, h = text.get_rect().size
            bg.blit(text, (24 + 192 - w / 2, 24 + 192 - h / 2))
        # Print bonus
        for b in self.bonus_list:
            text = self.render_text(str(b[1]), 36)
            w, h = text.get_rect().size
            x, y = self.board2screen(b[0])
            bg.blit(text, (x + 24 - w / 2, y + 24 - h / 2))
        # Print score
        bg.blit(self.render_text(str(self.score), 60), (444, 10))
        # Print level
        msg = 'LEVEL ' + str(self.level)
        if self.needed[1]: msg += ' - ' + str(self.needed[1])
        text = self.render_text(msg, 36)
        bg.blit(text, (444, 58))
        # Print done/needed
        for i in range(self.population):
            if not self.needed[i + 1]:
                break
            if self.done[i + 1] >= self.needed[i + 1]:
                surf = theme.tiny[i]
            else:
                surf = theme.shaded[i]
            bg.blit(surf, (444, 100 + i * 38))
            text = self.render_text(str(self.done[i + 1]), 36)
            bg.blit(text, (488, 102 + i * 38))
        win.blit(bg, (0, 0))
        pygame.display.flip()

    def iterate(self):
        ask_pause = False
        ticks = pygame.time.get_ticks()
        delta = (ticks - self.oldticks) * 400 / (11 - self.level)
        self.oldticks = ticks
        self.special_index = (self.special_index + 1) % self.population
        # Draw screen
        if self.check_moves:
            for move in self.list_moves():
                break
            else:
                theme.play('ding')
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
            elif event.type == KEYDOWN and (event.key == K_p or event.key == K_SPACE):
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
                theme.play('boing')
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
                self.board[self.select], self.board[self.switch] = \
                    self.board[self.switch], self.board[self.select]
                if self.missed:
                    self.clicks = []
                    self.missed = False
                else:
                    self.wins = self.get_wins()
                    if not self.wins:
                        theme.play('whip')
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
                theme.play('boing')
                self.blink_list = {}
                self.check_moves = True
            return
        if self.win_timer:
            self.win_timer -= 1
            if self.win_timer is WIN_DELAY - 1:
                theme.play('duh')
                for w in self.wins:
                    for (x, y) in w:
                        self.surprised_list.append((x, y))
            elif self.win_timer is WIN_DELAY * 3 / 6:
                theme.play('pop')
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
                        theme.play('grunt')
                        self.angry_tiles = angry
                self.disappear_list = []
            elif self.win_timer is WIN_DELAY / 6:
                self.time += self.timebonus
                if self.time > 2000000:
                    self.time = 2000000
                self.score += self.scorebonus
                self.fill_board()
                theme.play('boing')
            elif self.win_timer is 0:
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
                        theme.play('applause')
                        self.select = None
                        self.level_timer = SCROLL_DELAY
            return
        if self.warning_timer:
            self.warning_timer -= 1
        elif self.time <= 200000:
            theme.play('warning')
            self.warning_timer = WARNING_DELAY
        # Update time
        self.time -= delta
        if self.time <= 0:
            theme.play('laugh')
            self.select = None
            self.lost_timer = LOST_DELAY
            return
        # Honour pause request
        if ask_pause:
            self.toggle_pause()
            return
        # Handle moves from the AI:
        if HAVE_AI:
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
                    theme.play('click')
                    self.select = None
                    return
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    return
                theme.play('whip')
                self.switch = played
                self.switch_timer = SWITCH_DELAY
            else:
                if self.board[played] != 0:
                    theme.play('click')
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
pygame.display.set_caption('Alienkeeper')
theme = Theme()
# Read commandline (haha)
level = 1
# Go!
while True:
    game = Game(level = level)
    game.go()
    if game.exit == EXIT_QUIT:
        break

