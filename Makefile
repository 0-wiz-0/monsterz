
DIRECTORY=alienkeeper-0.1.2

all:

dist:
	rm -Rf $(DIRECTORY)
	mkdir -p $(DIRECTORY)
	cp alienkeeper.py tiles.png board.png music.s3m $(DIRECTORY)/
	cp Makefile README TODO COPYING AUTHORS $(DIRECTORY)/
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

