#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

u"""\
Lit un fichier `allout', ou une partie d'un tel, et effectue divers
traitements sur ce fichier.  L'appel générique est:

Usage: allout ACTION [OPTION]... [FICHIER]...
"""

__metaclass__ = type

def main(*arguments):
    import allout
    if not arguments:
        sys.stdout.write(__doc__)
        import listing, texinfo
        for module in listing, texinfo, allout:
            sys.stdout.write(u'\n')
            sys.stdout.write(module.__doc__)
        sys.exit(0)
    action = arguments[0]
    arguments = arguments[1:]
    try:
        if action == u'html':
            import html
            html.main(*arguments)
        elif action == u'list':
            import codecs
            sys.stdout = codecs.getwriter(u'UTF-8')(sys.stdout)
            import listing
            listing.main(*arguments)
        elif action == u'texi':
            import texinfo
            texinfo.main(*arguments)
        else:
            raise allout.UsageError, u"Unknown ACTION."
    except allout.UsageError, message:
        sys.stderr.write(u"* %s\n* Try `allout' without arguments for help.\n"
                         % message)
        sys.exit(1)

if __name__ == u'__main__':
    main(*sys.argv[1:])
