
DIRECTORY=monsterz-0.1.6

all:

dist:
	rm -Rf $(DIRECTORY)
	mkdir -p $(DIRECTORY)
	# Copy everything we need
	cp monsterz.py $(DIRECTORY)/
	cp tiles.png board.png logo.png music.s3m $(DIRECTORY)/
	cp grunt.wav click.wav pop.wav boing.wav whip.wav $(DIRECTORY)/
	cp applause.wav laugh.wav warning.wav duh.wav ding.wav $(DIRECTORY)/
	cp Makefile README TODO COPYING AUTHORS $(DIRECTORY)/
	# Sources (not used directly)
	cp pattern.png tiles.svg $(DIRECTORY)/
	# Build archive
	tar cvzf $(DIRECTORY).tar.gz $(DIRECTORY)/
	rm -Rf $(DIRECTORY)

