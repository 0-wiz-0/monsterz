
prefix = /usr/local
gamesdir = ${prefix}/games
datadir = ${prefix}/share
pkgdatadir = $(datadir)/games/monsterz
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.4
DIRECTORY = monsterz-$(VERSION)

DATA = $(BITMAP) $(SOUND) $(MUSIC)
BITMAP = tiles.png board.png logo.png icon.png
SOUND = grunt.wav click.wav pop.wav boing.wav whip.wav \
        applause.wav laugh.wav warning.wav duh.wav ding.wav
MUSIC = music.s3m
TEXT = README TODO COPYING AUTHORS INSTALL

all: monsterz $(BITMAP)

monsterz: monsterz.c
	$(CC) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

icon.png: tiles.svg
	inkscape tiles.svg -z -a 0:600:60:660 -w64 -h64 -e icon.png
tiles.png: tiles.svg
	inkscape tiles.svg -z -a 0:360:300:900 -d 72 -e tiles.png
board.png: tiles.svg
	inkscape tiles.svg -z -a 300:360:1100:960 -d 72 -e board.png
logo.png: tiles.svg
	inkscape tiles.svg -z -a 77:100:481:323 -w374 -h182 -e logo.png

install: all
	mkdir -p $(DESTDIR)$(gamesdir)
	cp monsterz $(DESTDIR)$(gamesdir)/
	chown root:games $(DESTDIR)$(gamesdir)/monsterz
	chmod g+s $(DESTDIR)$(gamesdir)/monsterz
	mkdir -p $(DESTDIR)$(pkgdatadir)
	cp monsterz.py $(DATA) $(DESTDIR)$(pkgdatadir)/
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
	# Copy everything we need
	cp monsterz.py monsterz.c Makefile $(DIRECTORY)/
	cp pattern.png tiles.svg $(SOUND) $(MUSIC) $(TEXT) $(DIRECTORY)/
	# Build archive
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

distclean: clean
clean:
	rm -f monsterz $(BITMAP)

