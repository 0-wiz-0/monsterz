
prefix = /usr/local
gamesdir = ${prefix}/games
datadir = ${prefix}/share
pkgdatadir = $(datadir)/games/monsterz
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.7.1
DIRECTORY = monsterz-$(VERSION)

BITMAP = graphics/tiles.png graphics/bigtiles.png graphics/background.png \
         graphics/board.png graphics/logo.png graphics/icon.png
SOUND = sound/grunt.wav sound/click.wav sound/pop.wav sound/boing.wav sound/whip.wav \
        sound/applause.wav sound/laugh.wav sound/warning.wav sound/duh.wav \
        sound/ding.wav
MUSIC = sound/music.s3m
TEXT = README TODO COPYING AUTHORS INSTALL

INKSCAPE = inkscape -z

all: monsterz

monsterz: monsterz.c
	$(CC) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

bitmap: $(BITMAP)

graphics/icon.png: graphics/graphics.svg
	$(INKSCAPE) graphics/graphics.svg -a 800:480:860:540 -w64 -h64 -e graphics/icon.png
graphics/tiles.png: graphics/graphics.svg
	$(INKSCAPE) graphics/graphics.svg -a 800:0:1100:840 -d 72 -e graphics/tiles.png
graphics/bigtiles.png: graphics/graphics.svg
	$(INKSCAPE) graphics/graphics.svg -a 800:0:860:540 -d 432 -e graphics/bigtiles.png
graphics/background.png: graphics/graphics.svg graphics/pattern.png
	$(INKSCAPE) graphics/graphics.svg -a 0:0:800:600 -d 72 -e graphics/background.png
graphics/board.png: graphics/graphics.svg graphics/pattern.png
	$(INKSCAPE) graphics/graphics.svg -a 30:690:510:1170 -d 72 -e graphics/board.png
graphics/logo.png: graphics/graphics.svg
	$(INKSCAPE) graphics/graphics.svg -a 810:858:1220:1075 -w380 -h180 -e graphics/logo.png

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
	#rm -f $(DESTDIR)$(scorefile)

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
	zip -r $(DIRECTORY).zip $(DIRECTORY)
	rm -Rf $(DIRECTORY)

distclean: clean
clean:
	rm -f monsterz

