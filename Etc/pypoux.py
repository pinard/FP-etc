#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003-10.

"""\
Vérifier et critiquer les fichiers et sources Python présents.

pypoux [OPTION]... [ARGUMENT]...

Options:
  -h   Fournir cette aide, et ne rien faire d'autre.
  -v   Imprimer une ligne pour chaque vérification.

Les ARGUMENTs sont ignorés.  Le programme examine les fichiers du
répertoire courant, ainsi que tous ses sous-répertoires, récursivement.
"""

# Ce module vérifie et critique tous les sources Python dans la
# hiérarchie débutant au répertoire courant.  Il peut être utilisé
# soit comme programme principal, sois sous le contrôle de pytest.

# Pour en faire un élément de suite de validation, il suffit de créer
# un fichier nommé "test_*.py", dans le projet à vérifier, qui
# contienne la ligne: "from Local.pypoux import *".

__metaclass__ = type
import sys

class Main:
    volubile = False

    def main(self, *arguments):
        import getopt
        options, arguments = getopt.getopt(arguments, 'hv')
        for option, value in options:
            if option == '-h':
                sys.stdout.write(__doc__)
                return
            elif option == '-v':
                self.volubile = True
        setup_module(None)
        write = sys.stderr.write
        courant = None
        for compteur, arguments in enumerate(Test_Poux().test_chacun()):
            test, fichier = arguments
            if self.volubile:
                if fichier.startswith('./'):
                    fichier = fichier[2:]
                if fichier != courant:
                    courant = marge = fichier
                write('%d. %s %s\n'
                      % (compteur + 1, marge, test.__func__.__name__))
                marge = ' ' * len(marge)
            try:
                test(fichier)
            except AssertionError:
                pass
        teardown_module(None)

run = Main()
main = run.main

def setup_module(module):
    import tempfile
    run.repertoire = tempfile.mkdtemp()

def teardown_module(module):
    import shutil
    shutil.rmtree(run.repertoire)

class Test_Poux:
    fichier = None
    tampon = None

    def test_chacun(self):
        for fichier in self.chaque_fichier():
            if not peut_avoir_tabs(fichier):
                yield self.verifier_tabs, fichier
            yield self.ligne_blanche_debut, fichier
            yield self.ligne_blanche_fin, fichier
            yield self.blancs_suffixes, fichier
            yield self.double_ligne_blanche, fichier
            yield self.commentaire_vide, fichier
            if est_python(fichier):
                yield self.ligne_blanche_manquante, fichier
                yield self.coding_manquant, fichier
                yield self.metaclasse_manquant, fichier
                yield self.chaines_unicode, fichier
                yield self.verifier_syntaxe, fichier

    ## Espace blanc.

    def verifier_tabs(self, fichier):
        self.garantir_tampon(fichier)
        self.position = self.tampon.find('\t')
        assert self.position < 0, self.rapporter("Caractère TAB.")

    def ligne_blanche_debut(self, fichier):
        self.garantir_tampon(fichier)
        self.position = 0
        assert not self.tampon.startswith('\n'), (
                self.rapporter("Ligne blanche au début."))

    def ligne_blanche_fin(self, fichier):
        self.garantir_tampon(fichier)
        self.position = len(self.tampon)
        assert not self.tampon.endswith('\n\n'), (
                self.rapporter("Ligne blanche à la fin."))

    def blancs_suffixes(self, fichier):
        self.garantir_tampon(fichier)
        self.position = self.tampon.find(' \n')
        assert self.position < 0, self.rapporter("Espace blanc suffixe.")

    def double_ligne_blanche(self, fichier):
        self.garantir_tampon(fichier)
        self.position = self.tampon.find('\n\n\n')
        assert self.position < 0, self.rapporter("Double ligne blanche.")

    def commentaire_vide(self, fichier):
        self.garantir_tampon(fichier)
        self.position = self.tampon.find('#\n')
        assert self.position < 0, self.rapporter("Commentaire vide.")

    def ligne_blanche_manquante(self, fichier):
        self.garantir_tampon(fichier)
        self.position = 0
        blanche = False
        for ligne in self.tampon.splitlines():
            if ligne:
                mots = ligne.split(None, 1)
                if mots:
                    if (len(mots) == 1 and mots[0][0] == '@'
                            and mots[0][1].isalpha()):
                        assert blanche, self.rapporter(
                            "Ligne blanche manquante.")
                        blanche = True
                    elif mots and mots[0] in ('class', 'def'):
                        assert blanche, self.rapporter(
                            "Ligne blanche manquante.")
                        blanche = False
                    else:
                        blanche = False
                else:
                    blanche = True
            else:
                blanche = True
            self.position += len(ligne) + 1

    ## Lignes obligées en Python.

    def coding_manquant(self, fichier):
        self.garantir_tampon(fichier)
        if not self.tampon:
            return
        self.position = self.tampon.find('# -*- coding: UTF-8 -*-\n')
        if self.position < 0:
            self.position = 0
            assert False, self.rapporter("Biscuit coding manquant.")

    def metaclasse_manquant(self, fichier):
        self.garantir_tampon(fichier)
        if not self.tampon:
            return
        self.position = self.tampon.find('__metaclass__ = type\n')
        if self.position < 0:
            self.position = 0
            assert False, self.rapporter("Méta-classe n'est pas `type'.")

    ## Syntaxe Python correcte.

    def chaines_unicode(self, fichier):
        import token, tokenize
        # Attention: cStringIO ne traite pas Unicode.  Grrr!
        from io import StringIO
        erreur = None
        self.garantir_tampon(fichier)
        # Noter la position de chaque ligne.
        self.lignes = [0, 0]
        position = 0
        while True:
            position = self.tampon.find('\n', position) + 1
            if not position:
                break
            self.lignes.append(position)
        self.lignes.append(len(self.tampon))
        # Analyser le source Python.
        self.position = 0
        chaine_vide = None
        try:
            for (categ, jeton, (srow, scol), (erow, ecol), ligne
                    ) in tokenize.generate_tokens(
                            StringIO(self.tampon).readline):
                self.position = self.lignes[srow] + scol
                if categ != token.STRING:
                    if chaine_vide is not None:
                        diagnostic = self.rapporter("Chaîne vide non Unicode.")
                        if erreur is None:
                            erreur = diagnostic
                        chaine_vide = None
                    continue
                # C'est une chaîne.
                position = 0
                while jeton[position].isalpha():
                    position += 1
                if 'u' in jeton[:position] or 'U' in jeton[:position]:
                    chaine_vide = None
                    continue
                # Ça n'est pas une chaîne unicode.
                if chaine_vide:
                    # Laisser passer si précédée d'une chaîne vide.
                    chaine_vide = None
                    continue
                if jeton in ('\'\'', '""'):
                    chaine_vide = jeton
                    continue
                diagnostic = self.rapporter("Chaîne `%s' non Unicode." % jeton)
                if erreur is None:
                    erreur = diagnostic
                self.position = self.lignes[erow] + ecol
        except tokenize.TokenError as exception:
            assert False, self.rapporter("Erreur de jeton: %s." % exception)
        assert erreur is None, erreur

    def verifier_syntaxe(self, fichier):
        pyc = os.path.basename(fichier)
        if pyc.endswith('.py'):
            pyc += 'c'
        else:
            pyc += '.pyc'
        import py_compile
        try:
            py_compile.compile(fichier.encode('UTF-8'),
                               os.path.join(run.repertoire, pyc),
                               doraise=True)
        except py_compile.PyCompileError as exception:
            sys.stdout.write(str(exception))
            assert False

    ## Services.

    def chaque_fichier(self):
        pile = ['.']
        while pile:
            pile.sort()
            repertoire = pile.pop(0)
            bases = os.listdir(repertoire)
            bases.sort()
            for base in bases:
                fichier = os.path.join(repertoire, base)
                if os.path.isdir(fichier):
                    if est_repertoire_acceptable(base):
                        pile.append(fichier)
                else:
                    if est_fichier_acceptable(base):
                        yield fichier

    def garantir_tampon(self, fichier):
        if fichier != self.fichier:
            self.fichier = fichier
            self.tampon = file(fichier).read()

    def rapporter(self, diagnostic):
        ligne = self.tampon[:self.position].count('\n') + 1
        position = self.tampon.rfind('\n', 0, self.position)
        if position < 0:
            colonne = self.position + 1
        else:
            colonne = self.position - position
        sys.stdout.write('%s:%d:%d: %s\n'
                         % (self.fichier, ligne, colonne, diagnostic))
        return diagnostic

def est_fichier_acceptable(base):
    if base in ('tags', 'TAGS'):
        return False
    if base.startswith('.'):
        return False
    if base.startswith('#'):
        return False
    if base.endswith('-'):
        return False
    if base.endswith(',v'):
        return False
    if base.endswith('~'):
        return False
    if os.path.splitext(base)[1] in (
            # REVOIR: .c66 ne devrait pas être là!!
            '.703', '.c66', 'défi', '.doc', '.gif', '.jpg', '.pdf',
            '.pickle', '.png', '.pyc', '.tmp', '.zip'):
        return False
    return True

def est_repertoire_acceptable(base):
    if base in ('CVS', 'RCS'):
        return False
    if base.startswith('.'):
        return False
    if base.startswith('build-'):
        return False
    if base.endswith('~'):
        return False
    return True

def peut_avoir_tabs(fichier):
    if os.path.basename(fichier) in ('Makefile',):
        return True
    if os.path.splitext(fichier)[1] in ('.htm',):
        return True
    return False

def est_python(fichier):
    if fichier.endswith('.py'):
        return True
    ligne = file(fichier).readline()
    if ligne.startswith('#!') and ligne.endswith('python\n'):
        return True
    return False

if __name__ == '__main__':
    main(*sys.argv[1:])
