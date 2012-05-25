#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Lit un fichier `allout', ou une partie d'un tel, et effectue divers
traitements sur ce fichier.  L'appel générique est:

Usage: allout ACTION [OPTION]... [FICHIER]...
"""

__metaclass__ = type
import sys

def main(*arguments):
    from . import allout
    if not arguments:
        sys.stdout.write(__doc__)
        from . import listing, texinfo
        for module in listing, texinfo, allout:
            sys.stdout.write('\n')
            sys.stdout.write(module.__doc__)
        sys.exit(0)
    action = arguments[0]
    arguments = arguments[1:]
    try:
        if action == 'html':
            from . import html
            html.main(*arguments)
        elif action == 'list':
            import codecs
            sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
            from . import listing
            listing.main(*arguments)
        elif action == 'texi':
            from . import texinfo
            texinfo.main(*arguments)
        else:
            raise allout.UsageError("Unknown ACTION.")
    except allout.UsageError as message:
        sys.stderr.write("* %s\n* Try `allout' without arguments for help.\n"
                         % message)
        sys.exit(1)

if __name__ == '__main__':
    main(*sys.argv[1:])
