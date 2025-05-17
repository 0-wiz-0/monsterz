#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 Monsterz: cute puzzle game

 Copyright: (c) 2005 - 2007 Sam Hocevar <sam@zoy.org>
   This program is free software; you can redistribute it and/or
   modify it under the terms of the Do What The Fuck You Want To
   Public License, Version 2, as published by Sam Hocevar. See
   http://sam.zoy.org/projects/COPYING.WTFPL for more details.
"""

import pygame
from pygame.locals import *
from random import randint
from sys import argv, exit, platform
from os.path import join, isdir, isfile, dirname, expanduser
from os import write, mkdir

# String constants
VERSION = "0.8"
COPYRIGHT = (
    "MONSTERZ - COPYRIGHT 2005 - 2007 SAM HOCEVAR - MONSTERZ IS "
    "FREE SOFTWARE, YOU CAN REDISTRIBUTE IT AND/OR MODIFY IT "
    "UNDER THE TERMS OF THE WTFPL LICENSE, VERSION 2 - "
)

# Constants
HAVE_AI = False  # broken

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
BOARD_WIDTH = 8
BOARD_HEIGHT = 8
ITEM_SIZE = 48

ITEMS = 9
ITEM_NONE = -1
ITEM_SPECIAL = ITEMS + 1
ITEM_METAL = ITEMS + 2
ITEM_PUZZLE = ITEMS + 3

STATUS_MENU = 0
STATUS_NEW = 1
STATUS_GAME = 2
STATUS_HELP = 3
STATUS_ABOUT = 4
STATUS_SCORES = 5
STATUS_QUIT = -1

GAME_CLASSIC = 0
GAME_QUEST = 1
GAME_PUZZLE = 2
GAME_TRAINING = 3
ACTION_MOREMONSTERZ = 10
ACTION_LESSMONSTERZ = 11
ACTION_MORELEVEL = 12
ACTION_LESSLEVEL = 13

LOST_DELAY = 40
SCROLL_DELAY = 40
WIN_DELAY = 12
SWITCH_DELAY = 4
WARNING_DELAY = 12
SPECIAL_FREQ = 500

rainbow = [
    (255, 127, 127),
    (255, 255, 0),
    (127, 255, 127),
    (0, 255, 255),
    (127, 127, 255),
    (255, 0, 255),
]

puzzlevels = [
    (5, 1, "2x1", [(3, 3), (4, 2)]),
    (5, 1, "1x2", [(3, 2), (3, 4)]),
    (6, 2, "1x3", [(3, 2), (3, 4), (3, 6)]),
    (6, 2, "3x1", [(3, 2), (4, 3), (5, 4)]),
    (6, 3, "2x1", [(3, 4), (4, 2)]),
    (6, 3, "1x2", [(3, 2), (4, 4)]),
    (7, 4, "2x2", [(3, 2), (4, 3), (3, 4), (4, 4)]),
    (6, 4, "1x3", [(3, 2), (4, 4), (3, 6)]),
    (7, 5, "3x1", [(2, 2), (4, 1), (5, 4)]),
    (7, 5, "2x2", [(3, 0), (5, 0), (2, 7), (4, 7)]),
]


def semi_grayscale(surf):
    try:
        pixels = pygame.surfarray.pixels3d(surf)
        alpha = pygame.surfarray.pixels_alpha(surf)
    except:
        pass
    else:
        # Convert to semi-grayscale
        for y, line in enumerate(pixels):
            for x, p in enumerate(line):
                r, g, b = p
                # convert from numpy.int8 to int
                r = r.item()
                g = g.item()
                b = b.item()
                M = max(r, g, b)
                m = min(r, g, b)
                val = (2 * M + r + g + b) // 5
                p[0] = (val + r) // 2
                p[1] = (val + g) // 2
                p[2] = (val + b) // 2
                if alpha[y][x] >= 250:
                    alpha[y][x] = 255 - (M - m) * 3 // 4
        del pixels
        del alpha
        surf.unlock()


def semi_transp(surf):
    try:
        # Convert to semi-transparency
        pixels = pygame.surfarray.pixels3d(surf)
        alpha = pygame.surfarray.pixels_alpha(surf)
    except:
        # If it did not work, make it empty
        surf.fill((0, 0, 0, 0))
    else:
        for y, line in enumerate(pixels):
            for x, p in enumerate(line):
                r, g, b = p
                # convert from numpy.int8 to int
                r = r.item()
                g = g.item()
                b = b.item()
                M = max(r, g, b)
                m = min(r, g, b)
                p[0] = (m + r) // 2
                p[1] = (m + g) // 2
                p[2] = (m + b) // 2
                if alpha[y][x] >= 250:
                    alpha[y][x] = 255 - M * 2 // 3
        del pixels
        del alpha
        surf.unlock()


def username():
    if platform == "win32":
        from os import environ

        return environ.get("USER") or environ.get("USERNAME") or "You"
    from pwd import getpwuid
    from os import geteuid

    return getpwuid(geteuid())[0]


class Settings:
    def __init__(self, scorefile, outfd):
        # Get username
        self.name = username()
        # Get home directory
        if platform == "win32":
            from os import environ

            tmp = environ.get("APPDATA") or environ.get("TMP")
            if tmp:
                configdir = join(tmp, "monsterz")
            else:
                configdir = join(dirname(argv[0]), "settings")
        else:
            configdir = join(expanduser("~"), ".monsterz")
        # Make sure our directory exists
        if isdir(configdir):
            pass
        elif isfile(configdir):
            raise configdir + " already exists"
        else:
            mkdir(configdir)
        # Set our scorefile
        if scorefile:
            self.scorefile = scorefile
        else:
            self.scorefile = join(configdir, "scores")
        self.outfd = outfd
        self.configfile = join(configdir, "config")
        # Load everything
        self._init_config()
        self._load_config()
        self._load_scores()

    config = {}

    def _init_config(self):
        self.config["fullscreen"] = 0
        self.config["music"] = 1
        self.config["sfx"] = 1
        self.config["difficulty"] = 5
        self.config["items"] = 7

    def _load_config(self):
        from re import compile

        regex = compile("[ \t]*([A-Za-z]+)[ \t]*=[ \t]*([0-9A-Za-z]+)[ \t]*(#.*|)")
        try:
            file = open(self.configfile, "r")
        except:
            return
        for line in file.readlines():
            m = regex.match(line.strip())
            if not m:
                continue
            key, value = m.group(1), int(m.group(2))
            # Sanitise data before using it
            if key == "difficulty":
                if value < 1:
                    value = 1
                elif value > 10:
                    value = 10
            elif key == "items":
                if value < 4:
                    value = 4
                elif value > 8:
                    value = 8
            self.set(key, value)
        file.close()

    def save(self):
        try:
            file = open(self.configfile, "w")
        except:
            return
        file.write("# Monsterz configuration file - automatically saved\r\n")
        for key, value in list(self.config.items()):
            file.write(key + " = " + str(int(value)) + "\r\n")
        file.close()

    def get(self, key):
        if key not in self.config:
            return None
        return self.config[key]

    def set(self, key, value):
        if key not in self.config:
            return
        self.config[key] = value

    def _load_scores(self):
        self.scores = {}
        # Load current score file
        try:
            file = open(self.scorefile, "r")
            lines = file.readlines()
            file.close()
            for l in [line.split(":") for line in lines]:
                if len(l) == 4:
                    self._add_score(l[0], l[1], int(l[2]), int(l[3]))
        except:
            pass
        # Add dummy scores to make sure our score list is full
        for game in ["CLASSIC"]:
            if game not in self.scores:
                self.scores[game] = []
            for x in range(20):
                self._add_score(game, "NOBODY", 0, 1)

    def _add_score(self, game, name, score, level):
        if game not in self.scores:
            self.scores[game] = []
        self.scores[game].append((name, score, level))
        self.scores[game].sort(key=lambda b: b[1] * 100 + b[2], reverse=True)
        self.scores[game] = self.scores[game][0:19]

    def new_score(self, game, score, level):
        # Reload scores
        self._load_scores()
        # Add our score
        self._add_score(game, self.name, score, level)
        # Immediately save
        msg = ""
        for type, list in self.scores.items():
            for name, score, level in list:
                msg += type + ":" + name + ":" + str(score) + ":" + str(level)
                msg += "\n"
        if self.outfd is not None:
            write(self.outfd, msg + "\n")
        else:
            try:
                file = open(self.scorefile, "w")
                file.write(msg)
                file.close()
            except:
                raise
                pass  # Cannot save scores, do nothing...


class Data:
    def __init__(self, dir):
        # Load stuff
        tiles = pygame.image.load(join(dir, "graphics", "tiles.png")).convert_alpha()
        w, h = tiles.get_rect().size
        self.tiles = tiles
        icon = pygame.image.load(join(dir, "graphics", "icon.png")).convert_alpha()
        pygame.display.set_icon(icon)
        self.bigtiles = pygame.image.load(
            join(dir, "graphics", "bigtiles.png")
        ).convert_alpha()
        self.background = pygame.image.load(
            join(dir, "graphics", "background.png")
        ).convert()
        self.board = pygame.image.load(join(dir, "graphics", "board.png")).convert()
        self.logo = pygame.image.load(join(dir, "graphics", "logo.png")).convert_alpha()
        self.orig_size = w // 5
        self.normal = [None] * ITEMS
        self.blink = [None] * ITEMS
        self.tiny = [None] * ITEMS
        self.shaded = [None] * ITEMS
        self.surprise = [None] * ITEMS
        self.angry = [None] * ITEMS
        self.exploded = [None] * ITEMS
        self.special = [None] * ITEMS
        self.selector = None
        # Load sound stuff
        if system.have_sound:
            self.wav = {}
            for s in [
                "click",
                "grunt",
                "ding",
                "whip",
                "pop",
                "duh",
                "boing",
                "applause",
                "laugh",
                "warning",
            ]:
                self.wav[s] = pygame.mixer.Sound(join(dir, "sound", s + ".wav"))
            pygame.mixer.music.load(join(dir, "sound", "music.s3m"))
            pygame.mixer.music.set_volume(0.9)
            # Play immediately
            pygame.mixer.music.play(-1, 0.0)
            if not settings.get("music"):
                pygame.mixer.music.pause()
        # Initialise tiles stuff
        t = ITEM_SIZE
        s = self.orig_size
        scale = self._scale
        tile_at = lambda x, y: self.tiles.subsurface((x * s, y * s, s, s))
        # Create sprites
        for i in range(ITEMS):
            self.normal[i] = scale(tile_at(0, i + 5), (t, t))
            self.tiny[i] = scale(tile_at(0, i + 5), (t * 3 // 4, t * 3 // 4))
            self.shaded[i] = scale(tile_at(3, i + 5), (t * 3 // 4, t * 3 // 4))
            semi_grayscale(self.shaded[i])
            self.blink[i] = scale(tile_at(1, i + 5), (t, t))
            self.surprise[i] = scale(tile_at(2, i + 5), (t, t))
            self.angry[i] = scale(tile_at(3, i + 5), (t, t))
            self.exploded[i] = scale(tile_at(4, i + 5), (t, t))
            # tmp = tile_at(1, 0).copy() # marche pas !
            tmp = scale(tile_at(1, 0), (t, t))  # marche...
            mini = tile_at(0, i + 5)
            mini = scale(mini, (t * 7 // 8 - 1, t * 7 // 8 - 1))
            tmp.blit(mini, (s // 16, s // 16))
            self.special[i] = scale(tmp, (t, t))
        self.led_off = scale(
            self.tiles.subsurface((3 * s, 0, s // 2, s // 2)), (t // 2, t // 2)
        )
        self.led_on = scale(
            self.tiles.subsurface((3 * s + s // 2, 0, s // 2, s // 2)), (t // 2, t // 2)
        )
        self.led_more = scale(
            self.tiles.subsurface((3 * s, s // 2, s // 2, s // 2)), (t // 2, t // 2)
        )
        self.led_less = scale(
            self.tiles.subsurface((3 * s + s // 2, s // 2, s // 2, s // 2)),
            (t // 2, t // 2),
        )
        self.eye = scale(tile_at(2, 0), (t * 3 // 4, t * 3 // 4))
        self.shadeye = scale(tile_at(2, 0), (t * 3 // 4, t * 3 // 4))
        semi_transp(self.shadeye)
        self.arrow = tile_at(4, 0)
        self.selector = scale(tile_at(0, 0), (t, t))
        self.metal = scale(tile_at(3, 3), (t, t))
        self.puzzle = {}
        self.puzzle["2x1"] = (
            scale(tile_at(3, 2), (t, t)),
            scale(tile_at(4, 2), (t, t)),
        )
        self.puzzle["3x1"] = (
            scale(tile_at(1, 4), (t, t)),
            scale(tile_at(2, 4), (t, t)),
            scale(tile_at(3, 4), (t, t)),
        )
        self.puzzle["1x2"] = (
            scale(tile_at(4, 3), (t, t)),
            scale(tile_at(4, 4), (t, t)),
        )
        self.puzzle["1x3"] = (
            scale(tile_at(0, 2), (t, t)),
            scale(tile_at(0, 3), (t, t)),
            scale(tile_at(0, 4), (t, t)),
        )
        self.puzzle["2x2"] = (
            scale(tile_at(1, 2), (t, t)),
            scale(tile_at(2, 2), (t, t)),
            scale(tile_at(1, 3), (t, t)),
            scale(tile_at(2, 3), (t, t)),
        )

    def _scale(self, surf, size):
        w, h = surf.get_size()
        if (w, h) == size:
            return pygame.transform.scale(surf, size)
        return pygame.transform.rotozoom(surf, 0.0, 1.0 * size[0] / w)

    def board2screen(self, coord):
        x, y = coord
        return (x * ITEM_SIZE + 24, y * ITEM_SIZE + 24)

    def screen2board(self, coord):
        x, y = coord
        return ((x - 24) // ITEM_SIZE, (y - 24) // ITEM_SIZE)


class Sprite:
    def __init__(self, surf, coord):
        self.surf = surf
        self.coord = coord

    def set_surf(self, surf):
        return

    def set_coord(self, coord):
        return


class System:
    def __init__(self):
        if settings.get("fullscreen"):
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
        pygame.display.set_caption("Monsterz")

    def blit(self, surf, coords):
        (x, y) = coords
        self.background.blit(surf, (int(x), int(y)))

    def blit_board(self, coords):
        (x1, y1, x2, y2) = coords
        x1, y1 = x1 * ITEM_SIZE, y1 * ITEM_SIZE
        x2, y2 = x2 * ITEM_SIZE - x1, y2 * ITEM_SIZE - y1
        surf = data.board.subsurface((x1, y1, x2, y2))
        self.background.blit(surf, (x1 + 24, y1 + 24))

    def flip(self):
        self.window.blit(self.background, (0, 0))
        pygame.display.flip()

    def play(self, sound):
        if self.have_sound and settings.get("sfx"):
            data.wav[sound].play()

    def toggle_fullscreen(self):
        self.play("whip")
        if settings.get("fullscreen"):
            settings.set("fullscreen", False)
            f = 0
        else:
            settings.set("fullscreen", True)
            f = pygame.FULLSCREEN
        settings.save()
        if platform == "win32":
            self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), f)
        else:
            pygame.display.toggle_fullscreen()

    def toggle_sfx(self):
        self.play("whip")
        settings.set("sfx", not settings.get("sfx"))
        settings.save()
        self.play("whip")

    def toggle_music(self):
        flag = settings.get("music")
        settings.set("music", not flag)
        settings.save()
        self.play("whip")
        if flag:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()


class Fonter:
    def __init__(self, size=50):
        # Keep 50 items in our cache, we need 31 for the high scores
        self.cache = []
        self.size = size

    def render(self, msg, size, color=(255, 255, 255)):
        for i, (m, s, c, t) in enumerate(self.cache):
            if s == size and m == msg and c == color:
                del self.cache[i]
                self.cache.append((m, s, c, t))
                return t
        font = pygame.font.Font(None, size * 2)
        delta = 2 + size // 8
        black = font.render(msg, 2, (0, 0, 0))
        w, h = black.get_size()
        text = pygame.Surface((w + delta, h + delta)).convert_alpha()
        text.fill((0, 0, 0, 0))
        for x, y in [(5, 5), (6, 3), (5, 1), (3, 0), (1, 1), (0, 3), (1, 5), (3, 6)]:
            text.blit(black, (x * delta // 6, y * delta // 6))
        white = font.render(msg, 2, color)
        text.blit(white, (delta // 2, delta // 2))
        text = pygame.transform.rotozoom(text, 0.0, 0.5)
        self.cache.append((msg, size, color, text))
        if len(self.cache) > self.size:
            self.cache.pop(0)
        return text


class Game:
    # Nothing here yet
    def __init__(self, type=GAME_CLASSIC):
        self.type = type
        self.difficulty = settings.get("difficulty")
        self.items = settings.get("items")
        self.needed = [0] * ITEMS
        self.done = [0] * ITEMS
        self.bonus_list = []
        self.blink_list = {}
        self.disappear_list = []
        self.surprised_list = []
        self.clicks = []
        self.select = None
        self.switch = None
        self.score = 0
        self.lost_timer = 0
        self.lost = False
        self.extra_offset = [[(0, 0)] * BOARD_WIDTH for x in range(BOARD_HEIGHT)]
        self.win_timer = 0
        self.warning_timer = 0
        self.switch_timer = 0
        self.level_timer = SCROLL_DELAY // 2
        self.board_timer = 0
        self.missed = False
        self.check_moves = False
        self.will_play = None
        self.paused = False
        self.splash = True
        self.pause_bitmap = None
        self.play_again = False
        self.eyes = 3
        self.lucky = -1
        self.show_move = False
        self.level = 1
        self.speed = 1
        self.new_level()
        self.oldticks = pygame.time.get_ticks()

    def get_random(self, no_special=False):
        if not no_special and randint(0, SPECIAL_FREQ) == 0:
            return ITEM_SPECIAL
        return randint(0, self.population - 1)

    def new_board(self):
        self.board = [[ITEM_NONE] * (BOARD_WIDTH + 2) for x in range(BOARD_HEIGHT + 2)]
        for y in range(BOARD_HEIGHT):
            while True:
                for x in range(BOARD_WIDTH):
                    self.board[x][y] = self.get_random()
                if not self.get_wins():
                    break
        if self.type == GAME_PUZZLE:
            for t, (x, y) in enumerate(puzzlevels[self.level - 1][3]):
                self.board[x][y] = ITEM_PUZZLE + t
        # self.board[randint(3, 4)][0] = ITEM_METAL

    def fill_board(self):
        for y in range(BOARD_HEIGHT - 1, -1, -1):
            for x in range(BOARD_WIDTH - 1, -1, -1):
                if self.board[x][y] != ITEM_NONE:
                    continue
                for y2 in range(y - 1, -1, -1):
                    if self.board[x][y2] != ITEM_NONE:
                        self.board[x][y] = self.board[x][y2]
                        self.extra_offset[x][y] = (0, ITEM_SIZE * (y2 - y))
                        self.board[x][y2] = ITEM_NONE
                        break
                else:
                    self.board[x][y] = self.get_random()
                    # self.board[(x, y)] = ITEM_METAL
                    self.extra_offset[x][y] = (0, ITEM_SIZE * (-2 - y))

    def get_wins(self):
        wins = []
        # Horizontal
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH - 2):
                a = self.board[x][y]
                if a == ITEM_NONE or a >= ITEMS:
                    continue
                b = self.board[x - 1][y]
                if a == b:
                    continue
                len = 1
                for t in range(1, BOARD_WIDTH - x):
                    if a != self.board[x + t][y]:
                        break
                    len += 1
                if len < 3:
                    continue
                win = []
                for t in range(len):
                    win.append((x + t, y))
                wins.append(win)
        # Horizontal
        for x in range(BOARD_WIDTH):
            for y in range(BOARD_HEIGHT - 2):
                a = self.board[x][y]
                if a == ITEM_NONE or a >= ITEMS:
                    continue
                b = self.board[x][y - 1]
                if a == b:
                    continue
                len = 1
                for t in range(1, BOARD_HEIGHT - y):
                    if a != self.board[x][y + t]:
                        break
                    len += 1
                if len < 3:
                    continue
                win = []
                for t in range(len):
                    win.append((x, y + t))
                wins.append(win)
        return wins

    def list_moves(self):
        checkme = [
            [(+2, 0), (+3, 0)],
            [(+1, -1), (+1, -2)],
            [(+1, -1), (+1, +1)],
            [(+1, +1), (+1, +2)],
        ]
        delta = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                a = self.board[x][y]
                if a >= ITEMS:
                    continue  # We don’t want no special piece
                for [(a1, b1), (a2, b2)] in checkme:
                    for dx, dy in delta:
                        if (
                            a
                            == self.board[x + dx * a1 + dy * b1][y + dx * b1 + dy * a1]
                            and a
                            == self.board[x + dx * a2 + dy * b2][y + dx * b2 + dy * a2]
                        ):
                            yield [(x, y), (x + dx, y + dy)]

    def new_level(self):
        # Compute level data
        if self.type == GAME_TRAINING:
            self.population = self.items
            for i in range(self.population):
                self.done[i] = 0
                self.needed[i] = 0
            self.lucky = -1
            self.time = 1000000
            self.speed = self.difficulty
        elif self.type == GAME_CLASSIC:
            if self.level < 7:
                self.population = 7
            else:
                self.population = 8
            for i in range(self.population):
                self.done[i] = 0
                if self.level < 10:
                    self.needed[i] = self.level + 2
                else:
                    self.needed[i] = 0  # level 10 is the highest
            self.lucky = self.get_random(no_special=True)
            self.time = 1000000
            self.speed = self.level
        elif self.type == GAME_PUZZLE:
            self.population = puzzlevels[self.level - 1][0]
            for i in range(self.population):
                self.done[i] = 0
                self.needed[i] = 0
            self.lucky = -1
            self.time = 1000000
            self.speed = puzzlevels[self.level - 1][1]
        self.angry_items = -1
        self.new_board()

    def check_puzzle(self):
        c = [None] * 4
        for x, y in [(x, y) for x in range(BOARD_WIDTH) for y in range(BOARD_HEIGHT)]:
            t = self.board[x][y]
            if t >= ITEM_PUZZLE:
                c[t - ITEM_PUZZLE] = (x, y)
        p = puzzlevels[self.level - 1][2]
        if p == "2x1":
            if c[0][0] + 1 == c[1][0] and c[0][1] == c[1][1]:
                return 1
            if c[0][1] == c[1][1] == BOARD_HEIGHT - 1 and c[0][0] > c[1][0]:
                return -1
        elif p == "3x1":
            if (
                c[0][0] + 1 == c[1][0]
                and c[0][0] + 2 == c[2][0]
                and c[0][1] == c[1][1] == c[2][1]
            ):
                return 1
            if c[0][1] == c[1][1] == BOARD_HEIGHT - 1 and c[0][0] > c[1][0]:
                return -1
            if c[0][1] == c[2][1] == BOARD_HEIGHT - 1 and c[0][0] > c[2][0]:
                return -1
            if c[1][1] == c[2][1] == BOARD_HEIGHT - 1 and c[1][0] > c[2][0]:
                return -1
        elif p == "1x2":
            if c[0][0] == c[1][0] and c[0][1] + 1 == c[1][1]:
                return 1
            if c[0][1] == BOARD_HEIGHT - 1:
                return -1
        elif p == "1x3":
            if (
                c[0][0] == c[1][0] == c[2][0]
                and c[0][1] + 1 == c[1][1]
                and c[0][1] + 2 == c[2][1]
            ):
                return 1
            if c[0][1] >= BOARD_HEIGHT - 2:
                return -1
            if c[1][1] == BOARD_HEIGHT - 1:
                return -1
        elif p == "2x2":
            if (
                c[0][0] + 1 == c[1][0]
                and c[0][1] == c[1][1]
                and c[0][0] == c[2][0]
                and c[0][1] + 1 == c[2][1]
                and c[1][0] == c[3][0]
                and c[1][1] + 1 == c[3][1]
            ):
                return 1
            if c[0][1] == BOARD_HEIGHT - 1 or c[1][1] == BOARD_HEIGHT - 1:
                return -1
            if c[0][1] == c[1][1] == BOARD_HEIGHT - 2 and c[0][0] > c[1][0]:
                return -1
            if c[2][1] == c[3][1] == BOARD_HEIGHT - 1 and c[2][0] > c[3][0]:
                return -1
        return 0

    def board_draw(self):
        # Draw checkered board
        system.blit(data.board, (24, 24))
        # Have a random piece blink
        c = randint(0, BOARD_WIDTH - 1), randint(0, BOARD_HEIGHT - 1)
        if randint(0, 5) == 0 and c not in self.blink_list:
            self.blink_list[c] = 5
        # Handle special scrolling cases
        if self.level_timer:
            timer = self.level_timer
        elif self.board_timer:
            timer = self.board_timer
        else:
            timer = 0
        if timer > SCROLL_DELAY // 2:
            global_xoff = 0
            yoff = (SCROLL_DELAY - timer) * (SCROLL_DELAY - timer)
            global_yoff = yoff * 50 * 50 // SCROLL_DELAY // SCROLL_DELAY
        elif timer > 0:
            global_xoff = 0
            yoff = -timer * timer
            global_yoff = yoff * 50 * 50 // SCROLL_DELAY // SCROLL_DELAY
        else:
            global_xoff = 0
            global_yoff = 0
        if self.switch_timer:
            x1, y1 = data.board2screen(self.select)
            x2, y2 = data.board2screen(self.switch)
            t = self.switch_timer * 1.0 / SWITCH_DELAY
        for i, j in [(x, y) for x in range(BOARD_WIDTH) for y in range(BOARD_HEIGHT)]:
            # Don’t print pieces for last frame
            if self.lost_timer == 1:
                break
            # Don’t print empty slots
            n = self.board[i][j]
            if n == ITEM_NONE:
                continue
            # Decide the coordinates
            if (i, j) == self.switch and self.switch_timer:
                x, y = x2 * t + x1 * (1 - t), y2 * t + y1 * (1 - t)
            elif (i, j) == self.select and self.switch_timer:
                x, y = x1 * t + x2 * (1 - t), y1 * t + y2 * (1 - t)
            else:
                x, y = data.board2screen((i, j))
            xoff, yoff = self.extra_offset[i][j]
            if self.lost_timer:
                d = LOST_DELAY - self.lost_timer
                xoff += (i * 2 - 7) * 4 * d // LOST_DELAY
                yoff += (j * 2 - 7) * 4 * d // LOST_DELAY
                xoff += (j * 2 - 7) * 4 * d // LOST_DELAY
                yoff += (-i * 2 + 7) * 4 * d // LOST_DELAY
                xoff += randint(0, d) - randint(0, d)
                yoff += randint(0, d) - randint(0, d)
                self.extra_offset[i][j] = xoff, yoff
            elif yoff and self.win_timer:
                yoff = yoff * (self.win_timer - 1) // (WIN_DELAY * 2 // 3)
                self.extra_offset[i][j] = xoff, yoff
            xoff += global_xoff
            yoff += global_yoff
            # Decide the shape
            if n == ITEM_SPECIAL:
                shape = data.special[monsterz.timer % self.population]
            elif n == ITEM_METAL:
                shape = data.metal
            elif n >= ITEM_PUZZLE:
                shape = data.puzzle[puzzlevels[self.level - 1][2]][n - ITEM_PUZZLE]
            elif self.level_timer and self.level_timer < SCROLL_DELAY // 2:
                shape = data.blink[n]
            elif (
                (i, j) in self.surprised_list
                or self.board_timer > SCROLL_DELAY // 2
                or self.level_timer > SCROLL_DELAY // 2
            ):
                shape = data.surprise[n]
            elif (i, j) in self.disappear_list:
                shape = data.exploded[n]
            elif n == self.angry_items:
                shape = data.angry[n]
            elif (i, j) in self.blink_list:
                shape = data.blink[n]
                self.blink_list[i, j] -= 1
                if self.blink_list[i, j] == 0:
                    del self.blink_list[i, j]
            else:
                shape = data.normal[n]
            # Remember the selector coordinates
            if (
                (i, j) == self.select
                and not self.missed
                or (i, j) == self.switch
                and self.missed
            ):
                select_coord = (x, y)
                shape = data.blink[n]  # Not sure if it looks nice
            # Print the shit
            self.piece_draw(shape, (x + xoff, y + yoff))
        # Draw selector if necessary
        if self.select:
            system.blit(data.selector, select_coord)

    def piece_draw(self, sprite, pos):
        (x, y) = pos
        width = ITEM_SIZE
        crop = sprite.subsurface
        # Constrain X
        if x < 10 - ITEM_SIZE or x > 24 + 8 * ITEM_SIZE + 14:
            return
        elif x < 10:
            delta = 10 - x
            sprite = crop((delta, 0, ITEM_SIZE - delta, ITEM_SIZE))
            crop = sprite.subsurface
            x += delta
            width -= delta
        elif x > 24 + 7 * ITEM_SIZE + 14:
            delta = x - 24 - 7 * ITEM_SIZE - 14
            sprite = crop((0, 0, ITEM_SIZE - delta, ITEM_SIZE))
            crop = sprite.subsurface
            width -= delta
        # Constrain Y
        if y < 10 - ITEM_SIZE or y > 24 + 8 * ITEM_SIZE + 14:
            return
        elif y < 10:
            delta = 10 - y
            sprite = crop((0, delta, width, ITEM_SIZE - delta))
            y += delta
        elif y > 24 + 7 * ITEM_SIZE + 14:
            delta = y - 24 - 7 * ITEM_SIZE - 14
            sprite = crop((0, 0, width, ITEM_SIZE - delta))
        system.blit(sprite, (x, y))

    psat = [0] * 2
    parea = None

    def game_draw(self):
        # Draw timebar
        timebar = pygame.Surface((406, 32)).convert_alpha()
        timebar.fill((0, 0, 0, 155))
        w = 406 * self.time // 2000000
        if w > 0:
            if self.warning_timer:
                ratio = (
                    1.0 * abs(2 * self.warning_timer - WARNING_DELAY) // WARNING_DELAY
                )
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
        except:
            pass
        else:
            for x in range(4):
                for y, p in enumerate(alpha[x]):
                    alpha[x][y] = p * x // 4
                for y, p in enumerate(alpha[406 - x - 1]):
                    alpha[406 - x - 1][y] = p * x // 4
            for col in alpha:
                l = len(col)
                for y in range(4):
                    col[y] = col[y] * y // 4
                    col[l - y - 1] = col[l - y - 1] * y // 4
                del col
            del alpha
            timebar.unlock()
        system.blit(timebar, (13, 436))
        if self.lost_timer == -1:
            # Print play again message
            text = fonter.render("GAME OVER", 80)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w // 2, 24 + 192 - h // 2))
            if self.score < 5000:
                msg = "YUO = TEH L0SER"
            elif self.score < 15000:
                msg = "WELL, AT LEAST YOU TRIED"
            elif self.score < 30000:
                msg = "W00T! YUO IS TEH R0X0R"
            else:
                msg = "ZOMFG!!!111!!! YUO PWND!!!%$#@%@#"
            text = fonter.render(msg, 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w // 2, 24 + 240 - h // 2))
        elif self.paused:
            # Draw pause message
            system.blit(self.pause_bitmap, (72, 24))
            text = fonter.render("PAUSED", 120)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w // 2, 24 + 336 - h // 2))
        elif self.splash:
            if self.type == GAME_TRAINING:
                msg = "TRAINING"
            elif self.type in [GAME_CLASSIC, GAME_PUZZLE]:
                msg = "LEVEL " + str(self.level)
            text = fonter.render(msg, 60)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w // 2, 24 + 144 - h // 2))
            if self.needed[0]:
                msg = "MONSTERS NEEDED: " + str(self.needed[0])
            elif self.type == GAME_PUZZLE:
                msg = "PUZZLE LEVEL"
            else:
                msg = "UNLIMITED LEVEL"
            text = fonter.render(msg, 40)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w // 2, 24 + 240 - h // 2))
            if self.lucky != -1:
                text = fonter.render("LUCKY MONSTER:", 40)
                w, h = text.get_rect().size
                system.blit(text, (192 - w // 2 - 8, 24 + 288 - h // 2))
                system.blit(data.normal[self.lucky], (192 + w // 2, 288))
        elif self.lost_timer != -1:
            # Draw pieces
            self.board_draw()
            # Print new level stuff
            if self.level_timer > SCROLL_DELAY // 2:
                if self.type == GAME_PUZZLE:
                    text = fonter.render("COMPLETED!", 80)
                else:
                    text = fonter.render("LEVEL UP!", 80)
                w, h = text.get_rect().size
                system.blit(text, (24 + 192 - w // 2, 24 + 192 - h // 2))
            # When no more moves are possible
            if self.board_timer > SCROLL_DELAY // 2:
                text = fonter.render("NO MORE MOVES!", 60)
                w, h = text.get_rect().size
                system.blit(text, (24 + 192 - w // 2, 24 + 192 - h // 2))
            # Print bonus
            for b in self.bonus_list:
                if b[2]:
                    text = fonter.render(str(b[1]), 48, rainbow[monsterz.timer % 6])
                else:
                    text = fonter.render(str(b[1]), 36)
                w, h = text.get_rect().size
                x, y = data.board2screen(b[0])
                system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
            # Print hint arrow
            if self.show_move:
                lookup = [0, 1, 5, 16, 27, 31, 32, 31, 27, 16, 5, 1]
                for (src, dst) in self.list_moves():
                    x1, y1 = data.board2screen(src)
                    x2, y2 = data.board2screen(dst)
                    delta = lookup[monsterz.timer % 12]
                    x = -32 + (x1 * delta + x2 * (32 - delta)) // 32
                    y = 32 + (y1 * delta + y2 * (32 - delta)) // 32
                    system.blit(data.arrow, (x, y))
                    break  # Only show one move
        # Print score
        text = fonter.render(str(self.score), 60)
        w, h = text.get_rect().size
        system.blit(text, (624 - w, 10))
        # Print done/needed
        for i in range(self.population):
            x = 440 + i // 4 * 90
            y = 64 + (i % 4) * 38
            if self.done[i] >= self.needed[i]:
                surf = data.tiny[i]
            else:
                surf = data.shaded[i]
            system.blit(surf, (x, y))
            if i == self.lucky:
                text = fonter.render(str(self.done[i]), 36, rainbow[monsterz.timer % 6])
            else:
                text = fonter.render(str(self.done[i]), 36)
            system.blit(text, (x + 44, y + 2))
        # Print eyes
        for i in range(3):
            x, y = 440 + 36 * i, 252
            if i < self.eyes:
                system.blit(data.eye, (x, y))
            else:
                system.blit(data.shadeye, (x, y))
        # Print pause and abort buttons
        if self.lost_timer != -1:
            r = (127, 0, 255)
            if self.paused:
                led, color = data.led_on, (255, 255, 255)
            else:
                led, color = data.led_off, (180, 150, 127)
            c = list(map(lambda a, b: b - (b - a) * self.psat[0] // 255, r, color))
            system.blit(led, (440, 298))
            system.blit(fonter.render("PAUSE", 30, c), (470, 296))
            color = (180, 150, 127)
            c = list(map(lambda a, b: b - (b - a) * self.psat[1] // 255, r, color))
            system.blit(fonter.render("ABORT", 30, c), (470, 326))
            for x in range(2):
                if self.psat[x]:
                    self.psat[x] = self.psat[x] * 8 // 10

    def pause(self):
        # TODO: prevent cheating by not allowing less than 1 second
        # since the last pause
        self.paused = not self.paused
        system.play("whip")
        if self.paused:
            i = self.get_random(no_special=True)
            # self.pause_bitmap = pygame.transform.scale(data.normal[i], (6 * ITEM_SIZE, 6 * ITEM_SIZE))
            # self.pause_bitmap = pygame.transform.rotozoom(data.normal[i], 0.0, 6.0)
            self.pause_bitmap = data.bigtiles.subsurface((0, i * 288, 288, 288))
        else:
            del self.pause_bitmap
        self.clicks = []

    def update(self):
        ticks = pygame.time.get_ticks()
        delta = (ticks - self.oldticks) * 450 // (12 - self.speed)
        self.oldticks = ticks
        # If paused, do nothing
        if self.paused:
            return
        if self.splash:
            return
        # Resolve winning moves and chain reactions
        if self.board_timer:
            self.board_timer -= 1
            if self.board_timer is SCROLL_DELAY // 2:
                self.new_board()
            elif self.board_timer == 0:
                system.play("boing")
                self.check_moves = True  # Need to check again
            return
        if self.lost_timer:  # FIXME: this is quite a mess...
            if self.lost:
                return  # Continue forever
            if self.lost_timer == -1:
                if self.type == GAME_TRAINING:
                    settings.new_score("TRAINING", self.score, self.level)
                elif self.type == GAME_CLASSIC:
                    settings.new_score("CLASSIC", self.score, self.level)
                elif self.type == GAME_PUZZLE:
                    settings.new_score("PUZZLE", self.score, self.level)
                self.lost = True
                return
            self.lost_timer -= 1
            if self.lost_timer == 0:
                self.lost_timer = -1
            return
        if self.switch_timer:
            self.switch_timer -= 1
            if self.switch_timer == 0:
                x1, y1 = self.select
                x2, y2 = self.switch
                self.board[x1][y1], self.board[x2][y2] = (
                    self.board[x2][y2],
                    self.board[x1][y1],
                )
                if self.missed:
                    self.clicks = []
                    self.missed = False
                else:
                    self.wins = self.get_wins()
                    if not self.wins:
                        system.play("whip")
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
            if self.level_timer is SCROLL_DELAY // 2:
                self.level += 1
                if self.type == GAME_PUZZLE:
                    if self.level > len(puzzlevels):
                        self.lost_timer = -1
                        return
                self.new_level()
                self.splash = True
            elif self.level_timer == 0:
                system.play("boing")
                self.blink_list = {}
                self.check_moves = True
            return
        if self.win_timer:
            self.win_timer -= 1
            if self.win_timer == WIN_DELAY - 1:
                system.play("duh")
                for w in self.wins:
                    for x, y in w:
                        self.surprised_list.append((x, y))
            elif self.win_timer == WIN_DELAY * 4 // 5:
                system.play("pop")
                self.scorebonus = 0
                self.timebonus = 0
                for w in self.wins:
                    if self.board[w[0][0]][w[0][1]] == self.lucky:
                        points = 20
                        lucky = True
                    else:
                        points = 10
                        lucky = False
                    if self.type != GAME_PUZZLE:
                        points *= self.level
                    if len(w) >= 3:
                        points *= 2 ** (self.win_iter + len(w) - 3)
                    self.scorebonus += points
                    self.timebonus += 45000 * len(w)
                    x2, y2 = 0.0, 0.0
                    for x, y in w:
                        x2 += x
                        y2 += y
                    self.bonus_list.append(
                        [(x2 // len(w), y2 // len(w)), points, lucky]
                    )
                self.disappear_list = self.surprised_list
                self.surprised_list = []
            elif self.win_timer == WIN_DELAY * 3 // 5:
                for x, y in self.disappear_list:
                    if self.board[x][y] != ITEM_NONE:
                        self.done[self.board[x][y]] += 1
                        self.board[x][y] = ITEM_NONE
                if self.angry_items == -1:
                    unfinished = 0
                    for i in range(self.population):
                        if self.done[i] < self.needed[i]:
                            unfinished += 1
                            angry = i
                    if unfinished == 1:
                        system.play("grunt")
                        self.angry_items = angry
                self.disappear_list = []
                self.bonus_list = []
            elif self.win_timer == WIN_DELAY * 2 // 5:
                self.time += self.timebonus
                if self.time > 2000000:
                    self.time = 2000000
                # Get a new eye each 10000 points, but no more than 3
                if (self.score % 10000) + self.scorebonus >= 10000 and self.eyes < 3:
                    self.eyes += 1
                self.score += self.scorebonus
                self.fill_board()
            elif self.win_timer == 0:
                system.play("boing")
                self.wins = self.get_wins()
                if self.wins:
                    self.win_timer = WIN_DELAY
                    self.win_iter += 1
                elif self.type == GAME_PUZZLE:
                    # Check for puzzle completion
                    status = self.check_puzzle()
                    if status < 0:
                        self.score -= 100
                        system.play("ding")
                        self.board_timer = SCROLL_DELAY
                    elif status > 0:
                        if (self.score % 10000) + 2000 >= 10000 and self.eyes < 3:
                            self.eyes += 1
                        self.score += 2000
                        system.play("applause")
                        self.level_timer = SCROLL_DELAY
                    else:
                        self.check_moves = True
                elif self.needed[0]:
                    # Check for new level
                    for i in range(self.population):
                        if self.done[i] < self.needed[i]:
                            self.check_moves = True
                            break
                    else:
                        system.play("applause")
                        self.select = None
                        self.level_timer = SCROLL_DELAY
                else:
                    self.check_moves = True
            return
        if self.show_move and (monsterz.timer % 6) == 0:
            system.play("click")
        if self.warning_timer:
            if self.time <= 200000:
                self.warning_timer -= 1
            else:
                self.warning_timer = 0
        elif self.time <= 200000:
            system.play("warning")
            self.warning_timer = WARNING_DELAY
        # Update time
        if self.type in [GAME_TRAINING, GAME_CLASSIC, GAME_PUZZLE]:
            self.time -= delta
            if self.time <= 0:
                system.play("laugh")
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
                            if self.board[(x, y)] == ITEM_SPECIAL:
                                special = (x, y)
                                break
                        if special:
                            break
                    if special:
                        incomplete = 0
                        for i in range(self.population):
                            if self.done[i] >= self.needed[i]:
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
                        if (
                            self.done[color] >= min
                            or self.done[color] >= self.needed[color]
                        ):
                            self.will_play = move
                            min = self.done[color]
                self.ai_timer = 15 - self.level
            if self.ai_timer == (15 - self.level) // 2:
                self.clicks.append(self.will_play[0])
            elif self.ai_timer == 0:
                self.clicks.append(self.will_play[1])
                self.will_play = None
            self.ai_timer -= 1
        # Handle moves from the player or the AI
        if self.clicks:
            i, j = self.clicks.pop(0)
            if (i, j) == (99, 99):
                system.play("whip")
                self.select = None
                self.eyes -= 1
                # show_move is removed when we click, or when we lose
                self.show_move = True
                return
            self.show_move = False
            if self.select:
                if self.select == (i, j):
                    system.play("click")
                    self.select = None
                    return
                x1, y1 = self.select
                x2, y2 = i, j
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    return
                system.play("whip")
                self.switch = i, j
                self.switch_timer = SWITCH_DELAY
            elif self.board[i][j] == ITEM_METAL:
                pass
            elif self.board[i][j] >= ITEM_PUZZLE:
                pass
            elif self.board[i][j] == ITEM_SPECIAL:
                # Deal with the special block
                self.wins = []
                target = monsterz.timer % self.population
                self.board[i][j] = target
                for x, y in [
                    (x, y) for x in range(BOARD_WIDTH) for y in range(BOARD_HEIGHT)
                ]:
                    if self.board[x][y] == target:
                        self.wins.append([(x, y)])
                self.win_iter = 0
                self.win_timer = WIN_DELAY
            else:
                system.play("click")
                self.select = i, j
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
            elif self.status == STATUS_NEW:
                iterator = self.iterate_new
            elif self.status == STATUS_GAME:
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
        except:
            pass
        else:
            for x in range(10):
                for y, p in enumerate(alpha[x]):
                    alpha[x][y] = p * x // 12
                for y, p in enumerate(alpha[406 - x - 1]):
                    alpha[406 - x - 1][y] = p * x // 12
            del alpha
            scroll.unlock()
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
            system.play("click")
        self.garea = garea
        system.blit(data.background, (0, 0))
        # Print various buttons
        r = (127, 0, 255)
        if system.have_sound:
            if settings.get("sfx"):
                led, color = data.led_on, (255, 255, 255)
            else:
                led, color = data.led_off, (180, 150, 127)
            c = list(map(lambda a, b: b - (b - a) * self.gsat[0] // 255, r, color))
            system.blit(led, (440, 378))
            system.blit(fonter.render("SOUND FX", 30, c), (470, 376))
            if settings.get("music"):
                led, color = data.led_on, (255, 255, 255)
            else:
                led, color = data.led_off, (180, 150, 127)
            c = list(map(lambda a, b: b - (b - a) * self.gsat[1] // 255, r, color))
            system.blit(led, (440, 408))
            system.blit(fonter.render("MUSIC", 30, c), (470, 406))
        if settings.get("fullscreen"):
            led, color = data.led_on, (255, 255, 255)
        else:
            led, color = data.led_off, (180, 150, 127)
        c = list(map(lambda a, b: b - (b - a) * self.gsat[2] // 255, r, color))
        system.blit(led, (440, 438))
        system.blit(fonter.render("FULLSCREEN", 30, c), (470, 436))
        for x in range(3):
            if self.gsat[x]:
                self.gsat[x] = self.gsat[x] * 8 // 10

    def generic_event(self, event):
        if event.type == QUIT:
            self.status = STATUS_QUIT
            return True
        elif event.type == pygame.KEYDOWN and event.key == K_f:
            system.toggle_fullscreen()
            return True
        if system.have_sound:
            if event.type == pygame.KEYDOWN and event.key == K_s:
                system.toggle_sfx()
                return True
            elif event.type == pygame.KEYDOWN and event.key == K_m:
                system.toggle_music()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN:
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

    wander_monster = randint(0, ITEMS-1)
    wander_x = None
    wander_y = 0

    def wanderer_draw(self):
        if self.wander_x == None:
            if randint(0, 30) == 1:
                self.wander_monster = (self.wander_monster+1) % ITEMS
                self.wander_y = randint(20, SCREEN_HEIGHT-ITEM_SIZE-20)
                self.wander_x = -ITEM_SIZE
            return
        if randint(0, 10) == 1:
            monster = data.blink[self.wander_monster]
        else:
            monster = data.normal[self.wander_monster]
        system.blit(monster, (self.wander_x, self.wander_y))
        if self.wander_x < SCREEN_WIDTH/3 or self.wander_x > (SCREEN_WIDTH/3)*2:
            self.wander_x += randint(4, 8)
            self.wander_y += randint(-2, 2)
        else:
            self.wander_x += 3
            self.wander_y += randint(-1, 1)
        if self.wander_x > SCREEN_WIDTH:
            self.wander_x = None

    msat = [0] * 4
    marea = None

    def iterate_menu(self):
        self.generic_draw()
        self.copyright_draw()
        colors = [[0, 255, 0], [255, 0, 255], [255, 255, 0], [255, 0, 0]]
        shapes = [2, 3, 4, 0]
        messages = ["NEW GAME", "HELP", "SCORES", "QUIT"]
        x, y = data.screen2board(pygame.mouse.get_pos())
        if y == 4 and 2 <= x <= 5:
            marea = STATUS_NEW
            self.msat[0] = 255
        elif y == 5 and 2 <= x <= 5:
            marea = STATUS_HELP
            self.msat[1] = 255
        elif y == 6 and 2 <= x <= 5:
            marea = STATUS_SCORES
            self.msat[2] = 255
        elif y == 7 and 2 <= x <= 5:
            marea = STATUS_QUIT
            self.msat[3] = 255
        else:
            marea = None
        if marea and marea != self.marea:
            system.play("click")
        self.marea = marea
        # Print logo and menu
        w, h = data.logo.get_size()
        system.blit(data.logo, (24 + 192 - w // 2, 24 + 96 - h // 2))
        self.wanderer_draw()
        for x in range(4):
            if self.msat[x] > 180:
                monster = data.surprise[shapes[x]]
            elif self.msat[x] > 40:
                monster = data.normal[shapes[x]]
            else:
                monster = data.blink[shapes[x]]
            system.blit(monster, data.board2screen((1, 4 + x)))
            c = [255 - (255 - a) * self.msat[x] // 255 for a in colors[x]]
            text = fonter.render(messages[x], 48, c)
            w, h = text.get_rect().size
            system.blit(text, (24 + 102, 24 + 216 + ITEM_SIZE * x - h // 2))
            if self.msat[x]:
                self.msat[x] = self.msat[x] * 8 // 10
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                system.play("whip")
                self.status = STATUS_QUIT
                return
            elif event.type == pygame.KEYDOWN and event.key == K_n:
                system.play("whip")
                self.status = STATUS_NEW
                return
            elif event.type == pygame.KEYDOWN and event.key == K_h:
                system.play("whip")
                self.status = STATUS_HELP
                return
            elif event.type == pygame.KEYDOWN and event.key == K_q:
                system.play("whip")
                self.status = STATUS_QUIT
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and marea is not None:
                system.play("whip")
                self.status = marea
                return

    nsat = [0] * 8
    narea = None

    def iterate_new(self):
        items = settings.get("items")
        difficulty = settings.get("difficulty")
        self.generic_draw()
        self.copyright_draw()
        messages = ["CLASSIC", "PUZZLE", "", "TRAINING"]
        x, y = data.screen2board(pygame.mouse.get_pos())
        if y == 2 and 1 <= x <= 6:
            narea = GAME_CLASSIC
            self.nsat[0] = 255
        elif y == 3 and 1 <= x <= 5:
            narea = GAME_PUZZLE
            self.nsat[1] = 255
        # elif y == 4 and 1 <= x <= 4:
        #     narea = GAME_QUEST
        #     self.nsat[2] = 255
        elif y == 5 and 1 <= x <= 4:
            narea = GAME_TRAINING
            self.nsat[3] = 255
        elif (x, y) == (1, 6):
            narea = ACTION_LESSMONSTERZ
            self.nsat[4] = 255
        elif (x, y) == (6, 6):
            narea = ACTION_MOREMONSTERZ
            self.nsat[5] = 255
        elif (x, y) == (1, 7):
            narea = ACTION_LESSLEVEL
            self.nsat[6] = 255
        elif (x, y) == (6, 7):
            narea = ACTION_MORELEVEL
            self.nsat[7] = 255
        else:
            narea = None
        if narea is not None and narea != self.narea:
            system.play("click")
        self.narea = narea
        # Print menu
        text = fonter.render("GAME TYPE", 60)
        w, h = text.get_rect().size
        system.blit(text, (24 + 192 - w // 2, 24 + 24 - h // 2))
        for i in range(4):
            c = [255 - (255 - a) * self.nsat[i] // 255 for a in [127, 0, 255]]
            text = fonter.render(messages[i], 48, c)
            w, h = text.get_rect().size
            system.blit(
                text, (24 + ITEM_SIZE * 4 - w // 2, 24 + 120 + ITEM_SIZE * i - h // 2)
            )
            if self.nsat[i]:
                self.nsat[i] = self.nsat[i] * 8 // 10
        for i in range(4, 8):
            c = [255 - (255 - a) * self.nsat[i] // 255 for a in [127, 0, 255]]
            if i % 2:
                img = data.led_more
                x = 320
            else:
                img = data.led_less
                x = 88
            y = 36 + ITEM_SIZE * (6 + (i - 4) // 2)
            system.blit(img, (x, y))
            if self.nsat[i]:
                self.nsat[i] = self.nsat[i] * 8 // 10
        # Print wanted monsterz
        for i in range(items):
            system.blit(
                data.normal[i],
                (24 + 96 + ITEM_SIZE * 3 * i // (items - 1), 24 + ITEM_SIZE * 6),
            )
        text = fonter.render("DIFFICULTY " + str(difficulty), 36)
        w, h = text.get_rect().size
        system.blit(text, (24 + 192 - w // 2, 24 + ITEM_SIZE * 7 + 24 - h // 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                system.play("whip")
                self.status = STATUS_MENU
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and narea is not None and narea >= 10:
                system.play("whip")
                if narea == ACTION_MOREMONSTERZ:
                    if items < 8:
                        settings.set("items", items + 1)
                elif narea == ACTION_LESSMONSTERZ:
                    if items > 4:
                        settings.set("items", items - 1)
                if narea == ACTION_MORELEVEL:
                    if difficulty < 10:
                        settings.set("difficulty", difficulty + 1)
                elif narea == ACTION_LESSLEVEL:
                    if difficulty > 1:
                        settings.set("difficulty", difficulty - 1)
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and narea is not None:
                system.play("whip")
                self.game = Game(type=narea)
                self.status = STATUS_GAME
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
            system.play("click")
        self.game.parea = parea
        # Draw screen
        self.generic_draw()
        # Check for new moves
        if self.game.check_moves:
            for move in self.game.list_moves():
                break
            else:
                if self.game.type == GAME_PUZZLE:
                    self.game.score -= 50
                system.play("ding")
                self.game.board_timer = SCROLL_DELAY
            self.game.check_moves = False
            self.game.clicks = []
        self.game.game_draw()
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                system.play("whip")
                if self.game.lost:
                    self.status = STATUS_MENU
                    return
                self.game.lost_timer = -1
                return
            elif (
                event.type == pygame.KEYDOWN
                and (event.key == K_p or event.key == K_SPACE)
                and self.game.lost_timer >= 0
            ):
                self.game.pause()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if self.game.lost_timer >= 0:
                    if 440 < x < 440 + 180 and 298 < y < 298 + 24:
                        system.play("whip")
                        self.game.pause()
                        return
                    elif 440 < x < 440 + 180 and 328 < y < 328 + 24:
                        system.play("whip")
                        self.game.lost_timer = -1
                        return
                if self.game.splash:
                    system.play("whip")
                    self.game.splash = False
                    return
                if self.game.lost_timer == -1:
                    system.play("whip")
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
        text = fonter.render("INSTRUCTIONS (" + str(self.page) + ")", 60)
        w, h = text.get_rect().size
        system.blit(text, (24 + 192 - w // 2, 24 + 24 - h // 2))
        if self.page == 1:
            # Explanation 1
            text = fonter.render("SWAP ADJACENT MONSTERS TO CREATE", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h // 2))
            text = fonter.render("ALIGNMENTS OF THREE OR MORE. NEW", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h // 2))
            text = fonter.render("MONSTERS WILL FILL THE HOLES.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h // 2))
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
            text = fonter.render("10", 36)
            w, h = text.get_rect().size
            x, y = data.board2screen((7, 4))
            system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
            # Explanation 2
            text = fonter.render("CREATE CHAIN REACTIONS TO GET TWICE", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 348 - h // 2))
            text = fonter.render("AS MANY POINTS, THEN 4x, 8x ETC.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 372 - h // 2))
        elif self.page == 2:
            # Explanation 1
            text = fonter.render("THE LUCKY MONSTER EARNS YOU TWICE", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h // 2))
            text = fonter.render("AS MANY POINTS AS OTHER MONSTERS.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h // 2))
            shape = data.special[self.timer % 7]
            # Print done/needed
            system.blit_board((0, 3, 4, 5))
            system.blit(data.normal[3], data.board2screen((0, 3)))
            system.blit(data.surprise[1], data.board2screen((1, 3)))
            system.blit(data.surprise[1], data.board2screen((2, 3)))
            system.blit(data.surprise[1], data.board2screen((3, 3)))
            system.blit(data.surprise[2], data.board2screen((0, 4)))
            system.blit(data.surprise[2], data.board2screen((1, 4)))
            system.blit(data.surprise[2], data.board2screen((2, 4)))
            system.blit(data.normal[4], data.board2screen((3, 4)))
            system.blit_board((0, 6, 4, 8))
            system.blit(data.normal[3], data.board2screen((0, 6)))
            system.blit(data.exploded[1], data.board2screen((1, 6)))
            system.blit(data.exploded[1], data.board2screen((2, 6)))
            system.blit(data.exploded[1], data.board2screen((3, 6)))
            system.blit(data.exploded[2], data.board2screen((0, 7)))
            system.blit(data.exploded[2], data.board2screen((1, 7)))
            system.blit(data.exploded[2], data.board2screen((2, 7)))
            system.blit(data.normal[4], data.board2screen((3, 7)))
            text = fonter.render("140", 48, rainbow[monsterz.timer % 6])
            w, h = text.get_rect().size
            x, y = data.board2screen((2, 6))
            system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
            text = fonter.render("70", 36)
            w, h = text.get_rect().size
            x, y = data.board2screen((1, 7))
            system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
            for i in range(4):
                surf = data.tiny[i + 1]
                count = 3 + i * 2
                x = 24 + 240 + 4 + i // 2 * 70
                y = 172 + (i % 2) * 38
                for dummy in range(2):
                    system.blit(surf, (x, y))
                    text = fonter.render(str(count), 36)
                    if i == 0:
                        text = fonter.render(
                            str(count), 36, rainbow[monsterz.timer % 6]
                        )
                    else:
                        text = fonter.render(str(count), 36)
                    system.blit(text, (x + 44, y + 2))
                    y = 316 + (i % 2) * 38
                    if i < 2:
                        count += 3
        elif self.page == 3:
            # Explanation 1
            text = fonter.render("YOU CAN ALWAYS PERFORM A VALID MOVE.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h // 2))
            text = fonter.render("WHEN NO MORE MOVES ARE POSSIBLE, YOU", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h // 2))
            text = fonter.render("GET A COMPLETE NEW BOARD.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h // 2))
            # Surprised
            system.blit_board((0, 3, 8, 5))
            for x in range(8):
                system.blit(data.surprise[(x * 3 + 2) % 8], data.board2screen((x, 3)))
                system.blit(data.surprise[(x * 7) % 8], data.board2screen((x, 4)))
            text = fonter.render("NO MORE MOVES!", 60)
            w, h = text.get_rect().size
            system.blit(text, (24 + 192 - w // 2, 24 + 192 - h // 2))
            # Explanation 2
            text = fonter.render("USE THE EYE TO FIND WHERE TO PLAY.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6 + 48, 24 + 300 - h // 2))
            text = fonter.render("EACH 10,000 POINTS YOU GET A NEW", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6 + 48, 24 + 324 - h // 2))
            text = fonter.render("EYE. YOU CAN'T HAVE MORE THAN 3.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6 + 48, 24 + 348 - h // 2))
            system.blit(data.eye, (24 + 6, 24 + 306))
        elif self.page == 4:
            # Explanation 1
            text = fonter.render("WHEN ONLY ONE KIND OF MONSTER IS", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h // 2))
            text = fonter.render("NEEDED TO FINISH THE LEVEL, MONSTERS", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h // 2))
            text = fonter.render("OF THAT KIND GET AN ANGRY FACE.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h // 2))
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
                x = 24 + 240 + 4 + i // 2 * 70
                y = 172 + (i % 2) * 38
                system.blit(surf, (x, y))
                text = fonter.render(str(i * 3), 36)
                system.blit(text, (x + 44, y + 2))
            # Explanation 2
            text = fonter.render("CLICK ON THE BONUS TO REMOVE ALL", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 252 - h // 2))
            text = fonter.render("MONSTERS OF A RANDOM KIND.", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 276 - h // 2))
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
            text = fonter.render("10", 36)
            w, h = text.get_rect().size
            x, y = data.board2screen((4, 7))
            system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
            x, y = data.board2screen((5, 6))
            system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
            x, y = data.board2screen((6, 6))
            system.blit(text, (x + 24 - w // 2, y + 24 - h // 2))
        elif self.page == 5:
            # Explanation 1
            text = fonter.render("IN PUZZLE MODE, PUT TOGETHER THE", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 84 - h // 2))
            text = fonter.render("PUZZLE BY MOVING PIECES AROUND. BE", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 108 - h // 2))
            text = fonter.render("CAREFUL NOT TO GET STUCK!", 24)
            w, h = text.get_rect().size
            system.blit(text, (24 + 6, 24 + 132 - h // 2))
            # Iter 1
            system.blit_board((0, 3, 2, 8))
            system.blit(data.normal[2], data.board2screen((0, 3)))
            system.blit(data.normal[5], data.board2screen((0, 4)))
            system.blit(data.blink[1], data.board2screen((0, 5)))
            system.blit(data.puzzle["2x1"][0], data.board2screen((0, 6)))
            system.blit(data.normal[7], data.board2screen((0, 7)))
            system.blit(data.puzzle["2x1"][1], data.board2screen((1, 3)))
            system.blit(data.normal[1], data.board2screen((1, 4)))
            system.blit(data.normal[4], data.board2screen((1, 5)))
            system.blit(data.normal[1], data.board2screen((1, 6)))
            system.blit(data.normal[3], data.board2screen((1, 7)))
            system.blit(data.selector, data.board2screen((0, 5)))
            # Iter 2
            system.blit_board((3, 3, 5, 8))
            system.blit(data.normal[2], data.board2screen((3, 3)))
            system.blit(data.normal[5], data.board2screen((3, 4)))
            system.blit(data.normal[4], data.board2screen((3, 5)))
            system.blit(data.puzzle["2x1"][0], data.board2screen((3, 6)))
            system.blit(data.normal[7], data.board2screen((3, 7)))
            system.blit(data.puzzle["2x1"][1], data.board2screen((4, 3)))
            system.blit(data.surprise[1], data.board2screen((4, 4)))
            system.blit(data.surprise[1], data.board2screen((4, 5)))
            system.blit(data.surprise[1], data.board2screen((4, 6)))
            system.blit(data.normal[3], data.board2screen((4, 7)))
            system.blit(data.selector, data.board2screen((4, 5)))
            # Iter 2
            system.blit_board((6, 3, 8, 8))
            system.blit(data.normal[2], data.board2screen((6, 3)))
            system.blit(data.normal[5], data.board2screen((6, 4)))
            system.blit(data.normal[4], data.board2screen((6, 5)))
            system.blit(data.puzzle["2x1"][0], data.board2screen((6, 6)))
            system.blit(data.normal[7], data.board2screen((6, 7)))
            system.blit(data.normal[0], data.board2screen((7, 3)))
            system.blit(data.normal[6], data.board2screen((7, 4)))
            system.blit(data.normal[0], data.board2screen((7, 5)))
            system.blit(data.puzzle["2x1"][1], data.board2screen((7, 6)))
            system.blit(data.normal[3], data.board2screen((7, 7)))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                system.play("whip")
                self.status = STATUS_MENU
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                system.play("whip")
                self.page += 1
                if self.page > 5:
                    self.status = STATUS_MENU
                return

    def iterate_scores(self):
        self.generic_draw()
        self.copyright_draw()
        text = fonter.render("HIGH SCORES", 60)
        w, h = text.get_rect().size
        system.blit(text, (24 + 192 - w // 2, 24 + 24 - h // 2))
        # Print our list
        for x in range(10):
            name, score, level = settings.scores["CLASSIC"][x]
            text = fonter.render(str(x + 1) + ". " + name.upper(), 32)
            w, h = text.get_rect().size
            system.blit(text, (24 + 24, 24 + 72 + 32 * x - h // 2))
            text = fonter.render(str(score), 32)
            w, h = text.get_rect().size
            system.blit(text, (24 + 324 - w, 24 + 72 + 32 * x - h // 2))
            text = fonter.render(str(level), 32)
            w, h = text.get_rect().size
            system.blit(text, (24 + 360 - w, 24 + 72 + 32 * x - h // 2))
        # Handle events
        for event in pygame.event.get():
            if self.generic_event(event):
                return
            elif event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                system.play("whip")
                self.status = STATUS_MENU
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                system.play("whip")
                self.status = STATUS_MENU
                return


def version():
    print("monsterz " + VERSION)
    print(
        "Written by Sam Hocevar, music by MenTaLguY, sound effects by Sun Microsystems,"
    )
    print("Inc., Michael Speck, David White and the Battle for Wesnoth project, Mike")
    print("Kershaw and Sam Hocevar.")
    print()
    print("Copyright (C) 2005, 2006 Sam Hocevar <sam@zoy.org>")
    print("          (C) 1998 MenTaLguY <mental@rydia.net>")
    print("          (C) 2002, 2005 Sun Microsystems, Inc.")
    print("          (C) Michael Speck <kulkanie@gmx.net>")
    print("          (C) 2003 by David White <davidnwhite@optusnet.com.au> and the")
    print("              Battle for Wesnoth project")
    print("          (C) Mike Kershaw <dragorn@kismetwireless.net>")

    print(
        "This program is free software; you can redistribute it and/or modify it under"
    )
    print("the terms of the Do What The Fuck You Want To Public License, Version 2, as")
    print("published by Sam Hocevar. See http://sam.zoy.org/wtfpl/ for more details.")
    print("The sound effects are released under their own licences: applause.wav and")
    print("pop.wav are covered by the LGPL, the others are covered by the GPL.")


def usage():
    print("Usage: monsterz [OPTION]...")
    print()
    print("Options")
    print(" -f, --fullscreen   start in full screen mode")
    print(" -h, --help         display this help and exit")
    print(" -m, --nomusic      disable music")
    print(" -s, --nosfx        disable sound effects")
    print("     --outfd <fd>   output scores to file descriptor <fd>")
    print("     --data <dir>   set alternate data directory to <dir>")
    print("     --score <file> set score file to <file>")
    print(" -v, --version      display version information and exit")
    print()
    print("Report bugs or suggestions to <sam@zoy.org>.")


def main():
    from getopt import getopt, GetoptError

    global system, data, settings, fonter, monsterz
    override = {}
    scorefile = None
    sharedir = dirname(argv[0])
    outfd = None
    try:
        longopts = [
            "help",
            "version",
            "music",
            "sound",
            "fullscreen",
            "outfd=",
            "data=",
            "score=",
        ]
        opts = getopt(argv[1:], "hvmsf", longopts)[0]
    except GetoptError:
        usage()
        exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            exit()
        elif opt in ("-v", "--version"):
            version()
            exit()
        elif opt in ("-m", "--nomusic"):
            override["music"] = 0
        elif opt in ("-s", "--nosfx"):
            override["sfx"] = 0
        elif opt in ("-f", "--fullscreen"):
            override["fullscreen"] = 0
        elif opt in ("--outfd"):
            try:
                outfd = int(arg)
                write(outfd, "\n")
            except:
                outfd = None
        elif opt in ("--data"):
            sharedir = arg
        elif opt in ("--score"):
            scorefile = arg
    # Init everything and launch the game
    settings = Settings(scorefile, outfd)
    for key, value in list(override.items()):
        settings.set(key, value)
    system = System()
    try:
        data = Data(sharedir)
    except:
        print(argv[0] + ": could not open data from `" + sharedir + "'.")
        raise
    fonter = Fonter()
    monsterz = Monsterz()
    monsterz.go()
    settings.save()
    exit()


if __name__ == "__main__":
    main()
