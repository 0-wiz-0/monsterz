#!/usr/bin/env python

import pygame
from pygame.locals import *
from random import randint

# constants
AI = False
screen_width = 800
screen_height = 600

class MySprite(pygame.sprite.Sprite):
    def __init__(self, image, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.image = image
        self.rect = self.image.get_rect()

# Start all the stuff
class Game:
    def __init__(self, size = (8, 8), level = 1):
        pygame.init()
        # Init display
        self.window = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption('Alienkeeper')
        self.background = pygame.Surface(self.window.get_size())
        self.backsprites = pygame.sprite.RenderUpdates()
        self.frontsprites = pygame.sprite.RenderUpdates()
        # Load stuff
        self.tiles = pygame.image.load('tiles.png').convert_alpha()
        # Init values
        (self.board_width, self.board_height) = size
        self.needed = {}
        self.done = {}
        self.bonus_list = []
        self.disappear_list = []
        self.surprised_list = []
        self.select = None
        self.happy = {}
        self.surprised = {}
        self.angry = {}
        self.exploded = {}
        self.special = {}
        # Compute stuff
        self.tile_size = screen_width / self.board_width
        tmp = screen_height * 17 / 20 / self.board_height
        if tmp < self.tile_size:
            self.tile_size = tmp
        # Create sprites
        for x in range(8):
            self.happy[x] = pygame.transform.scale(self.tiles.subsurface((0, (x + 1) * 128, 128, 128)), (self.tile_size, self.tile_size))
            self.surprised[x] = pygame.transform.scale(self.tiles.subsurface((128, (x + 1) * 128, 128, 128)), (self.tile_size, self.tile_size))
            self.angry[x] = pygame.transform.scale(self.tiles.subsurface((256, (x + 1) * 128, 128, 128)), (self.tile_size, self.tile_size))
            self.exploded[x] = pygame.transform.scale(self.tiles.subsurface((384, (x + 1) * 128, 128, 128)), (self.tile_size, self.tile_size))
            tmp = pygame.Surface((128, 128))
            tmp.blit(self.tiles.subsurface((128, 0, 128, 128)), (0, 0))
            tmp2 = self.tiles.subsurface((0, (x + 1) * 128, 128, 128))
            # Crappy FX
            #tmp2 = pygame.transform.scale(tmp2, (24, 24))
            #tmp2 = pygame.transform.scale(tmp2, (128, 128))
            tmp.blit(tmp2, (0, 0))
            self.special[x] = pygame.transform.scale(tmp, (self.tile_size, self.tile_size))
        # Create selector sprite
        self.selector = pygame.transform.scale(self.tiles.subsurface((0, 0, 128, 128)), (self.tile_size, self.tile_size))
        # Other initialisation stuff
        self.score = 0
        self.timer = 0
        self.resolve_wins = False
        self.need_update = True
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
        if self.level >= 8:
            self.population = 8
        else:
            self.population = 7
        for i in range(self.population):
            self.done[i + 1] = 0
            if i + 1 == 8 and self.level < 8:
                self.needed[i + 1] = 0
            else:
                self.needed[i + 1] = self.level + 2
        self.angry_tiles = -1
        self.new_board()
        self.time = 1000000
        self.need_update = True

    def draw_sprites(self):
        self.backsprites.empty()
        if self.time > 0:
            self.background.fill((210, 200, 150))
        else:
            self.background.fill((255, 20, 15))
        # Draw board
        for (coord, n) in self.board.items():
            if n == 0:
                tmp = MySprite(self.special[self.timer % self.population], self.backsprites)
            elif coord in self.surprised_list:
                tmp = MySprite(self.surprised[n - 1], self.backsprites)
            elif coord in self.disappear_list:
                tmp = MySprite(self.exploded[n - 1], self.backsprites)
            elif n == self.angry_tiles:
                tmp = MySprite(self.angry[n - 1], self.backsprites)
            else:
                tmp = MySprite(self.happy[n - 1], self.backsprites)
            (x, y) = coord
            x *= self.tile_size
            y *= self.tile_size
            tmp.rect.center = (x + self.tile_size / 2, y + self.tile_size / 2)
        # Draw selector
        if self.select:
            tmp = MySprite(self.selector, self.backsprites)
            (x, y) = self.select
            x *= self.tile_size
            y *= self.tile_size
            tmp.rect.center = (x + self.tile_size / 2, y + self.tile_size / 2)
        # Print score
        font = pygame.font.Font(None, screen_height / 8)
        delta = 1 + screen_height / 200
        for x in range(2):
            text = font.render(str(self.score), 2, (x * 255, x * 255, x * 255))
            self.background.blit(text, (self.tile_size * self.board_width + self.tile_size / 2 - delta * x, - delta * x))
        # Print done/needed:
        font = pygame.font.Font(None, screen_height / 12)
        delta = 1 + screen_height / 300
        x = self.tile_size * self.board_width + self.tile_size / 2
        y = self.tile_size / 2 + screen_height / 8
        for i in range(self.population):
            self.background.blit(self.happy[i], (x, y))
            for d in range(2):
                text = font.render(str(self.done[i + 1]) + '/' + str(self.needed[i + 1]), 2, (d * 255, d * 255, d * 255))
                self.background.blit(text, (x + self.tile_size * 5 / 4 - delta * d, y + screen_height / 64 - delta * d))
            y += screen_height / 10
        # Print bonus:
        for x in self.bonus_list:
            for d in range(2):
                text = font.render(str(x[2]), 2, (d * 255, d * 255, d * 255))
                self.background.blit(text, (x[0] * self.tile_size + self.tile_size / 4 - delta * d, x[1] * self.tile_size + self.tile_size / 4 - delta * d))

    def draw_time(self):
        x = self.tile_size / 2
        y = screen_height * 18 / 20
        w = (self.board_width - 1) * self.tile_size
        h = screen_height / 20
        w2 = w * self.time / 2000000
        if self.time <= 350000:
            color = (255, 0, 0)
        else:
            color = (255, 240, 0)
        pygame.draw.rect(self.background, (0, 0, 0), (x, y, w, h))
        if w2 > 0:
            pygame.draw.rect(self.background, color, (x, y, w * self.time / 2000000, h))

    def iterate(self):
        ticks = pygame.time.get_ticks()
        delta = (ticks - self.oldticks) * 400 / (11.0000001 - self.level) # FIXME
        self.oldticks = ticks
        self.timer += 1
        # Draw screen
        if self.need_update:
            can_play = False
            for move in self.list_moves():
                can_play = True
                break
            self.need_update = False
            if not can_play:
                print 'no more moves!'
                self.new_board()
                self.need_update = True # Need to check again
        self.draw_sprites()
        self.draw_time()
        self.window.blit(self.background, (0, 0))
        # Draw stuff here
        self.backsprites.clear(self.window, self.background)
        self.frontsprites.clear(self.window, self.background)
        self.backsprites.update()
        self.frontsprites.update()
        dirtyRects1 = self.backsprites.draw(self.window)
        dirtyRects2 = self.frontsprites.draw(self.window)
        dirtyRects = dirtyRects1 + dirtyRects2
        #pygame.display.update(dirtyRects)
        pygame.display.flip()
        # Resolve winning moves and chain reactions
        if self.resolve_wins:
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
                    self.bonus_list.append([x2 / len(w), y2 / len(w), points])
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
                    self.resolve_wins = False
                    # Check for new level
                    finished = True
                    for i in range(self.population):
                        n = i + 1
                        if self.done[n] < self.needed[n]:
                            finished = False
                            break
                    if finished:
                        self.level += 1
                        self.new_level()
                self.need_update = True
            if self.win_timer:
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
                (x2, y2) = event.pos
                x2 /= self.tile_size
                y2 /= self.tile_size
                if x2 < 0 or x2 >= self.board_width or y2 < 0 or y2 >= self.board_height:
                    continue
                played = (x2, y2)
                break
        if self.time <= 0:
            #self.die = True
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
        if played:
            if not self.select:
                if self.board[played] != 0:
                    self.select = played
                    return
                # Deal with the special block
                self.wins = []
                target = 1 + (self.timer % self.population)
                found = 0
                for y in range(self.board_height):
                    for x in range(self.board_width):
                        if self.board[(x, y)] == target:
                            self.wins.append([(x, y)])
                self.board[played] = target
                self.wins.append([played])
                self.win_iter = 0
                self.win_timer = 12
                self.resolve_wins = True
                return
            (x1, y1) = self.select
            (x2, y2) = played
            if x1 == x2 and y1 == y2:
                self.select = None
                return
            if abs(x1 - x2) + abs(y1 - y2) != 1:
                return
            tmp = self.board[self.select]
            self.board[self.select] = self.board[played]
            self.board[played] = tmp
            self.wins = self.get_wins()
            if not self.wins:
                tmp = self.board[self.select]
                self.board[self.select] = self.board[played]
                self.board[played] = tmp
            self.select = None
            self.win_iter = 0
            self.win_timer = 12
            self.resolve_wins = True

level = 1
size = (8, 8)
game = Game(size = size, level = level)
game.go()

