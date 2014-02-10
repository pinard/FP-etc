#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Lorsque ACTION est `html', ce programme produite un fichier HTML à partir
des indications contenues dans le fichier `allout'.  Nous avons alors:

Usage: allout html [OPTION]... [FICHIER]

   -s SÉLECTION   Limiter le traitement au sous-arbre SÉLECTION

FICHIER contient le fichier `allout' à lire, entrée standard si non fourni.

L'option `-s' introduit une liste de nombres séparés par des points.  Ces
nombres décrivent un parcours de sélection d'un sous-arbre par la sélection
successive d'un embranchement à chaque niveau.  À chaque niveau, le nombre 0
représente la tête du niveau, les nombres 1 et suivants représentent les
branches comptées à partir de la première, les nombres -1 et précédents
représentent les branches comptées à partir de la dernière.  Cette sélection
s'effectue sur l'arbre après les simplifications décrites plus haut.
"""

__metaclass__ = type
import cgi
import sys


class Main:
    def __init__(self):
        self.selection = []

    def main(self, *arguments):
        self.selection = []
        import getopt
        options, arguments = getopt.getopt(arguments, 'as:')
        for option, value in options:
            if option == '-s':
                self.selection = list(map(int, value.split('.')))
        # Lire le fichier en format `allout'.
        from . import allout
        if len(arguments) == 0:
            structure = allout.read()
        elif len(arguments) == 1:
            structure = allout.read(arguments[0])
        else:
            raise allout.UsageError("Trop d'arguments.")
        # Choisir la sous-branche désirée.
        for branche in self.selection:
            structure = structure[branche]
        # Imprimer la liste résultante.
        write_html(structure)

main = Main().main


def write_html(structure, write=sys.stdout.write):
    # Transformer l'arbre STRUCTURE en HTML.
    # Le résultat est écrit sur OUTPUT, qui doit être une fonction
    # d'écriture ou encore, le nom d'un fichier à créer.
    if isinstance(write, str):
        write = file(write, 'w').write
    write(('<html>\n'
           ' <head>\n'
           '  <meta http-equiv="Content-Type" content="text/html;'
           ' charset=UTF-8" />\n'
           '  <title>%s</title>\n'
           ' </head>\n'
           ' <body>\n')
          % cgi.escape(''))
    write_html_recursive(structure, write, 1)
    write(' </body>\n'
          + '</html>\n')


def write_html_recursive(structure, write, level):
    # SPACING est True à l'entrée si la structure précédente s'imprimait sur
    # plusieurs lignes, et la valeur de cette fonction est True pour
    # indiquer que STRUCTURE a requis plus d'une ligne pour s'imprimer.
    if level > 1:
        write('  ' * level + '<li>')
    if isinstance(structure, str):
        if structure.startswith('http://'):
            write('<a href="%s">%s</a>\n' % (structure, cgi.escape(structure)))
        else:
            write(cgi.escape(structure))
    else:
        write(cgi.escape(structure[0]) + '\n')
        write('  ' * level + ' <ol>\n')
        for element in structure[1:]:
            write_html_recursive(element, write, level+1)
        write('  ' * level + ' </ol>\n' + '  ' * level)
    if level > 1:
        write('</li>\n')

if __name__ == '__main__':
    main(*sys.argv[1:])
