
prefix = /usr/local
bindir = ${prefix}/bin
datadir = ${prefix}/share
pkgdatadir = $(datadir)/monsterz
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.3
DIRECTORY = monsterz-$(VERSION)

DATA = $(BITMAP) $(SOUND) $(MUSIC)
BITMAP = tiles.png board.png logo.png
SOUND = grunt.wav click.wav pop.wav boing.wav whip.wav \
        applause.wav laugh.wav warning.wav duh.wav ding.wav
MUSIC = music.s3m
TEXT = README TODO COPYING AUTHORS INSTALL

all: monsterz

monsterz: monsterz.c
	$(CC) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

install: all
	mkdir -p $(DESTDIR)$(bindir)
	cp monsterz $(DESTDIR)$(bindir)/
	chown root:games $(DESTDIR)$(bindir)/monsterz
	chmod g+s $(DESTDIR)$(bindir)/monsterz
	mkdir -p $(DESTDIR)$(pkgdatadir)
	cp monsterz.py $(DATA) $(DESTDIR)$(pkgdatadir)/
	mkdir -p $(DESTDIR)$(scoredir)
	test -f $(DESTDIR)$(scorefile) || echo "" > $(DESTDIR)$(scorefile)
	chown root:games $(DESTDIR)$(scorefile)
	chmod g+w $(DESTDIR)$(scorefile)

uninstall:
	rm -f $(DESTDIR)$(bindir)/monsterz
	rm -Rf $(DESTDIR)$(pkgdatadir)/
	rm -f $(DESTDIR)$(scorefile)

dist:
	rm -Rf $(DIRECTORY)
	mkdir $(DIRECTORY)
	# Copy everything we need
	cp monsterz.py monsterz.c $(DATA) $(TEXT) Makefile $(DIRECTORY)/
	cp pattern.png tiles.svg $(DIRECTORY)/
	# Build archive
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

clean:
	rm -f monsterz

