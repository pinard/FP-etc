all:
	@echo "See the README file."

install-user:
	$(MAKE) install-common VIMFILES=$(HOME)/.vim
	@echo "WARNING: You might need to modify your ~/.vimrc; see README."

install-root:
	@test -d "$(VIM)" || \
	  (echo "VIM should be set to a directory; see README" && false)
	$(MAKE) install-common VIMFILES=$(VIM)/vimfiles
	@echo "WARNING: Python should now about $(VIM)/vimfiles/python/,"
	@echo "         see README for more information on this."

install-common:
	for dir in $(VIMFILES) $(VIMFILES)/syntax $(VIMFILES)/ftplugin \
	      $(VIMFILES)/doc $(VIMFILES)/python; do \
	  test -d $$dir || mkdir $$dir; \
	done
	cp doc.txt $(VIMFILES)/doc/allout.txt
	cp ftplugin.vim $(VIMFILES)/ftplugin/allout.vim
	cp ../Allout/vim.py $(VIMFILES)/python/allout.py
	cp syntax.vim $(VIMFILES)/syntax/allout.vim
	vim -fNn -u NONE >/dev/null 2>/dev/null \
	  -c 'helptags $(VIMFILES)/doc' -c q

dist: dist-tar dist-zip

PACKAGE = allout-vim
VERSION := $(shell date +%y%m%d)
ARCHIVES = $(HOME)/fp-etc/archives

dist-tar:
	mkdir $(PACKAGE)-$(VERSION)
	ln ChangeLog Makefile README THANKS TODO $(PACKAGE)-$(VERSION)
	ln doc.txt ftplugin.vim syntax.vim $(PACKAGE)-$(VERSION)
	ln ../Allout/vim.py $(PACKAGE)-$(VERSION)/python.py
	rm -f $(ARCHIVES)/$(PACKAGE)-$(VERSION).tgz $(ARCHIVES)/$(PACKAGE).tgz
	tar cfz $(ARCHIVES)/$(PACKAGE)-$(VERSION).tgz $(PACKAGE)-$(VERSION)
	ln -s $(PACKAGE)-$(VERSION).tgz $(ARCHIVES)/$(PACKAGE).tgz
	rm -rf $(PACKAGE)-$(VERSION)

dist-zip:
	mkdir tmp
	mkdir tmp/doc
	cp doc.txt tmp/doc/allout.txt
	mkdir tmp/ftplugin
	cp ftplugin.vim tmp/ftplugin/allout.vim
	mkdir tmp/python
	cp ../Allout/vim.py tmp/python/allout.py
	mkdir tmp/syntax
	cp syntax.vim tmp/syntax/allout.vim
	rm -f $(ARCHIVES)/$(PACKAGE)-$(VERSION).zip $(ARCHIVES)/$(PACKAGE).zip
	(cd tmp && zip -r $(ARCHIVES)/$(PACKAGE)-$(VERSION).zip .)
	ln -s $(PACKAGE)-$(VERSION).zip $(ARCHIVES)/$(PACKAGE).zip
	rm -rf tmp
