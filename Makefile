
DIRECTORY=monsterz-0.1.4

all:

dist:
	rm -Rf $(DIRECTORY)
	mkdir -p $(DIRECTORY)
	cp monsterz.py tiles.png board.png music.s3m $(DIRECTORY)/
	cp grunt.wav click.wav pop.wav boing.wav whip.wav $(DIRECTORY)/
	cp applause.wav laugh.wav warning.wav duh.wav ding.wav $(DIRECTORY)/
	cp Makefile tiles.svg README TODO COPYING AUTHORS $(DIRECTORY)/
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

