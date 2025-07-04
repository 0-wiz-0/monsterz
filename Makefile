prefix = /usr/local
gamesdir = $(prefix)/games
datadir = $(prefix)/share
mandir = $(prefix)/share/man
pkgdatadir = $(datadir)/games/monsterz
applicationsdir = $(datadir)/applications
scoredir = /var/games
scorefile = $(scoredir)/monsterz

VERSION = 0.9
DIRECTORY = monsterz-$(VERSION)

BITMAP = graphics/tiles.png graphics/bigtiles.png graphics/background.png \
  graphics/board.png graphics/logo.png graphics/icon.png
SOUND = sound/grunt.wav sound/click.wav sound/pop.wav sound/boing.wav sound/whip.wav \
  sound/applause.wav sound/laugh.wav sound/warning.wav sound/duh.wav \
  sound/ding.wav
MUSIC = sound/music.s3m
TEXT = AUTHORS COPYRIGHT INSTALL LICENSE NEWS.md README.md TODO monsterz.desktop.in monsterz.6

INSTALL_DATA = install -c -m 644
INSTALL_PROGRAM = install -c -m 755
INSTALL_SCRIPT = install -c -m 755
INSTALL_DIR = install -d

INKSCAPE = inkscape

all: monsterz monsterz.desktop

monsterz: monsterz.c
	$(CC) $(CFLAGS) $(CPPFLAGS) $(LDFLAGS) -Wall monsterz.c -DDATADIR=\"$(pkgdatadir)\" -DSCOREFILE=\"$(scorefile)\" -o monsterz

monsterz.desktop: monsterz.desktop.in
	sed "s!@DATADIR@!$(pkgdatadir)!" monsterz.desktop.in > monsterz.desktop

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
	$(INSTALL_DIR) $(DESTDIR)$(gamesdir)
	$(INSTALL_DIR) $(DESTDIR)$(applicationsdir)
	$(INSTALL_DIR) $(DESTDIR)$(mandir)/man6
	$(INSTALL_PROGRAM) monsterz $(DESTDIR)$(gamesdir)/
	chown root:games $(DESTDIR)$(gamesdir)/monsterz
	chmod g+s $(DESTDIR)$(gamesdir)/monsterz
	$(INSTALL_DIR) $(DESTDIR)$(pkgdatadir)/graphics
	$(INSTALL_DIR) $(DESTDIR)$(pkgdatadir)/sound
	$(INSTALL_SCRIPT) monsterz.py $(DESTDIR)$(pkgdatadir)/
	$(INSTALL_DATA) $(BITMAP) $(DESTDIR)$(pkgdatadir)/graphics/
	$(INSTALL_DATA) $(SOUND) $(MUSIC) $(DESTDIR)$(pkgdatadir)/sound/
	$(INSTALL_DATA) monsterz.desktop $(DESTDIR)$(applicationsdir)
	$(INSTALL_DATA) monsterz.6 $(DESTDIR)$(mandir)/man6
	$(INSTALL_DIR) $(DESTDIR)$(scoredir)
	test -f $(DESTDIR)$(scorefile) || echo "" > $(DESTDIR)$(scorefile)
	chown root:games $(DESTDIR)$(scorefile)
	chmod g+w $(DESTDIR)$(scorefile)

uninstall:
	rm -f $(DESTDIR)$(gamesdir)/monsterz
	rm -f $(DESTDIR)$(applicationsdir)/monsterz.desktop
	rm -f $(DESTDIR)$(mandir)/man6/monsterz.6
	rmdir -p $(DESTDIR)$(gamesdir) 2> /dev/null || true
	rmdir -p $(DESTDIR)$(applicationsdir) 2> /dev/null || true
	rmdir -p $(DESTDIR)$(mandir)/man6 2> /dev/null || true
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
	rm -f monsterz monsterz.desktop
