
DIRECTORY=alienkeeper-0.0.20050228

all:

dist:
	rm -Rf $(DIRECTORY)
	mkdir -p $(DIRECTORY)
	cp alienkeeper.py tiles.png $(DIRECTORY)/
	cp Makefile README COPYING AUTHORS $(DIRECTORY)/
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

