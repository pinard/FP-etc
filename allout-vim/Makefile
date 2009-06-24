FILES = Makefile README doc.txt ftplugin.vim syntax.vim ../Allout/vim.py

PACKAGE_VERSION := allout-vim-$(shell date +%y%m%d)
ARCHIVES = $(HOME)/fp-etc/archives

dist:
	mkdir $(PACKAGE_VERSION)
	ln $(FILES) $(PACKAGE_VERSION)
	tar cfz $(ARCHIVES)/$(PACKAGE_VERSION).tgz $(PACKAGE_VERSION)
	rm -rf $(PACKAGE_VERSION)
