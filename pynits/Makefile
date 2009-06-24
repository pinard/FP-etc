INSTALL = install
# Use `mkdir' if you do not have `install'.
INSTALL_DIR = $(INSTALL) -d -m 755
# Use `cp' if you do not have `install'.
INSTALL_DATA = $(INSTALL) -m 644

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
	for dir in $(VIMFILES) $(VIMFILES)/doc $(VIMFILES)/ftplugin \
	      $(VIMFILES)/python; do \
	  test -d $$dir || $(INSTALL_DIR) $$dir; \
	done
	$(INSTALL_DATA) pynits.py $(VIMFILES)/python/pynits.py
	grep 'python import pynits' $(VIMFILES)/ftplugin/python.vim \
	    >/dev/null 2>/dev/null \
	  || echo 'python import pynits' >> $(VIMFILES)/ftplugin/python.vim
	$(INSTALL_DATA) pynits.txt $(VIMFILES)/doc/pynits.txt
	vim -fNn -u NONE >/dev/null 2>/dev/null \
	  -c 'helptags $(VIMFILES)/doc' -c q

dist: dist-tar dist-zip

PACKAGE = pynits
VERSION := $(shell date +%y%m%d)
ARCHIVES = $(HOME)/fp-etc/archives

dist-tar:
	mkdir $(PACKAGE)-$(VERSION)
	ln ChangeLog Makefile README THANKS TODO pynits.py pynits.txt \
	  $(PACKAGE)-$(VERSION)
	rm -f $(ARCHIVES)/$(PACKAGE)-$(VERSION).tgz $(ARCHIVES)/$(PACKAGE).tgz
	tar cfz $(ARCHIVES)/$(PACKAGE)-$(VERSION).tgz $(PACKAGE)-$(VERSION)
	ln -s $(PACKAGE)-$(VERSION).tgz $(ARCHIVES)/$(PACKAGE).tgz
	rm -rf $(PACKAGE)-$(VERSION)

dist-zip:
	mkdir tmp
	mkdir tmp/doc
	cp pynits.txt tmp/doc/
	mkdir tmp/python
	cp pynits.py tmp/python/
	rm -f $(ARCHIVES)/$(PACKAGE)-$(VERSION).zip $(ARCHIVES)/$(PACKAGE).zip
	(cd tmp && zip -r $(ARCHIVES)/$(PACKAGE)-$(VERSION).zip .)
	ln -s $(PACKAGE)-$(VERSION).zip $(ARCHIVES)/$(PACKAGE).zip
	rm -rf tmp
