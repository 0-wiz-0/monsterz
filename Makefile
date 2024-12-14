
prefix = /usr/local
gamesdir = ${prefix}/games
datadir = ${prefix}/share
pkgdatadir = $(datadir)/games/monsterz
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.8
DIRECTORY = monsterz-$(VERSION)

BITMAP = graphics/tiles.png graphics/bigtiles.png graphics/background.png \
         graphics/board.png graphics/logo.png graphics/icon.png
SOUND = sound/grunt.wav sound/click.wav sound/pop.wav sound/boing.wav sound/whip.wav \
        sound/applause.wav sound/laugh.wav sound/warning.wav sound/duh.wav \
        sound/ding.wav
MUSIC = sound/music.s3m
TEXT = README.md TODO COPYING AUTHORS INSTALL

INKSCAPE = inkscape

all: monsterz

monsterz: monsterz.c
	$(CC) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

bitmap: $(BITMAP)

graphics/icon.png: graphics/graphics.svg
	$(INKSCAPE) --actions="export-area:800:660:860:720;export-width:64;export-height:64;export-filename:graphics/icon.png;export-do;" graphics/graphics.svg
graphics/tiles.png: graphics/graphics.svg
	$(INKSCAPE) -d 72 --actions="export-area:800:360:1100:1200;export-width:240;export-height:672;export-filename:graphics/tiles.png;export-do;" graphics/graphics.svg
graphics/bigtiles.png: graphics/graphics.svg
	$(INKSCAPE) -d 432 --actions="export-area:800:660:860:1200;export-width:288;export-height:2592;export-filename:graphics/bigtiles.png;export-do;" graphics/graphics.svg
graphics/background.png: graphics/graphics.svg graphics/pattern.png
	$(INKSCAPE) -d 72 --actions="export-area:0:600:800:1200;export-width:640;export-height:480;export-filename:graphics/background.png;export-do;" graphics/graphics.svg
graphics/board.png: graphics/graphics.svg graphics/pattern.png
	$(INKSCAPE) -d 72 --actions="export-area:30:30:510:510;export-width:384;export-height:384;export-filename:graphics/board.png;export-do;" graphics/graphics.svg
graphics/logo.png: graphics/graphics.svg
	$(INKSCAPE) --actions="export-area:810:125:1220:342;export-width:380;export-height:180;export-filename:graphics/logo.png;export-do;" graphics/graphics.svg

install: all
	mkdir -p $(DESTDIR)$(gamesdir)
	cp monsterz $(DESTDIR)$(gamesdir)/
	chown root:games $(DESTDIR)$(gamesdir)/monsterz
	chmod g+s $(DESTDIR)$(gamesdir)/monsterz
	mkdir -p $(DESTDIR)$(pkgdatadir)/graphics
	mkdir -p $(DESTDIR)$(pkgdatadir)/sound
	cp monsterz.py $(DESTDIR)$(pkgdatadir)/
	cp $(BITMAP) $(DESTDIR)$(pkgdatadir)/graphics/
	cp $(SOUND) $(MUSIC) $(DESTDIR)$(pkgdatadir)/sound/
	mkdir -p $(DESTDIR)$(scoredir)
	test -f $(DESTDIR)$(scorefile) || echo "" > $(DESTDIR)$(scorefile)
	chown root:games $(DESTDIR)$(scorefile)
	chmod g+w $(DESTDIR)$(scorefile)

uninstall:
	rm -f $(DESTDIR)$(gamesdir)/monsterz
	rm -Rf $(DESTDIR)$(pkgdatadir)/
#	rm -f $(DESTDIR)$(scorefile)

dist:
	rm -Rf $(DIRECTORY)
	mkdir $(DIRECTORY)
	mkdir $(DIRECTORY)/graphics
	mkdir $(DIRECTORY)/sound
	cp monsterz.py monsterz.c Makefile $(TEXT) $(DIRECTORY)/
	cp graphics/pattern.png graphics/graphics.svg $(DIRECTORY)/graphics
	cp $(BITMAP) $(DIRECTORY)/graphics
	cp $(SOUND) $(MUSIC) $(DIRECTORY)/sound
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

distclean: clean
clean:
	rm -f monsterz

