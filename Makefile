
prefix = /usr/local
gamesdir = ${prefix}/games
datadir = ${prefix}/share
pkgdatadir = $(datadir)/games/monsterz
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.4.2
DIRECTORY = monsterz-$(VERSION)

DATA = $(BITMAP) $(SOUND) $(MUSIC)
BITMAP = tiles.png background.png board.png logo.png icon.png
SOUND = grunt.wav click.wav pop.wav boing.wav whip.wav \
        applause.wav laugh.wav warning.wav duh.wav ding.wav
MUSIC = music.s3m
TEXT = README TODO COPYING AUTHORS INSTALL

all: monsterz $(BITMAP)

monsterz: monsterz.c
	$(CC) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

icon.png: tiles.svg
	inkscape tiles.svg -z -a 800:240:860:300 -w64 -h64 -e icon.png
tiles.png: tiles.svg
	inkscape tiles.svg -z -a 800:0:1100:600 -d 72 -e tiles.png
background.png: tiles.svg pattern.png
	inkscape tiles.svg -z -a 0:0:800:600 -d 72 -e background.png
board.png: tiles.svg pattern.png
	inkscape tiles.svg -z -a 30:690:510:1170 -d 72 -e board.png
logo.png: tiles.svg
	inkscape tiles.svg -z -a 810:618:1220:835 -w380 -h180 -e logo.png

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
	rm -Rf $(DIRECTORY)-src
	mkdir $(DIRECTORY)-src
	# Copy everything we need
	cp monsterz.py monsterz.c Makefile $(DIRECTORY)-src/
	cp pattern.png tiles.svg $(SOUND) $(MUSIC) $(TEXT) $(DIRECTORY)-src/
	# Build archive
	tar cvzf $(DIRECTORY)-src.tar.gz $(DIRECTORY)-src/
	rm -Rf $(DIRECTORY)-src

binary: all
	rm -Rf $(DIRECTORY)
	mkdir $(DIRECTORY)
	cp monsterz.py $(BITMAP) $(SOUND) $(MUSIC) $(TEXT) $(DIRECTORY)/
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	zip -r $(DIRECTORY).zip $(DIRECTORY)
	rm -Rf $(DIRECTORY)

distclean: clean
clean:
	rm -f monsterz $(BITMAP)

