
prefix = /usr/local
gamesdir = ${prefix}/games
datadir = ${prefix}/share
pkgdatadir = $(datadir)/games/monsterz
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.5.0
DIRECTORY = monsterz-$(VERSION)

BITMAP = graphics/tiles.png graphics/bigtiles.png graphics/background.png \
         graphics/board.png graphics/logo.png graphics/icon.png
SOUND = sound/grunt.wav sound/click.wav sound/pop.wav sound/boing.wav sound/whip.wav \
        sound/applause.wav sound/laugh.wav sound/warning.wav sound/duh.wav \
        sound/ding.wav
MUSIC = sound/music.s3m
TEXT = README TODO COPYING AUTHORS INSTALL

all: monsterz $(BITMAP)

monsterz: monsterz.c
	$(CC) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

graphics/icon.png: graphics/graphics.svg
	inkscape graphics/graphics.svg -z -a 800:240:860:300 -w64 -h64 -e graphics/icon.png
graphics/tiles.png: graphics/graphics.svg
	inkscape graphics/graphics.svg -z -a 800:0:1100:660 -d 72 -e graphics/tiles.png
graphics/bigtiles.png: graphics/graphics.svg
	inkscape graphics/graphics.svg -z -a 800:0:860:540 -d 432 -e graphics/bigtiles.png
graphics/background.png: graphics/graphics.svg graphics/pattern.png
	inkscape graphics/graphics.svg -z -a 0:0:800:600 -d 72 -e graphics/background.png
graphics/board.png: graphics/graphics.svg graphics/pattern.png
	inkscape graphics/graphics.svg -z -a 30:690:510:1170 -d 72 -e graphics/board.png
graphics/logo.png: graphics/graphics.svg
	inkscape graphics/graphics.svg -z -a 810:678:1220:895 -w380 -h180 -e graphics/logo.png

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
	rm -Rf $(DIRECTORY)-src
	mkdir $(DIRECTORY)-src
	mkdir $(DIRECTORY)-src/graphics
	mkdir $(DIRECTORY)-src/sound
	# Copy everything we need
	cp monsterz.py monsterz.c Makefile $(DIRECTORY)-src/
	cp $(TEXT) $(DIRECTORY)-src/
	cp graphics/pattern.png graphics/graphics.svg $(DIRECTORY)-src/graphics
	cp $(SOUND) $(MUSIC) $(DIRECTORY)-src/sound
	# Build archive
	tar cvzf $(DIRECTORY)-src.tar.gz $(DIRECTORY)-src/
	rm -Rf $(DIRECTORY)-src

binary: all
	rm -Rf $(DIRECTORY)
	mkdir $(DIRECTORY)
	mkdir $(DIRECTORY)/graphics
	mkdir $(DIRECTORY)/sound
	cp monsterz.py $(TEXT) $(DIRECTORY)/
	cp $(BITMAP) $(DIRECTORY)/graphics
	cp $(SOUND) $(MUSIC) $(DIRECTORY)/sound
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	zip -r $(DIRECTORY).zip $(DIRECTORY)
	rm -Rf $(DIRECTORY)

distclean: clean
clean:
	rm -f monsterz $(BITMAP)

