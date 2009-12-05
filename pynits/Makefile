INSTALL = install
# Use `mkdir' if you do not have `install'.
INSTALL_DIR = $(INSTALL) -d -m 755
# Use `cp' if you do not have `install'.
INSTALL_DATA = $(INSTALL) -m 644

LANGUAGES = fr es
LANGUAGES = fr
BUILT = pynits.pot $(addsuffix .mo, $(LANGUAGES))

all:
	@echo "See the README file."

install:
	@echo "Choose either `install-user' or `install-root'; see README."

install-user:
	$(MAKE) install-common VIMFILES=$(HOME)/.vim
	@echo "WARNING: You might need to modify your ~/.vimrc; see README."

install-root:
	@test -d "$(VIM)" || \
	  (echo "VIM should be set to a directory; see README" && false)
	$(MAKE) install-common VIMFILES=$(VIM)/vimfiles
	@echo "WARNING: Python should know about $(VIM)/vimfiles/python/,"
	@echo "         see README for more information on this."

install-common:
	test -d $(VIMFILES) || $(INSTALL_DIR) $(VIMFILES)
	for dir in doc ftplugin locale python; do \
	  test -d $(VIMFILES)/$$dir || $(INSTALL_DIR) $(VIMFILES)/$$dir; \
	done
	$(INSTALL_DATA) pynits.py $(VIMFILES)/python/pynits.py
	grep 'python import pynits' $(VIMFILES)/ftplugin/python.vim \
	    >/dev/null 2>/dev/null \
	  || echo 'python import pynits' >> $(VIMFILES)/ftplugin/python.vim
	$(INSTALL_DATA) pynits.txt $(VIMFILES)/doc/pynits.txt
	vim -fNn -u NONE >/dev/null 2>/dev/null \
	  -c 'helptags $(VIMFILES)/doc' -c q
	for lang in $(LANGUAGES); do \
	  for dir in locale/$$lang locale/$$lang/LC_MESSAGES; do \
	    test -d $(VIMFILES)/$$dir || $(INSTALL_DIR) $(VIMFILES)/$$dir; \
	  done; \
	  $(INSTALL_DATA) $$lang.mo \
	      $(VIMFILES)/locale/$$lang/LC_MESSAGES/pynits.mo; \
	done

dist: dist-tar dist-zip

PACKAGE = pynits
VERSION := $(shell date +%y%m%d)
ARCHIVES = $(HOME)/fp-etc/archives

dist-tar: $(BUILT)
	rm -rf $(PACKAGE)-$(VERSION)
	mkdir $(PACKAGE)-$(VERSION)
	ln ChangeLog Makefile README THANKS TODO \
	    pynits.pot pynits.py pynits.txt $(PACKAGE)-$(VERSION)
	for lang in $(LANGUAGES); do \
	  ln $$lang.po $$lang.mo $(PACKAGE)-$(VERSION); \
	done
	rm -f $(ARCHIVES)/$(PACKAGE)-$(VERSION).tgz $(ARCHIVES)/$(PACKAGE).tgz
	tar cfz $(ARCHIVES)/$(PACKAGE)-$(VERSION).tgz $(PACKAGE)-$(VERSION)
	ln -s $(PACKAGE)-$(VERSION).tgz $(ARCHIVES)/$(PACKAGE).tgz
	rm -rf $(PACKAGE)-$(VERSION)

dist-zip: $(BUILT)
	rm -rf tmp
	mkdir tmp
	mkdir tmp/doc
	cp pynits.txt tmp/doc/
	mkdir tmp/python
	cp pynits.py tmp/python/
	mkdir tmp/locale
	for lang in $(LANGUAGES); do \
	  mkdir tmp/locale/$$lang tmp/locale/$$lang/LC_MESSAGES; \
	  cp $$lang.mo tmp/locale/$$lang/LC_MESSAGES/; \
	done
	rm -f $(ARCHIVES)/$(PACKAGE)-$(VERSION).zip $(ARCHIVES)/$(PACKAGE).zip
	(cd tmp && zip -r $(ARCHIVES)/$(PACKAGE)-$(VERSION).zip .)
	ln -s $(PACKAGE)-$(VERSION).zip $(ARCHIVES)/$(PACKAGE).zip
	rm -rf tmp

i18ndir = /usr/share/doc/packages/python/Tools/i18n

.SUFFIXES: .po .mo

%.mo: %.po
	$(PYTHON) $(i18ndir)/msgfmt.py $^

%.po: pynits.pot
	msgmerge $@ $^ > $@-tmp && mv $@-tmp $@

pynits.pot: pynits.py
	$(PYTHON) $(i18ndir)/pygettext.py --docstrings --output=$@ pynits.py
