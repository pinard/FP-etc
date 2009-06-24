all:
	
install:
	for dir in .vim .vim/syntax .vim/ftplugin .vim/doc .vim/python; do \
	  test -d $(HOME)/$$dir || mkdir $(HOME)/$$dir; \
	done
	cp doc.txt $(HOME)/.vim/doc/allout.txt
	cp ftplugin.vim $(HOME)/.vim/ftplugin/allout.vim
	cp python.py $(HOME)/.vim/python/allout.py
	cp syntax.vim $(HOME)/.vim/syntax/allout.vim
	vim -fNn -u NONE >/dev/null 2>/dev/null \
	  -c 'helptags $(HOME)/.vim/doc' -c q
	@echo "WARNING: You also need to modify your ~/.vimrc; see README."

install-root:

dist: dist-tar dist-zip

PACKAGE = allout-vim
VERSION := $(shell date +%y%m%d)
ARCHIVES = $(HOME)/fp-etc/archives

dist-tar:
	mkdir $(PACKAGE)-$(VERSION)
	ln ChangeLog Makefile README TODO $(PACKAGE)-$(VERSION)
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
