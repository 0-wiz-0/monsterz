
DIRECTORY=alienkeeper-0.1.3

all:

dist:
	rm -Rf $(DIRECTORY)
	mkdir -p $(DIRECTORY)
	cp alienkeeper.py tiles.png board.png music.s3m $(DIRECTORY)/
	cp grunt.wav click.wav $(DIRECTORY)/
	cp Makefile tiles.svg README TODO COPYING AUTHORS $(DIRECTORY)/
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

