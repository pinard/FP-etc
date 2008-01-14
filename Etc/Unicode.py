#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2005 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2005.

u"""\
Offrir quelques commodités pour travailler complètement en Unicode.

Usage suggéré:  from Unicode import VALEUR...

VALEUR:
  apply       ``apply`` avec mots-clés re-transformés en ASCII
  deunicode   ``str`` universel, livrant du UTF-8 ou du Latin-1
  reunicode   ``unicode`` universel, lisant du UTF-8 ou Latin-1
  file        ``file``, avec fragments convertis en Unicode, séparément
  open        Même chose que ``file``
  sys         ``sys.argv`` en Unicode
              ``sys.stdin`` filtré pour Unicode
              ``sys.stdout`` filtré pour Unicode
              ``sys.stderr`` filtré pour Unicode

De plus, les exceptions sont modifiées pour traiter sans férir des arguments
de type unicode.
"""

# REVOIR:
# . dans socket, arguments de bind, connect, recv et send
# . les nombres flottants sont formatés avec une virgule
# . os.environ va, mais os.putenv ne va pas, par exemple dans:
#        os.putenv(u'CLASSER_JOURNAL', u'trace')
#        os.environ[u'CLASSER_JOURNAL'] = u'trace'
# · dans type, le premier argument ne peut être unicode

__metaclass__ = type
import locale, os, sys

CODES = u'UTF-8', u'ISO-8859-1'
ERREURS = ""'backslashreplace'
IMPLICITE = sys.getdefaultencoding()
TERMINAL = locale.getpreferredencoding()

if sys.version_info < (2, 5):

    def decorer_exception_init(classe):
        vieux_init = classe.__init__

        def __init__(self, *arguments):
            valeurs = []
            for argument in arguments:
                if isinstance(argument, unicode):
                    valeurs.append(deunicode(argument))
                else:
                    valeurs.append(argument)
            vieux_init(self, *valeurs)

        classe.__init__ = __init__

    # J'ai consulté Python-2.3.4/Python/exceptions.c pour savoir quelles
    # exceptions doivent être ainsi "décorées" (ou interceptées).
    decorer_exception_init(Exception)
    decorer_exception_init(EnvironmentError)
    decorer_exception_init(SystemExit)
    decorer_exception_init(UnicodeDecodeError)
    decorer_exception_init(UnicodeTranslateError)

def apply(fonction, arguments, definitions={}):
    return fonction(*arguments,
                    **dict([(cle.encode(""'ASCII'), valeur)
                            for cle, valeur in definitions.iteritems()]))

def deunicode(texte):
    return texte.encode(TERMINAL, ERREURS)

def reunicode(texte, encoding=None, errors=u'strict'):
    if isinstance(texte, unicode):
        return texte
    if encoding is not None:
        return unicode(texte, encoding, errors)
    if isinstance(texte, str):
        for encoding in CODES:
            try:
                return texte.decode(encoding)
            except UnicodeDecodeError:
                pass
        assert False
    else:
        try:
            return unicode(texte)
        except UnicodeDecodeError:
            # On arrive ici dans le cas d'une exception.
            return unicode(str(texte))

def file(filename, mode=u'r', encoding=None, errors=u'strict', bufsize=-1):
    filename = nom_fichier_str(filename)
    if u'b' in mode:
        import __builtin__
        return __builtin__.file(filename, mode, bufsize)
    if u'w' in mode:
        import codecs
        return codecs.open(filename, mode, encoding or TERMINAL,
                           errors, bufsize)
    import __builtin__
    return Filtre(__builtin__.file(filename, mode, bufsize), encoding, errors)

open = file

class _sys:
    import sys

    def __init__(self):
        self.__dict__[u'argv'] = tuple(map(reunicode, self.sys.argv))
        self.__dict__[u'stdin'] = Filtre(self.sys.stdin)
        self.__dict__[u'stdout'] = Filtre(self.sys.stdout)
        self.__dict__[u'stderr'] = Filtre(self.sys.stderr)

    def __getattr__(self, attribut):
        return getattr(self.sys, attribut)

    def __setattr__(self, attribut, valeur):
        if attribut in (u'argv', u'stdin', u'stdout', u'stderr'):
            self.__dict__[attribut] = valeur
        else:
            setattr(self.sys, attribut, valeur)

def nom_fichier_str(nom, nouveau=False, code=None):
    # Retourne un nom de fichier à 8-bits en résolvant les ambiguïtés entre
    # Latin-1 et UTF-8 dans la séquence de répertoires et sous-répertoires.
    # Si NOUVEAU est True, le dernier fragment du nom est forcé au code
    # implicite, indépendamment du fait que ce fichier existe ou non.
    # Si CODE est None, préférer le code indiqué dans TERMINAL.
    fragments = reunicode(nom).split(u'/')
    partiel = None
    for compteur, fragment in enumerate(fragments):
        for essai in CODES:
            if nouveau and compteur == len(fragments) - 1:
                # Au dernier fragment lorsque NOUVEAU, simplement gaspiller
                # la boucle, de manière à exécuter sa clause "else:".
                continue
            # Sauver le chemin partiel avec le bon code, s'il existe.
            if partiel is None:
                if not fragment:
                    partiel = ""''
                    break
                hypothese = fragment.encode(essai)
            else:
                hypothese = partiel + ""'/' + fragment.encode(essai)
            if os.path.exists(hypothese):
                partiel = hypothese
                break
        else:
            # Le fragment de chemin n'existe pas, retourner ce que l'on a
            # déjà pu trouver, en utilisant le code implicite pour le reste.
            if partiel is None:
                partiel = ""''
            else:
                partiel += ""'/'
            if code is None:
                code = TERMINAL
            try:
                return partiel + u'/'.join(fragments[compteur:]).encode(code)
            except UnicodeEncodeError:
                assert False, (partiel, compteur, fragments, code)
    return partiel

class Filtre:

    def __new__(cls, stream, encoding=None, errors=None):
        if u'b' in getattr(stream, u'mode', u''):
            return stream
        return object.__new__(cls)

    def __init__(self, stream, encoding=None, errors=None):
        self.stream = stream
        self.encoding = encoding
        self.errors = errors

    def __getattr__(self, attribut):
        return getattr(self.stream, attribut)

    def __iter__(self):
        return self

    def next(self):
        return reunicode(self.stream.next(), self.encoding, self.errors)

    def read(self, *args, **defs):
        return reunicode(self.stream.read(*args, **defs),
                         self.encoding, self.errors)

    def readline(self, *args, **defs):
        return reunicode(self.stream.readline(*args, **defs),
                         self.encoding, self.errors)

    def readlines(self, *args, **defs):
        lignes = self.stream.readlines(*args, **defs)
        encoding = self.encoding
        errors = self.errors
        return [reunicode(ligne, encoding, errors) for ligne in lignes]

    def write(self, tampon):
        self.stream.write(tampon.encode(self.encoding or TERMINAL,
                                        self.errors or ERREURS))

    def writelines(self, sequence):
        for tampon in sequence:
            self.write(tampon)

sys = _sys()
