
DIRECTORY=alienkeeper-0.0.20050304

all:

dist:
	rm -Rf $(DIRECTORY)
	mkdir -p $(DIRECTORY)
	cp alienkeeper.py tiles.png $(DIRECTORY)/
	cp Makefile README TODO COPYING AUTHORS $(DIRECTORY)/
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

