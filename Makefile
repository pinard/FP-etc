# Allout utilities - Makefile.
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003-03.

PYSETUP = python setup.py --quiet
DISTRIBUTION = Etc-0.2

all:
	$(PYSETUP) build

install: all
	$(PYSETUP) install

tags:
	find -name '*.py' | grep -v '~$$' | etags -

dist:
	$(PYSETUP) sdist
	mv dist/$(DISTRIBUTION).tar.gz .
	rmdir dist
	ls -l *.gz

publish: dist
	traiter README.html > index.html
	chmod 644 index.html $(DISTRIBUTION).tar.gz
	scp -p index.html $(DISTRIBUTION).tar.gz bor:w/allout/
	rm index.html $(DISTRIBUTION).tar.gz
