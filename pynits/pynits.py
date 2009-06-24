#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2004, 2005 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2004.

"""\
A few supplementary tools for Python support within Vim.

This script may also be used as a program, rather than imported within
Vim, mainly for debugging purposes.  The first Python line of FILE is
read and reformatted on standard output, the remainder of FILE is ignored.

Usage: pynits.py [OPTION]... [FILE]

Operation mode:
  -h   Print this help and exit.
  -d   Enable debugging trace.
  -P   Enable code profiling.

Enabling heuristics:
  -b   Columnar formatting, no refilling.
  -c   Columnar formatting, with refilling.
  -l   Format all on a single line, `-w' ignored.
  -p   Full formatting, no refilling.
  -q   Full formatting, with refilling (default).

Formatting options:
  -w WIDTH   Line width in columns (default is 80).
  -i STEP    Indentation step in columns (default is 4).

If FILE is not specified, standard input is read.
"""

__metaclass__ = type
import gettext, os, re, sys

try:
    import vim
except ImportError:
    class vim:
        class error(Exception): pass
        class current:
            buffer = []
            class window: cursor = 1, 0
        def eval(texte):
            return {'&shiftwidth': str(Editeur.indentation),
                    '&textwidth': str(Editeur.limite)}[texte]
        eval = staticmethod(eval)
        def command(texte): pass
        command = staticmethod(command)

localedir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locale')
try:
    _ = gettext.translation('pynits', localedir).gettext
except IOError:
    def _(texte): return texte

def declarer_ordinaux(*noms):
    # Déclarer, dans l'espace local de l'appelant, des variables énumératives
    # dont les NOMS sont fournis en arguments, et retourner ce type précis
    # dont les variables juste créées sont les seuls éléments.  Lorsque
    # qu'imprimées, ces variables affichent leur nom plutôt que leur valeur.
    class Ordinal(int):
        def __new__(cls, nom, valeur):
            return int.__new__(cls, valeur)
        def __init__(self, nom, valeur):
            self.nom = nom
        def __repr__(self):
            return self.nom
        def __str__(self):
            return self.nom
    locaux = sys._getframe(1).f_locals
    for valeur, nom in enumerate(noms):
        locaux[nom] = Ordinal(nom, valeur)
    return Ordinal

class Main:
    def __init__(self):
        self.commande = None

    def main(self, *arguments):
        profilage = False
        import getopt
        options, arguments = getopt.getopt(arguments, 'Pbcdhi:lpqw:')
        for option, valeur in options:
            if option == '-P':
                profilage = True
            elif option == '-b':
                self.commande = disposeur.disposer_en_colonne
            elif option == '-c':
                self.commande = disposeur.disposer_en_colonne_remplir
            elif option == '-d':
                Editeur.mise_au_point = True
            elif option == '-i':
                Editeur.indentation = int(valeur)
            elif option == '-h':
                sys.stdout.write(_(__doc__))
                sys.exit(0)
            elif option == '-l':
                self.commande = disposeur.disposer_en_ligne
            elif option == '-p':
                self.commande = disposeur.disposer_en_retrait
            elif option == '-q':
                self.commande = disposeur.disposer_en_retrait_remplir
            elif option == '-w':
                Editeur.limite = int(valeur)
        assert len(arguments) < 2, arguments
        if arguments:
            fichier = file(arguments[0])
        else:
            fichier = sys.stdin
        if self.commande is None:
            self.commande = disposeur.disposer_en_retrait_remplir
        vim.current.buffer[:] = fichier.read().splitlines()
        if profilage:
            import profile, pstats
            profile.run('run.commande(\'n\')', '.profile-data')
            sys.stderr.write('\n')
            stats = pstats.Stats('.profile-data')
            stats.strip_dirs().sort_stats('time', 'cumulative').print_stats(10)
        else:
            self.commande('n')
            sys.stderr.write('\n')
        for ligne in vim.current.buffer[:curseur_courant()[0]]:
            sys.stdout.write(ligne + '\n')

def installer_vim():
    # REVOIR: Je ne réussis pas à utiliser ni `,s' ni `,t': bizarre!
    # REVOIR: Délai inexpliqué pour les commandes `,c' et `,m'.
    register_local_keys(
        'pynits',
        (('<LocalLeader><LocalLeader>', 'n', 'trouver_broutille'),
         ('<LocalLeader>"', 'n', 'forcer_guillemets'),
         ('<LocalLeader>\'', 'n', 'forcer_apostrophes'),
         ('<LocalLeader>(', 'n', 'ajouter_parentheses'),
         ('<LocalLeader>)', 'n', 'eliminer_parentheses'),
         ('<LocalLeader>.', 'n', 'corriger_broutille'),
         ('<LocalLeader>b', 'n', 'disposer_en_colonne'),
         ('<LocalLeader>c', 'n', 'disposer_en_colonne_remplir'),
         ('<LocalLeader>d', 'n', 'choisir_mise_au_point'),
         ('<LocalLeader>f', 'n', 'choisir_remplisseur'),
         ('<LocalLeader>l', 'n', 'disposer_en_ligne'),
         ('<LocalLeader>p', 'n', 'disposer_en_retrait'),
         ('<LocalLeader>q', 'n', 'disposer_en_retrait_remplir'),
         ('<LocalLeader>y', 'n', 'montrer_syntaxe'),
         ('Q', 'n', 'disposer_en_retrait_remplir')))
    Editeur.indentation = int(vim.eval('&shiftwidth'))
    Editeur.limite = int(vim.eval('&textwidth')) or 80

def register_local_keys(plugin, triplets):
    for keys, modes, name in triplets:
        for mode in modes:
            python_command = ':python %s.%s(\'%s\')' % (plugin, name, mode)
            sid_name = '<SID>%s_%s' % (mode, name)
            plug_name = '<Plug>%s_%s_%s' % (plugin.capitalize(), mode, name)
            vim.command('%smap <buffer> %s %s' % (mode, keys, plug_name))
            vim.command('%snoremap <buffer> <script> %s %s'
                        % (mode, plug_name, sid_name))
            if mode == 'i':
                vim.command('%snoremap <buffer> <silent> %s <C-O>%s<CR>'
                            % (mode, sid_name, python_command))
            else:
                vim.command('%snoremap <buffer> <silent> %s %s<CR>'
                            % (mode, sid_name, python_command))

def ajuster_codage():
    if vim.eval('&filetype') != 'python':
        return
    codage = vim.eval('&fileencoding') or vim.eval('&encoding')
    substitutions = {'latin1': 'ISO-8859-1'}
    codage = substitutions.get(codage, codage).lower()
    tampon = vim.current.buffer
    for index in 0, 1:
        if index < len(tampon):
            ligne = tampon[index]
            # En théorie: coding[=:]\s*([-\w-.]+)
            match = re.match(r'(#.*?-\*-.*coding: *)([-_A-Za-z0-9]*)(.*)',
                             ligne)
            if match:
                ligne = match.expand(r'\1%s\3' % codage)
                if ligne != tampon[index]:
                    tampon[index] = ligne
                return
    index = 0
    if index < len(tampon) and tampon[index].startswith('#!'):
        index = 1
    tampon[index:index] = ['# -*- coding: %s -*-' % codage]

## Redisposition contrôlée par la syntaxe.

import compiler, compiler.ast, compiler.consts, compiler.visitor

# Noeuds syntaxiques bidon représentant quelques codes Python accessoires.
# L'attribut RUSTINE a pour effet d'empêcher la productin de `pass'.
class Elif(compiler.ast.If):
    rustine = True
class Else(compiler.ast.Pass):
    rustine = True
class Except(compiler.ast.Tuple):
    rustine = True
class Finally(compiler.ast.Pass):
    rustine = True
class Try(compiler.ast.Pass):
    rustine = True

class Disposeur:

    # Limite en lignes d'exploration vers l'arrière pour trouver le début
    # d'une ligne logique de code Python.
    limite_arriere = 12

    # Limite en lignes de l'exploration vers l'avant pour trouver la fin
    # d'une ligne logique de code Python.
    limite_avant = 200

    # Outil à utiliser pour remplir les commentaires.
    choix_remplisseurs = 'fmt', 'par', 'vim', 'python'
    remplisseur = 'fmt'

    def montrer_syntaxe(self, mode):
        # Imprimer la syntaxe d'une ligne (pour aider la mise-au-point).
        rangee = curseur_courant()[0]
        try:
            debut, fin, marge, commentaires, arbre = self.trouver_ligne_python(
                rangee)
        except SyntaxError, diagnostic:
            sys.stderr.write(str(diagnostic))
        else:
            sys.stdout.write(str(arbre))

    def disposer_en_ligne(self, mode):
        Editeur.strategie = LIGNE
        self.traiter_ligne(None)

    def disposer_en_colonne(self, mode):
        Editeur.strategie = COLONNE
        self.traiter_ligne(False)

    def disposer_en_colonne_remplir(self, mode):
        Editeur.strategie = COLONNE
        self.traiter_ligne(True)

    def disposer_en_retrait(self, mode):
        Editeur.strategie = RETRAIT
        self.traiter_ligne(False)

    def disposer_en_retrait_remplir(self, mode):
        Editeur.strategie = RETRAIT
        self.traiter_ligne(True)

    def traiter_ligne(self, remplir):
        # Redisposer la ligne et remplir selon REMPLIR.
        rangee = curseur_courant()[0]
        tampon = vim.current.buffer
        ligne = tampon[rangee].lstrip()
        if ligne.startswith('#'):
            fin = self.traiter_commentaire(rangee)
        elif ligne:
            fin = self.traiter_code_python(rangee, remplir)
        else:
            fin = self.traiter_blanche(rangee)
        # Placer le curseur sur la ligne suivante.
        if fin <= len(tampon):
            colonne = marge_gauche(tampon[fin-1])
        else:
            fin = len(tampon)
            colonne = 0
        try:
            changer_curseur_courant(fin, colonne)
        except vim.error:
            # REVOIR: Il y a erreur Vim en disposant, par exemple, `x = 0.0'.
            pass

    def traiter_blanche(self, rangee):
        debut = fin = rangee
        tampon = vim.current.buffer
        if '\f' in tampon[rangee]:
            insertion = '\f\n'
        else:
            insertion = '\n'
        while debut > 1 and not tampon[debut-2].lstrip():
            debut -= 1
            if '\f' in tampon[debut-1]:
                insertion = '\f\n'
        while fin < len(tampon) and not tampon[fin].lstrip():
            fin += 1
            if '\f' in tampon[fin-1]:
                insertion = '\f\n'
        return self.modifier_tampon(debut, fin + 1, insertion)

    def traiter_commentaire(self, rangee):
        debut = fin = rangee
        tampon = vim.current.buffer
        prefixe = ' '*marge_gauche(tampon[rangee]) + '#'
        while debut > 1 and tampon[debut-2].startswith(prefixe):
            debut -= 1
        while fin < len(tampon) and tampon[fin].startswith(prefixe):
            fin += 1
        if self.remplisseur == 'vim':
            vim.command('normal %dGgq%dG' % (debut, fin))
            return curseur_courant()[0]
        if self.remplisseur == 'fmt':
            import os, tempfile
            nom = tempfile.mktemp()
            file(nom, 'w').writelines([tampon[rangee] + '\n'
                                       for rangee in range(debut, fin + 1)])
            insertion = (os.popen('fmt -u -w%d -p\'%s\' <%s'
                                  % (Editeur.limite, prefixe + ' ', nom))
                         .read)()
            os.remove(nom)
        elif self.remplisseur == 'par':
            import os, tempfile
            nom = tempfile.mktemp()
            file(nom, 'w').writelines([tampon[rangee] + '\n'
                                       for rangee in range(debut, fin + 1)])
            # REVOIR: Examiner PARINIT et voir s'il faut l'intégrer.
            insertion = os.popen('par w%d <%s' % (Editeur.limite, nom)).read()
            os.remove(nom)
        elif self.remplisseur == 'python':
            import textwrap
            lignes = [tampon[rangee][len(prefixe):]
                      for rangee in range(debut, fin + 1)]
            insertion = textwrap.fill(textwrap.dedent('\n'.join(lignes)),
                                      width=Editeur.limite,
                                      fix_sentence_endings=True,
                                      initial_indent=prefixe + ' ',
                                      subsequent_indent=prefixe + ' ')
        return self.modifier_tampon(debut, fin + 1, insertion)

    def traiter_code_python(self, rangee, remplir):
        try:
            debut, fin, marge, commentaires, arbre = self.trouver_ligne_python(
                rangee)
        except SyntaxError, diagnostic:
            sys.stderr.write(str(diagnostic))
            return rangee
        editeur = Editeur(marge, remplir)
        try:
            compiler.walk(arbre, editeur,
                          walker=compiler.visitor.ExampleASTVisitor(),
                          verbose=True)
        except Impasse, diagnostic:
            if not remplir:
                sys.stderr.write('%s...' % str(diagnostic))
                return rangee
            editeur = Editeur(marge, False)
            try:
                compiler.walk(arbre, editeur,
                              walker=compiler.visitor.ExampleASTVisitor(),
                              verbose=True)
            except Impasse, diagnostic2:
                sys.stderr.write('%s...' % str(diagnostic))
                return rangee
            sys.stderr.write(_("I ought to disable filling."))
        resultat = str(editeur)
        if resultat.endswith(':\n'):
            resultat += self.recommenter(marge + editeur.indentation,
                                         commentaires)
        else:
            resultat = self.recommenter(marge, commentaires) + resultat
        return self.modifier_tampon(debut, fin, resultat)

    def trouver_ligne_python(self, rangee):
        # Lire le code Python qui débute à la RANGEE donnée ou, au besoin
        # d'une syntaxe correcte, jusqu'à une douzaine de lignes plus tôt.
        # Retourner (DEBUT, FIN, MARGE, COMMENTAIRES, ARBRE), indiquant la
        # première et la dernière rangée du code Python trouve, la grandeur
        # de la marge, une liste des fragments de commentaire trouvés dans
        # le code Python, et un ARBRE syntaxique représentatif du code trouvé.
        debut = rangee
        while True:
            try:
                fin, marge, commentaires, texte = self.lire_ligne_python(debut)
                # En reculant suffisamment, on peut trouver du code Python
                # valide, mais si ce code ne rejoint pas au moins la ligne
                # de départ, il faut probablement reculer davantage.
                if fin <= rangee:
                    raise SyntaxError(
                        _("Syntax error, maybe did not back up enough?"))
                if texte.endswith(':\n'):
                    for prefixe in 'class ', 'def ', 'if ', 'for ', 'while ':
                        if texte.startswith(prefixe):
                            rustine = True
                            texte = texte[:-2].rstrip() + ': pass\n'
                            break
                    else:
                        for prefixe, classe in (('try:', Try),
                                                ('else:', Else),
                                                ('finally:', Finally)):
                            if texte.startswith(prefixe):
                                rustine = classe
                                texte = 'pass'
                                break
                        else:
                            if texte.startswith('elif '):
                                texte = texte[2:-2].rstrip() + ': pass\n'
                                rustine = Elif
                            elif texte == 'except:\n':
                                texte = '()'
                                rustine = Except
                            elif texte.startswith('except '):
                                texte = texte[7:-2].strip() + ',\n'
                                rustine = Except
                            else:
                                rustine = None
                else:
                    rustine = None
                from parser import ParserError
                try:
                    arbre = compiler.parse(texte)
                except ParserError, diagnostic:
                    raise SyntaxError(diagnostic)
            except SyntaxError:
                # S'il y a une quelconque erreur de syntaxe, la ligne physique
                # n'était peut-être pas la première de la ligne logique.
                # On tente alors l'analyse à nouveau en reculant d'une ligne
                # physique, mais quand même, pas plus d'une douzaine de fois.
                if debut < 1 or debut <= rangee - self.limite_arriere:
                    raise
                debut -= 1
            else:
                # Nous avons enfin un arbre syntaxique utilisable.
                break
        if rustine:
            assert isinstance(arbre, compiler.ast.Module), arbre
            assert isinstance(arbre.node, compiler.ast.Stmt), arbre.node
            assert len(arbre.node.nodes) == 1, arbre.node.nodes
            noeud = arbre.node.nodes[0]
            if rustine is True:
                # Nous avons class, def, if, for ou while.  RUSTINE a pour
                # effet d'inhiber la production de l'énoncé `pass'.
                noeud.rustine = True
            elif isinstance(noeud, compiler.ast.Pass):
                # Nous avons try, else ou finally.
                arbre.node.nodes[0] = rustine()
            elif isinstance(noeud, compiler.ast.If):
                # Nous avons elif.
                arbre.node.nodes[0] = rustine(noeud.tests, noeud.else_)
            else:
                # Nous avons except.
                assert isinstance(noeud, compiler.ast.Discard), noeud
                assert isinstance(noeud.expr, compiler.ast.Tuple), noeud.expr
                noeud.expr = rustine(noeud.expr.nodes)
        return debut, fin, marge, commentaires, arbre

    def lire_ligne_python(self, rangee):
        # Lire le code Python qui débute à la RANGÉE donnée, en lisant
        # au besoin les lignes de continuation.  Retourner (FIN, MARGE,
        # COMMENTAIRES, TEXTE), indiquant la ligne suivant l'énoncé trouvé,
        # la grandeur de la marge, une liste des fragments de commentaire
        # trouvés dans le code Python, puis le texte complet du code Python
        # sous la forme d'une seule chaîne, y compris les fins de ligne,
        # mais sans la marge de départ ni les commentaires.
        debut = rangee
        tampon = vim.current.buffer
        ligne = tampon[rangee].rstrip()
        marge = marge_gauche(ligne)
        commentaires = []
        lignes = []
        pile = []
        ligne = ligne.lstrip()
        quelque_chose = False
        while True:
            lignes.append(ligne)
            while ligne:
                if ligne[0] in '([{':
                    quelque_chose = True
                    pile.append({'(': ')', '[': ']', '{': '}'}[ligne[0]])
                    ligne = ligne[1:].lstrip()
                    continue
                if ligne[0] in ')]}':
                    quelque_chose = True
                    if not pile:
                        raise SyntaxError(_("Spurious `%s'.") % ligne[0])
                    attendu = pile.pop()
                    if ligne[0] != attendu:
                        raise SyntaxError(_("`%s' seen, `%s' expected!")
                                          % (ligne[0], attendu))
                    ligne = ligne[1:].lstrip()
                    continue
                if ligne.startswith('#'):
                    lignes[-1] = lignes[-1][:-len(ligne)].rstrip()
                    if ligne.startswith('# '):
                        commentaires.append(ligne[2:])
                    else:
                        commentaires.append(ligne[1:])
                    break
                if ligne == '\\':
                    if rangee >= len(tampon):
                        break
                    rangee += 1
                    ligne = tampon[rangee].lstrip()
                    lignes.append(ligne)
                    continue
                match = re.match(r'u?r?(\'\'\'|""")', ligne)
                if match:
                    quelque_chose = True
                    terminateur = match.group(1)
                    ligne = ligne[match.end():]
                    while terminateur not in ligne:
                        if (rangee - debut == self.limite_avant
                              or rangee + 1 >= len(tampon)):
                            ligne = None
                            break
                        rangee += 1
                        ligne = tampon[rangee].rstrip()
                        lignes.append(ligne)
                    else:
                        position = ligne.find(terminateur)
                        ligne = ligne[position+3:].lstrip()
                    continue
                match = re.match(r'u?r?(\'([^\\\']+|\\.)*\'|"([^\\"]+|\\.)*")',
                                 ligne)
                if match:
                    quelque_chose = True
                    ligne = ligne[match.end():].lstrip()
                    continue
                ligne = ligne[1:].lstrip()
                quelque_chose = True
            if not pile and quelque_chose:
                break
            if len(lignes) == self.limite_avant or rangee + 1 >= len(tampon):
                if pile:
                    raise SyntaxError(_("`%s' expected!")
                                      % '\', `'.join(pile[::-1]))
                raise SyntaxError(_("No Python code!"))
            rangee += 1
            ligne = tampon[rangee].strip()
        return (debut + len(lignes), marge, commentaires,
                '\n'.join(lignes) + '\n')

    def recommenter(self, marge, commentaires):
        while commentaires:
            if not commentaires[-1]:
                del commentaires[-1]
            elif not commentaires[0]:
                del commentaires[0]
            else:
                break
        if commentaires:
            if commentaires[-1][-1] not in '.!?':
                commentaires[-1] += '.'
            while len(commentaires) > 1 and not commentaires[0]:
                commentaires.pop(0)
            if commentaires[0][0].islower():
                commentaires[0] = (commentaires[0][0].upper()
                                   + commentaires[0][1:])
        lignes = []
        for commentaire in commentaires:
            if commentaire:
                lignes.append(' '*marge + '# ' + commentaire + '\n')
            else:
                lignes.append(' '*marge + '#\n')
        return ''.join(lignes)

    def modifier_tampon(self, debut, fin, texte):
        lignes = texte.splitlines()
        tampon = vim.current.buffer
        if fin - debut != len(lignes) or tampon[debut:fin] != lignes:
            tampon[debut:fin] = lignes
        return debut + len(lignes)

disposeur = Disposeur()
montrer_syntaxe = disposeur.montrer_syntaxe
disposer_en_ligne = disposeur.disposer_en_ligne
disposer_en_colonne = disposeur.disposer_en_colonne
disposer_en_colonne_remplir = disposeur.disposer_en_colonne_remplir
disposer_en_retrait = disposeur.disposer_en_retrait
disposer_en_retrait_remplir = disposeur.disposer_en_retrait_remplir

## Outil d'édition d'un arbre syntaxique.

declarer_ordinaux('NON_ASSOC', 'ASSOC_GAUCHE', 'ASSOC_DROITE')

def preparer_editeur():
    # Cette fonction modifie les classes structurales de `compiler.ast' pour
    # leur ajouter les notions de priorité, d'associativité et possiblement
    # aussi, la chaîne représentant l'opérateur.  Ces informations sont
    # bien utiles, par exemple pour choisir quand et comment insérer des
    # parenthèses lors de la reconstruction de la surface d'un énoncé Python.
    for donnees in (
            (0, NON_ASSOC, 'AssTuple', 'Tuple'),
            (1, NON_ASSOC, 'Lambda'),
            (2, ASSOC_GAUCHE, ('Or', 'or')),
            (3, ASSOC_GAUCHE, ('And', 'and')),
            (4, NON_ASSOC, ('Not', 'not')),
            (5, ASSOC_GAUCHE, 'Compare'),
            (6, ASSOC_GAUCHE, ('Bitor', '|')),
            (7, ASSOC_GAUCHE, ('Bitxor', '^')),
            (8, ASSOC_GAUCHE, ('Bitand', '&')),
            (9, ASSOC_GAUCHE, ('LeftShift', '<<'), ('RightShift', '>>')),
            (10, ASSOC_GAUCHE, ('Add', '+'), ('Sub', '-')),
            (11, ASSOC_GAUCHE, ('Div', '/'), ('FloorDiv', '//'), ('Mod', '%'),
                               ('Mul', '*')),
            (12, ASSOC_DROITE, ('Power', '**')),
            (13, NON_ASSOC, ('Invert', '~'), ('UnaryAdd', '+'),
                            ('UnarySub', '-')),
            (14, ASSOC_GAUCHE, 'AssAttr', 'AssList', 'CallFunc', 'Getattr',
                               'Slice', 'Subscript'),
            (15, NON_ASSOC, 'AssName', 'Backquote', 'Const', 'Dict', 'List',
                            'ListComp', 'Name'),
            ):
        priorite = donnees[0]
        associativite = donnees[1]
        for paire in donnees[2:]:
            if isinstance(paire, tuple):
                nom_classe, operateur = paire
            else:
                nom_classe = paire
                operateur = None
            classe = getattr(compiler.ast, nom_classe)
            setattr(classe, 'priorite', priorite)
            setattr(classe, 'associativite', associativite)
            setattr(classe, 'operateur', operateur)

preparer_editeur()

# La priorité à l'extérieur de toute expression, ou immédiatement à l'intérieur
# de parenthèses de priorité ou de cisèlement.
PRIORITE_ENONCE = -1
# La priorité à l'intérieur d'un tuple.  C'est aussi la priorité lorsqu'un
# nouveau tuple doit nécessairement être niché dans des parenthèses.
PRIORITE_TUPLE = 0
# La priorité jusqu'à laquelle un blanc est garanti de part et d'autre des
# opérateurs.  Au delà de cette priorité, la présence de blancs est décidé
# par la variable ESPACEMENTS.
PRIORITE_ESPACEMENT = 6
# La priorité des phénomènes tels que l'appel de fonction, l'indiçage et le
# choix d'attributs.  Ces phénomènes sont associatifs à gauche entre eux,
# et les parenthèses sont supprimées directement dans la fonction EDITER.
PRIORITE_APPEL = 14

# Énumération des diverses stratégies de disposition.  Garder en ordre!
declarer_ordinaux('LIGNE', 'COLONNE', 'RETRAIT')

# Lorsqu'une tentative de disposition aboutit dans un cul-de-sac logique.
class Impasse(Exception): pass

# Quelques caractères spéciaux utilisés dans la sortie de mise-au-point.
POINT_AU_CENTRE = '·'
PIED_DE_MOUCHE = '¶'

class Editeur:
    # Un ÉDITEUR se comporte comme un "visiteur" syntaxique pour le module
    # `compile'.  Il sait obéir à des formats et accumule la structure de
    # surface au fur et à mesure de sa construction.  De plus, il orchestre
    # une mécanique de continuations qui s'activent lors d'impasses.

    # La mise au point est plutôt verbeuse.
    mise_au_point = False

    # Accroissement de la marge par niveau d'intentation.
    indentation = 4

    # Les lignes doivent idéalement tenir dans 80 colonnes par défaut.
    limite = 80

    # La stratégie maximale, qui limite les stratégies de disposition.
    strategie = RETRAIT

    # RECRITURE_SANS note quelques améliorations stylistiques ponctuellement
    # demandées par l'utilisateur, mais inactives par défaut, qui portent
    # en elles un léger risque de modifier la sémantique du résultat.
    # Sont admissibles: 'apply', 'find', 'has_key', 'print' et 'string'.
    recriture_sans = []

    def __init__(self, marge, remplir):
        # BLOCS est une liste de blocs de lignes.  Chacun de ces blocs
        # est une chaîne contenant une ou plusieurs lignes, y compris les
        # terminateurs de ligne.  La caractéristique d'un bloc de plus d'une
        # ligne est qu'il ne peut participer à une opération de remplissage.
        self.blocs = []
        # LIGNE donne le nombre de lignes complétées ou débutées.
        self.ligne = 0
        # COLONNE donne le nombre de colonnes dans la dernière ligne.
        self.colonne = 0
        # MARGES est une pile de marges.  Chaque marge donne le nombre de
        # blancs en début de toute nouvelle ligne.
        self.marges = [marge]
        # FLOTTEMENTS est une pile de flottements.  Chaque flottement donne un
        # nombre de colonnes libres à garantir sur la dernière ligne produite,
        # une sorte de marge droite supplémentaire.
        self.flottements = [0]
        # REMPLIR à True indique que l'on doit remplir les lignes produites
        # tantque la marge ne change pas, False ou None sinon.  La valeur
        # None indique en plus qu'il n'y a pas de nombre maximum de colonnes.
        self.remplir = remplir
        # DEBUTS est une pile de débuts.  Chaque début est le numéro d'un
        # bloc à partir duquel un remplissage aura lieu.
        self.debuts = []
        # Niveau de récursion dans les appels à EDITER, pour fins de trace.
        self.profondeur = 0
        # Imbrication courante de parenthèses explicities.
        self.imbrication = 0
        # PRIORITES est une pile de priorités.  Une priorité qualifie le
        # texte couramment engendré.
        self.priorites = [PRIORITE_ENONCE]
        # ENONCE_DEL indique qu'il s'agit d'un énoncé `del' et que le mot-clé
        # `del' est déjà écrit.
        self.enonce_del = False
        # MARGES2 est une pile de secondes marges.  Chaque seconde marge
        # peut établir un minimum supplémentaire pour la marge.  Voir la
        # documentation de la fonction EDITER pour plus de détails.
        self.marges2 = [None]
        # ESPACEMENTS est une pile d'espacements.  Chaque espacement contrôle
        # l'économie possible de certaines espaces.  Voir la documentation
        # de la fonction EDITER pour plus de détails.
        self.espacements = [2]
        # ECONOMIE peut provoquer l'économie d'une paire de parentheèse.
        # Voir la documentation de la fonction EDITER pour plus de détails.
        self.economie = False
        # STRATEGIES est une pile de stratégies.  Chaque stratégie est en
        # train d'être essayée à un niveau d'imbrication particulier.
        self.strategies = [LIGNE]

    def __str__(self):
        return ('\n'.join([ligne.rstrip(' ')
                           for ligne in ''.join(self.blocs).splitlines()])
                + '\n')

    def debug_format(self, format, arguments, position, index):
        if Editeur.mise_au_point:
            cadre = sys._getframe()
            while True:
                cadre = cadre.f_back
                nom = cadre.f_code.co_name
                for prefixe in 'visit', 'operateur_':
                    if nom.startswith(prefixe):
                        break
                else:
                    continue
                break
            self.debug_texte((format[:position].replace('%', '')
                              + POINT_AU_CENTRE
                              + format[position:].replace('%', '')),
                             *((nom[len(prefixe):] + ':',) + arguments[:index]
                               + (POINT_AU_CENTRE,) + arguments[index:]))

    def debug_texte(self, *arguments):
        if Editeur.mise_au_point:
            self.debug(*arguments)
            if self.blocs:
                sys.stdout.write(''.join(self.blocs) + PIED_DE_MOUCHE + '\n')

    def debug(self, *arguments):
        if Editeur.mise_au_point:
            write = sys.stdout.write
            write('%-16s' % ('%2d %d,%s,%d %d%s'
                             % (self.priorites[-1],
                                self.marges[-1], self.marges2[-1] or '',
                                self.flottements[-1], self.espacements[-1],
                                ('', '-')[self.economie])))
            write('%*d' % (-self.profondeur, self.profondeur))
            assert self.strategies[0] == LIGNE, self.strategies
            if len(self.strategies) > 1:
                write(' ')
                write(''.join([str(strategie)[0]
                               for strategie in self.strategies[1:]]))
            for argument in arguments:
                write(' ')
                if argument is None:
                    write('-')
                elif isinstance(argument, str):
                    if len(argument) > 16:
                        write(argument[:13] + '...')
                    else:
                        write(argument)
                elif isinstance(argument, compiler.ast.Node):
                    write(argument.__class__.__name__)
                else:
                    write(repr(argument))
            write('\n')

    ## Énoncés.

    def visitAssert(self, noeud):
        format = 'assert%#'
        arguments = [PRIORITE_TUPLE]
        if noeud.fail is None:
            format += ' %^'
            arguments += [noeud.test]
        else:
            format += ' %(%!%^%|%), %^'
            arguments += [None, noeud.test, noeud.fail]
        self.traiter(format, *arguments)

    def visitAssign(self, noeud):
        format = ''
        arguments = []
        for gauche in noeud.nodes:
            format += '%(%^%|%) = '
            arguments += [None, gauche]
        format += '%(%!%^%)'
        arguments += [None, noeud.expr]
        self.traiter(format, *arguments)

    def visitAugAssign(self, noeud):
        self.traiter('%(%^%|%) %s %(%!%^%)', None, noeud.node, noeud.op, None,
                     noeud.expr)

    def visitBreak(self, noeud):
        self.traiter('break')

    def visitContinue(self, noeud):
        self.traiter('continue')

    def visitDiscard(self, noeud):
        self.traiter('%^', noeud.expr)

    def visitElif(self, noeud):
        assert len(noeud.tests) == 1, noeud.tests
        for test, enonce in noeud.tests:
            self.traiter('elif %;%^%:', test)
            self.traiter_corps(noeud, enonce)
        assert noeud.else_ is None, noeud.else_

    def visitElse(self, noeud):
        self.traiter('else:')

    def visitExcept(self, noeud):
        if len(noeud.nodes) == 0:
            self.traiter('except:')
        elif len(noeud.nodes) == 1:
            self.traiter('except %;%^%:', noeud.nodes[0])
        else:
            self.traiter('except %;%^%:', compiler.ast.Tuple(noeud.nodes))

    def visitExec(self, noeud):
        format = 'exec%#'
        arguments = [PRIORITE_TUPLE]
        if noeud.globals is None:
            if noeud.locals is None:
                format += ' %^'
                arguments += [noeud.expr]
            else:
                format += ' %(%!%^%|%) in %^'
                arguments += [None, noeud.expr, noeud.locals]
        else:
            format += ' %(%!%^%|%) in %(%!%^%|%), %^'
            arguments += [None, noeud.expr, None, noeud.locals, noeud.globals]
        self.traiter(format, *arguments)

    def visitFinally(self, noeud):
        self.traiter('finally:')

    def visitFor(self, noeud):
        self.traiter('for %;%^ in %^%:', noeud.assign, noeud.list)
        self.traiter_corps(noeud, noeud.body)
        assert noeud.else_ is None, noeud.else_

    def visitFrom(self, noeud):
        format = 'from %s import'
        arguments = [noeud.modname]
        separateur = ' '
        for nom, alias in noeud.names:
            format += separateur + '%s'
            arguments += [nom]
            if alias is not None:
                format += ' alias %s'
                arguments += [alias]
            separateur = ', '
        self.traiter(format, *arguments)

    def visitGlobal(self, noeud):
        format = 'global'
        arguments = []
        separateur = ' '
        for nom in noeud.names:
            format += separateur + '%s'
            arguments += [nom]
            separateur = ', '
        self.traiter(format, *arguments)

    def visitIf(self, noeud):
        separateur = 'if'
        assert len(noeud.tests) == 1, noeud.tests
        for test, enonce in noeud.tests:
            self.traiter('%s %;%^%:', separateur, test)
            self.traiter_corps(noeud, enonce)
            separateur = 'elif'
        assert noeud.else_ is None, noeud.else_

    def visitImport(self, noeud):
        format = 'import'
        arguments = []
        separateur = ' '
        for nom, alias in noeud.names:
            format += separateur + '%s'
            arguments += [nom]
            if alias is not None:
                format += ' as %s'
                arguments += [alias]
            separateur = ', '
        self.traiter(format, *arguments)

    def visitPass(self, noeud):
        self.traiter('pass')

    def visitPrint(self, noeud):
        self.traiter_print(noeud, False)

    def visitPrintnl(self, noeud):
        self.traiter_print(noeud, True)

    def visitRaise(self, noeud):
        format = 'raise%#'
        arguments = [PRIORITE_TUPLE]
        if noeud.expr3 is None:
            if noeud.expr2 is None:
                if noeud.expr1 is not None:
                    format += ' %^'
                    arguments += [noeud.expr1]
            else:
                format += ' %(%!%^%|%), %^'
                arguments += [None, noeud.expr1, noeud.expr2]
        else:
            format = ' %(%!%^%|%), %(%!%^%|%), %^'
            arguments += [None, noeud.expr1, None, noeud.expr2, noeud.expr3]
        self.traiter(format, *arguments)

    def visitReturn(self, noeud):
        if est_none(noeud.value):
            format = 'return'
            arguments = []
        else:
            format = 'return %^'
            arguments = [noeud.value]
        self.traiter(format, *arguments)

    def visitTry(self, noeud):
        self.traiter('try:')

    def visitTryExcept(self, noeud):
        # body, handlers, else_
        assert False

    def visiTryFinally(self):
        assert False

    def visitWhile(self, noeud):
        self.traiter('while %;%^%:', noeud.test)
        self.traiter_corps(noeud, noeud.body)
        assert noeud.else_ is None, noeud.else_

    def visitYield(self, noeud):
        self.traiter('yield %^', noeud.value)

    ## Expressions.

    def operateur_unaire(self, noeud):
        operateur = noeud.operateur
        if operateur.isalpha():
            format = '%(%s %^%)'
        else:
            format = '%(%s%^%)'
        self.espacements[-1] -= 1
        self.traiter(format, noeud.priorite, operateur, noeud.expr)
        self.espacements[-1] += 1

    def operateur_binaire(self, noeud):
        priorite = noeud.priorite
        if noeud.associativite == ASSOC_DROITE:
            format = '%(%(%^%_%|%s%_'
            arguments = [priorite, None, noeud.left, noeud.operateur]
            noeud = noeud.right
            while noeud == priorite:
                format += '%^%_%|%s%_'
                arguments += [noeud.left, noeud.operateur]
                noeud = noeud.right
            format += '%^%)%)'
            arguments += [noeud]
        else:
            paires = []
            while noeud.priorite == priorite:
                paires.append((noeud.operateur, noeud.right))
                noeud = noeud.left
            paires.reverse()
            format = '%(%(%^'
            arguments = [priorite, None, noeud]
            for operateur, expression in paires:
                format += '%_%|%s%_%^'
                arguments += [operateur, expression]
            format += '%)%)'
        self.espacements[-1] -= 1
        self.traiter(format, *arguments)
        self.espacements[-1] += 1

    def operateur_masquage(self, noeud):
        self.espacements[-1] -= 1
        self.operateur_multiple(noeud)
        self.espacements[-1] += 1

    def operateur_multiple(self, noeud):
        format = '%(%(%^'
        arguments = [noeud.priorite, None, noeud.nodes[0]]
        for expression in noeud.nodes[1:]:
            if noeud.operateur.isalpha():
                format += ' %|%s %^'
            else:
                format += '%_%|%s%_%^'
            arguments += [noeud.operateur, expression]
        format += '%)%)'
        self.traiter(format, *arguments)

    visitAdd = operateur_binaire
    visitAnd = operateur_multiple

    def visitBackquote(self, noeud):
        self.traiter('repr(%^)', noeud.expr)

    visitBitand = operateur_masquage
    visitBitor = operateur_masquage
    visitBitxor = operateur_masquage

    def visitCallFunc(self, noeud):
        if (self.recrire_sans_apply(noeud) or self.recrire_sans_has_key(noeud)
              or self.recrire_sans_string(noeud)):
            return
        compte = (len(noeud.args) + bool(noeud.star_args)
                  + bool(noeud.dstar_args))
        if compte == 0:
            self.traiter('%(%^()%)', noeud.priorite, noeud.node)
            return
        format = '%!%(%^(%\\'
        arguments = [noeud.priorite, noeud.node, PRIORITE_TUPLE]
        if compte == 1:
            format += '%!'
        separateur = ''
        for expression in noeud.args:
            format += separateur + '%^'
            arguments += [expression]
            separateur = ', %|'
        if noeud.star_args is not None:
            format += separateur + '*%^'
            arguments += [noeud.star_args]
            separateur = ', %|'
        if noeud.dstar_args is not None:
            format += separateur + '**%^'
            arguments += [noeud.dstar_args]
        format += ')%)%/'
        self.traiter(format, *arguments)

    def visitCompare(self, noeud):
        if self.recrire_sans_find(noeud):
            return
        format = '%(%^'
        arguments = [noeud.priorite, noeud.expr]
        for operateur, comparand in noeud.ops:
            if operateur.isalpha():
                format += ' %|%s %^'
            else:
                format += '%_%|%s%_%^'
            arguments += [operateur, comparand]
        format += '%)'
        self.traiter(format, *arguments)

    def visitConst(self, noeud):
        if isinstance(noeud.value, str):
            self.traiter_chaine(noeud.value)
        elif isinstance(noeud.value, (int, float)):
            self.traiter_constante(noeud.value)
        else:
            assert False, (type(noeud.value), noeud.value)

    def visitDict(self, noeud):
        format = '%!%({%\\'
        arguments = [noeud.priorite, PRIORITE_TUPLE]
        separateur = ''
        for cle, valeur in noeud.items:
            format += separateur + '%^: %^'
            arguments += [cle, valeur]
            separateur = ', %|'
        format += '}%)%/'
        self.traiter(format, *arguments)

    visitDiv = operateur_binaire
    visitFloorDiv = operateur_binaire

    def visitGetattr(self, noeud):
        attributs = [noeud.attrname]
        noeud = noeud.expr
        while isinstance(noeud, compiler.ast.Getattr):
            attributs.append(noeud.attrname)
            noeud = noeud.expr
        attributs.reverse()
        self.traiter('%(%^' + '%|.%s'*len(attributs) + '%)', noeud.priorite,
                     noeud, *attributs)

    visitInvert = operateur_unaire

    def visitLambda(self, noeud):
        flags = noeud.flags
        ordinaires = noeud.argnames[:]
        if noeud.kwargs:
            assert flags & compiler.consts.CO_VARKEYWORDS, flags
            flags &= ~compiler.consts.CO_VARKEYWORDS
            dstar_args = ordinaires.pop()
        else:
            dstar_args = None
        if noeud.varargs:
            assert flags & compiler.consts.CO_VARARGS, flags
            flags &= ~compiler.consts.CO_VARARGS
            star_args = ordinaires.pop()
        else:
            star_args = None
        assert not flags, flags
        if noeud.defaults:
            cles = ordinaires[-len(noeud.defaults):]
            ordinaires = ordinaires[:-len(noeud.defaults)]
        format = '%(lambda'
        arguments = [noeud.priorite]
        separateur = ' '
        for ordinaire in ordinaires:
            format += separateur + '%s'
            arguments += [ordinaire]
            separateur = ', %|'
        if noeud.defaults:
            for cle, valeur in zip(cles, noeud.defaults):
                format += separateur + '%s=%^'
                arguments += [cle, valeur]
                separateur = ', %|'
        if star_args is not None:
            format += separateur + '*%s'
            arguments += [star_args]
            separateur = ', %|'
        if dstar_args is not None:
            format += separateur + '**%s'
            arguments += [dstar_args]
        format += ': %^%)'
        arguments += [noeud.code]
        self.traiter(format, *arguments)

    visitLeftShift = operateur_binaire

    def visitList(self, noeud):
        format = '%!%([%\\'
        if len(noeud.nodes) == 1:
            format += '%!'
        arguments = [PRIORITE_APPEL, PRIORITE_TUPLE]
        separateur = ''
        for expression in noeud.nodes:
            format += separateur + '%^'
            arguments += [expression]
            separateur = ', %|'
        format += ']%)%/'
        self.traiter(format, *arguments)

    def visitListComp(self, noeud):
        self.traiter(r'%!%([%\%^' + '%^'*len(noeud.quals) + ']%)%/',
                     PRIORITE_APPEL, PRIORITE_TUPLE, noeud.expr, *noeud.quals)

    visitMod = operateur_binaire
    visitMul = operateur_binaire

    def visitName(self, noeud):
        self.traiter('%s', noeud.name)

    visitNot = operateur_unaire
    visitOr = operateur_multiple
    visitPower = operateur_binaire
    visitRightShift = operateur_binaire

    def visitSlice(self, noeud):
        format = self.peut_etre_del(noeud) + '%^%!%([%\\'
        arguments = [noeud.expr, noeud.priorite, PRIORITE_ENONCE]
        if noeud.lower is not None:
            format += '%|%^'
            arguments += [noeud.lower]
        format += '%|:'
        if noeud.upper is not None:
            format += '%^'
            arguments += [noeud.upper]
        format += ']%)%/'
        self.traiter(format, *arguments)

    visitSub = operateur_binaire

    def visitSubscript(self, noeud):
        indices = noeud.subs
        # REVOIR: Le cas du 1-tuple n'est pas simplifié, pour être consistant
        # avec un bug dans `compiler': d[0] et d[0,] n'y sont pas distingués.
        if (len(indices) == 1 and isinstance(indices[0], compiler.ast.Tuple)
              and len(indices[0].nodes) > 1):
            indices = indices[0].nodes
        format = self.peut_etre_del(noeud) + '%(%^%!%([%\\'
        arguments = [noeud.priorite, noeud.expr, None, PRIORITE_TUPLE]
        if len(indices) == 1:
            format += '%!%^'
            arguments += indices
        else:
            format += ', %|'.join(['%^'] * len(indices))
            for indice in indices:
                arguments += [indice]
        format += ']%)%)%/'
        self.traiter(format, *arguments)

    def visitTuple(self, noeud):
        if len(noeud.nodes) == 0:
            format = '()'
            arguments = []
        elif len(noeud.nodes) == 1:
            format = '%(%!%^,%)'
            arguments = [PRIORITE_TUPLE, noeud.nodes[0]]
        else:
            format = '%('
            arguments = [PRIORITE_TUPLE]
            separateur = ''
            for expression in noeud.nodes:
                format += separateur + '%^'
                arguments += [expression]
                separateur = ', %|'
            format += '%)'
        self.traiter(format, *arguments)

    visitUnaryAdd = operateur_unaire
    visitUnarySub = operateur_unaire

    ## Structuration et divers.

    def visitAssAttr(self, noeud):
        format = self.peut_etre_del(noeud)
        attributs = [noeud.attrname]
        noeud = noeud.expr
        while isinstance(noeud, compiler.ast.Getattr):
            attributs.append(noeud.attrname)
            noeud = noeud.expr
        attributs.reverse()
        self.traiter(format + '%(%^' + '%|.%s'*len(attributs) + '%)',
                     noeud.priorite, noeud, *attributs)

    def visitAssName(self, noeud):
        self.traiter(self.peut_etre_del(noeud) + '%s', noeud.name)

    visitAssList = visitList
    visitAssTuple = visitTuple

    def visitClass(self, noeud):
        format = 'class %s%;'
        arguments = [noeud.name]
        if noeud.bases:
            format += '('
            separateur = ''
            for base in noeud.bases:
                format += separateur + '%^'
                arguments += [base]
                separateur = ', %|'
            format += ')'
        format += '%:'
        self.traiter(format, *arguments)
        assert noeud.doc is None, noeud.doc
        self.traiter_corps(noeud, noeud.code)

    def visitEllipsis(self, noeud):
        self.traiter('...')

    def visitFunction(self, noeud):
        flags = noeud.flags
        ordinaires = noeud.argnames[:]
        if noeud.kwargs:
            assert flags & compiler.consts.CO_VARKEYWORDS, flags
            flags &= ~compiler.consts.CO_VARKEYWORDS
            dstar_args = ordinaires.pop()
        else:
            dstar_args = None
        if noeud.varargs:
            assert flags & compiler.consts.CO_VARARGS, flags
            flags &= ~compiler.consts.CO_VARARGS
            star_args = ordinaires.pop()
        else:
            star_args = None
        assert not flags, flags
        if noeud.defaults:
            cles = ordinaires[-len(noeud.defaults):]
            ordinaires = ordinaires[:-len(noeud.defaults)]
        format = 'def %s%;(%\\'
        arguments = [noeud.name, PRIORITE_TUPLE]
        separateur = ''
        for ordinaire in ordinaires:
            format += separateur + '%s'
            arguments += [ordinaire]
            separateur = ', %|'
        if noeud.defaults:
            for cle, valeur in zip(cles, noeud.defaults):
                format += separateur + '%s=%^'
                arguments += [cle, valeur]
                separateur = ', %|'
        if star_args is not None:
            format += separateur + '*%s'
            arguments += [star_args]
            separateur = ', %|'
        if dstar_args is not None:
            format += separateur + '**%s'
            arguments += [dstar_args]
        format += ')%:%/'
        self.traiter(format, *arguments)
        assert noeud.doc is None, noeud.doc
        self.traiter_corps(noeud, noeud.code)

    def visitKeyword(self, noeud):
        self.traiter('%s=%^', noeud.name, noeud.expr)

    def visitListCompFor(self, noeud):
        self.traiter(' %|for %#%^ in %^' + '%^'*len(noeud.ifs),
                     PRIORITE_ENONCE, noeud.assign, noeud.list, *noeud.ifs)

    def visitListCompIf(self, noeud):
        self.traiter(' %|if %^', noeud.test)

    def visitModule(self, noeud):
        if noeud.doc is None:
            self.traiter('%^', noeud.node)
        else:
            assert isinstance(noeud.node, compiler.ast.Stmt)
            assert len(noeud.node.nodes) == 0, noeud.node
            self.traiter_chaine(noeud.doc, triple=True)

    def visitSliceobj(self, noeud):
        format = ''
        arguments = []
        separateur = '%|'
        for expression in noeud.nodes:
            format += separateur
            if not est_none(expression):
                format += '%^'
                arguments += [expression]
            separateur = '%|:'
        self.traiter(format, *arguments)

    def visitStmt(self, noeud):
        assert len(noeud.nodes) == 1, noeud
        self.traiter('%^' * len(noeud.nodes), *noeud.nodes)

    ## Récritures spécialisées.

    def recrire_sans_apply(self, noeud):
        if 'apply' not in self.recriture_sans:
            return
        from compiler.ast import CallFunc, Name
        if (isinstance(noeud, CallFunc) and len(noeud.args) == 2
              and not (noeud.star_args or noeud.dstar_args)
              and isinstance(noeud.node, Name) and noeud.node.name == 'apply'):
            self.visit(CallFunc(noeud.args[0], (), star_args=noeud.args[1]))
            return True
        return False

    def recrire_sans_find(self, noeud):
        if 'find' not in self.recriture_sans:
            return
        from compiler.ast import CallFunc, Compare, Const, Getattr, UnarySub
        if (isinstance(noeud, Compare) and len(noeud.ops) == 1
              and isinstance(noeud.expr, CallFunc)
              and len(noeud.expr.args) == 1
              and not (noeud.expr.star_args or noeud.expr.dstar_args)
              and isinstance(noeud.expr.node, Getattr)
              and noeud.expr.node.attrname == 'find'):
            operateur, comparand = noeud.ops[0]
            if (isinstance(comparand, UnarySub)
                  and isinstance(comparand.expr, Const)
                  and comparand.expr.value == 1):
                if operateur == '==':
                    operateur = 'not in'
                elif operateur == '!=':
                    operateur = 'in'
                else:
                    return False
            elif isinstance(comparand, Const) and comparand.value == 0:
                if operateur == '<':
                    operateur = 'not in'
                elif operateur == '>=':
                    operateur = 'in'
                else:
                    return False
            self.visit(Compare(noeud.expr.args[0],
                               [(operateur, noeud.expr.node.expr)]))
            return True
        return False

    def recrire_sans_has_key(self, noeud):
        if 'has_key' not in self.recriture_sans:
            return
        from compiler.ast import CallFunc, Compare, Getattr, Name
        if (isinstance(noeud, CallFunc) and len(noeud.args) == 1
              and not (noeud.star_args or noeud.dstar_args)
              and isinstance(noeud.node, Getattr)
              and noeud.node.attrname == 'has_key'):
            self.visit(Compare(noeud.args[0], [('in', noeud.node.expr)]))
            return True
        return False

    def recrire_sans_print(self, noeud, nl):
        if 'print' not in self.recriture_sans:
            return
        from compiler.ast import Add, CallFunc, Const, Getattr, Mod, Name, Tuple
        format = ''
        arguments = []
        separateur = ''
        for expression in noeud.nodes:
            if (isinstance(expression, Mod)
                  and isinstance(expression.left, Const)
                  and isinstance(expression.left.value, str)):
                format += separateur + expression.left.value
                if isinstance(expression.right, Tuple):
                    arguments += expression.right.nodes
                else:
                    arguments += [expression.right]
            elif (isinstance(expression, Const)
                  and isinstance(expression.value, str)
                  and '%' not in expression.value):
                format += separateur + expression.value
            else:
                format += separateur + '%s'
                arguments += [expression]
            separateur = ' '
        if nl:
            separateur = '\n'
        if noeud.dest is None:
            dest = Getattr(Name('sys'), 'stdout')
        else:
            dest = noeud.dest
        if len(arguments) == 0:
            self.visit(CallFunc(Getattr(dest, 'write'),
                                [Const(format + separateur)]))
        elif len(arguments) == 1:
            if format == '%s':
                if (isinstance(arguments[0], Const)
                      and isinstance(arguments[0].value, str)):
                    self.visit(
                        CallFunc(Getattr(dest, 'write'),
                                 [Const(arguments[0].value + separateur)]))
                else:
                    self.visit(
                        CallFunc(Getattr(dest, 'write'),
                                 [Add([CallFunc(Name('str'), arguments),
                                       Const(separateur)])]))
            else:
                self.visit(CallFunc(Getattr(dest, 'write'),
                                    [Mod([Const(format + separateur),
                                          arguments[0]])]))
        else:
            self.visit(CallFunc(Getattr(dest, 'write'),
                                [Mod([Const(format + separateur),
                                      Tuple(arguments)])]))
        return True

    def recrire_sans_string(self, noeud):
        if 'string' not in self.recriture_sans:
            return
        from compiler.ast import CallFunc, Const, Getattr, Name
        if (isinstance(noeud, CallFunc) and len(noeud.args) > 0
              and not (noeud.star_args or noeud.dstar_args)
              and isinstance(noeud.node, Getattr)
              and isinstance(noeud.node.expr, Name)
              and noeud.node.expr.name == 'string'):
            methode = noeud.node.attrname
            if methode == 'join':
                if len(noeud.args) == 1:
                    self.visit(CallFunc(Getattr(Const(' '), 'join'),
                                        [noeud.args[0]]))
                    return True
                if len(noeud.args) == 2:
                    self.visit(CallFunc(Getattr(noeud.args[1], 'join'),
                                        [noeud.args[0]]))
                    return True
            elif methode in ('capitalize', 'center', 'count', 'expandtabs',
                             'find', 'index', 'ljust', 'lower', 'lstrip',
                             'replace', 'rfind', 'rindex', 'rjust', 'rstrip',
                             'split', 'strip', 'swapcase', 'translate',
                             'upper', 'zfill'):
                self.visit(CallFunc(Getattr(noeud.args[0], methode),
                                    noeud.args[1:]))
                return True
        return False

    ## Méthodes de service.

    def peut_etre_del(self, noeud):
        if self.enonce_del:
            assert noeud.flags == compiler.consts.OP_DELETE, (
                noeud, noeud.flags)
            return ''
        if noeud.flags == compiler.consts.OP_DELETE:
            self.enonce_del = True
            return 'del '
        assert noeud.flags in (compiler.consts.OP_APPLY,
                               compiler.consts.OP_ASSIGN), (noeud, noeud.flags)
        return ''

    def traiter_corps(self, noeud, enonce):
        assert isinstance(enonce, compiler.ast.Stmt), enonce
        assert len(enonce.nodes) == 1, enonce
        if not hasattr(noeud, 'rustine'):
            self.traiter(r'%\ %|%^%/', PRIORITE_ENONCE, enonce.nodes[0])

    def traiter_print(self, noeud, nl):
        if self.recrire_sans_print(noeud, nl):
            return
        format = 'print%#'
        arguments = [PRIORITE_TUPLE]
        separateur = ' '
        if noeud.dest is not None:
            format += separateur + '>>%^'
            arguments += [noeud.dest]
            separateur = ', '
        for expression in noeud.nodes:
            format += separateur + '%^'
            arguments += [expression]
            separateur = ', '
        if not nl:
            format += ','
        self.traiter(format, *arguments)

    # REVOIR: Peut-être transporter le type original? (raw, '', "", """)
    def traiter_chaine(self, texte, triple=False):
        # Formatter TEXTE au mieux.  Si TRIPLE, forcer un triple délimiteur.

        # MEILLEURE est la longueur de la plus grande séquence de lettres.
        # SEQUENCE est la longueur de la séquence de lettres la plus récente.
        # COMPTEUR est le nombre de lettres dans tout TEXTE.
        meilleure = 0
        sequence = 0
        compteur = 0
        for caractere in texte:
            if caractere.isalpha():
                compteur += 1
                sequence += 1
            else:
                if sequence > meilleure:
                    meilleure = sequence
                sequence = 0

        # DELIMITEUR reçoit le meilleur délimiteur pour représenter TEXTE,
        # c'est-à-dire un guillemet si la chaîne semble être écrite en
        # langue naturelle, ou un apostrophe autrement.  Comment déterminer
        # si une chaîne est un fragment en langue naturelle?  Je dois me
        # contenter d'heuristiques simples.
        # REVOIR: Une chaîne comprise dans _() devrait toujours utiliser ".

        # Voici celle que Richard Stallman m'a suggérée et que j'ai mise
        # en application dans `po-mode.el'.  Trois lettres d'affilée?
        # Alors oui.  Jamais deux lettres d'affilée?  Alors non.  Sinon,
        # alors oui si plus de lettres que de non-lettres.  Mais ce code ne
        # me satisfait pas vraiment, je le laisse en commentaire ici!
        if False:
            if meilleure >= 3 or meilleure == 2 and 2 * compteur > len(texte):
                delimiteur = '"'
            else:
                delimiteur = '\''
        # Je préfère tenter l'heuristique suivante, qui considère qu'un
        # fragment est en langue naturelle si un blanc y apparaît, si l'on
        # y trouve un mot d'au moins quatre lettres, et s'il y a au moins
        # deux fois plus de lettres que de non-lettres.
        if ' ' in texte and meilleure >= 4 and 3 * compteur > len(texte):
            delimiteur = '"'
        else:
            delimiteur = '\''
        # RAW indique si l'on doit préfixer la chaîne par `r'.
        raw = meilleure_en_raw(texte, delimiteur)

        def essai_delimiteur_ligne():
            # Tenter une disposition tout d'un pain sur une ligne.
            self.write(chaine_python(texte, delimiteur))

        def essai_delimiteur_simple():
            # Tenter une disposition avec des délimiteurs simples, quitte
            # à découper la chaîne en plusieurs morceaux à concaténer et à
            # disposer chacun sur une ligne.
            if raw:
                format_debut = 'r' + delimiteur
            else:
                format_debut = delimiteur
                substitutions = {delimiteur: '\\' + delimiteur, '\\': r'\\',
                                 '\a': r'\a', '\b': r'\b', '\f': r'\f',
                                 '\n': r'\n', '\t': r'\t', '\v': r'\v'}
            format_fin = '%s' + delimiteur
            format = '%(' + format_debut
            arguments = [None]
            # Effectuer une édition bidon, juste pour savoir dans quelle
            # colonne la chaîne débuterait.  Nous prévoierons nous-mêmes
            # les coupures de ligne une fois cette colonne connue.
            reprise = Reprise(self)
            self.traiter(format, *arguments)
            marge = colonne = self.colonne
            reprise.ramener()
            del reprise.editeur
            # Formatter un mot à la fois, blancs préfixes inclus.  Changer de
            # ligne si il n'y a plus de place pour le mot.
            strategie = self.strategies[-1]
            remplir = self.remplir
            # On imagine un fragment bidon au début, qui est nul, dans le
            # but d'inhiber une seconde production d'un début de format.
            fragments_ligne = ['']
            fragments_mot = ['']
            write = fragments_mot.append
            BLANC, NOIR = range(2)
            etat = BLANC
            for caractere in texte:
                if caractere == ' ':
                    if etat == NOIR:
                        if fragments_mot:
                            mot = ''.join(fragments_mot)
                            del fragments_mot[:]
                            # S'assurer de deux colonnes de jeu pour récrire
                            # le délimiteur si la chaîne doit être brisée sur
                            # plusieurs lignes, et pour la parenthèse fermante
                            # clôturant une série de chaînes concaténées.
                            if (remplir is not None
                                  and colonne + len(mot) > Editeur.limite - 2):
                                if strategie == LIGNE:
                                    raise Impasse(_("String too long"))
                                format += format_fin
                                arguments += [''.join(fragments_ligne)]
                                del fragments_ligne[:]
                                colonne = marge
                            if not fragments_ligne:
                                format += '%|' + format_debut
                            fragments_ligne.append(mot)
                            colonne += len(mot)
                        etat = BLANC
                    write(' ')
                else:
                    etat = NOIR
                    if raw:
                        write(caractere)
                    elif caractere in substitutions:
                        write(substitutions[caractere])
                    elif not est_imprimable(caractere):
                        write(repr(caractere)[1:-1])
                    else:
                        write(caractere)
                    if caractere == '\n':
                        mot = ''.join(fragments_mot)
                        del fragments_mot[:]
                        # Pour le `-2', voir le commentaire plus haut.
                        if (remplir is not None
                              and colonne + len(mot) > Editeur.limite - 2):
                            if strategie == LIGNE:
                                raise Impasse(_("String too long"))
                            format += format_fin
                            arguments += [''.join(fragments_ligne)]
                            del fragments_ligne[:]
                        if not fragments_ligne:
                            format += '%|' + format_debut
                        fragments_ligne.append(mot)
                        format += format_fin
                        arguments += [''.join(fragments_ligne)]
                        del fragments_ligne[:]
                        colonne = marge
                        etat = BLANC
            if fragments_mot:
                mot = ''.join(fragments_mot)
                # Pour le `-2', voir le commentaire plus haut.
                if (remplir is not None
                      and colonne + len(mot) > Editeur.limite - 2):
                    if strategie == LIGNE:
                        raise Impasse(_("String too long"))
                    format += format_fin
                    arguments += [''.join(fragments_ligne)]
                    del fragments_ligne[:]
                if not fragments_ligne:
                    format += '%|' + format_debut
                fragments_ligne.append(mot)
            if fragments_ligne:
                format += format_fin
                arguments += [''.join(fragments_ligne)]
            format += '%)'
            if remplir is not None:
                self.remplir = False
            try:
                self.traiter(format, *arguments)
            finally:
                self.remplir = remplir

        def essai_delimiteur_triple():
            # Tenter une disposition avec un triple délimiteur.
            fragments = []
            write = fragments.append
            if raw:
                write('r' + delimiteur*3 + '\\\n')
            else:
                write(delimiteur*3 + '\\\n')
                # `\n' se substitue par lui-même, tout simplement.
                substitutions = {'\n': '\n', '\\': r'\\', '\a': r'\a',
                                 '\b': r'\b', '\f': r'\f', '\v': r'\v'}
            if texte:
                for caractere in texte:
                    if raw:
                        write(caractere)
                    elif caractere in substitutions:
                        write(substitutions[caractere])
                    elif not est_imprimable(caractere):
                        write(repr(caractere)[1:-1])
                    else:
                        write(caractere)
            else:
                caractere = None
            if caractere != '\n':
                write('\\\n')
            write(delimiteur * 3)
            self.write(''.join(fragments))

        if triple:
            essai_delimiteur_triple()
        elif self.strategies[-1] == LIGNE or len(texte) < 25:
            essai_delimiteur_ligne()
        else:
            self.profondeur += 1
            try:
                def fonction((routine, strategie)):
                    self.strategies.append(strategie)
                    routine()
                    del self.strategies[-1]
                branchement = (
                    Branchement(self, None, None, fonction,
                                ((essai_delimiteur_ligne, LIGNE),
                                 (essai_delimiteur_simple, COLONNE),
                                 (essai_delimiteur_triple, COLONNE))))
                for position, index, fonction, avenue in branchement:
                    try:
                        fonction(avenue)
                    except Impasse:
                        pass
                    else:
                        branchement.sauver_solution()
                branchement.completer()
            finally:
                self.profondeur -= 1

    def traiter_constante(self, valeur):
        # Formatter la constante VALEUR, qui ne peut être une chaîne.
        if isinstance(valeur, float):
            sys.stderr.write(
                _("WARNING: floating values are not dependable.\n"
                  "(There is a bug in `import compiler'.  Sigh!)"))
        self.write(repr(valeur))

    def traiter(self, format, *arguments):
        # Produire FORMAT en sortie tout en interprétant les séquences
        # formées d'un pourcent et d'une lettre de spécification.  Certaines
        # spécifications consomment l'un des ARGUMENTS supplémentaires fournis,
        # tous les arguments doivent être finalement consommés par le format.

        # La séquence `%%' produit un seul `%'.  `%_' produit une espace
        # ou non, selon la priorité courante ou la valeur de ESPACEMENTS,
        # ESPACEMENTS indique un nombre de niveaux d'expression pour
        # lesquels on ajoute un blanc de part et d'autre de chaque opérateur.
        # S'il vaut zéro ou est négatif, de tels blancs ne sont pas ajoutés.
        # `%s' et `%^' disposent respectivement une chaîne ou un sous-arbre,
        # fournis en argument.

        # `%(' et `%)' encadrent un fragment de texte dont la priorité est
        # possiblement différente, la nouvelle priorité est donnée en argument
        # pour `%(', cet argument est None si la priorité ne doit pas changer.
        # Le fragment de texte est placé entre parenthèses si la priorité du
        # fragment n'est pas plus grande que celle du texte environnant, ou
        # encore, pour mieux souligner le cisèlement en stratégie COLONNE
        # ou RETRAIT: dans ce dernier cas, ces parenthèses permettent
        # d'introduire les lignes de continuation.  Lorsqu'une paire `%('
        # et `%)' produit effectivement des parenthèses, l'effet de `%('
        # implique automatiquement `%\' avec un argument de -1 pour la
        # nouvelle priorité, l'effet de '%)' implique automatiquement `%/'.

        # '%\' ajoute une indentation à la marge, qui sera effective pour les
        # lignes de continuation, et force aussi une nouvelle priorité fournie
        # en argument, mais sans production de parenthèses: c'est utile après
        # un délimiteur ouvrant explicite.  '%/' rétablit la marge à sa valeur
        # précédente et possiblement, tente de combiner les lignes accumulées
        # depuis le changement de marge afin de mieux remplir les lignes.
        # `%|' termine la ligne courante et force le commencement d'une autre.
        # Ces trois spécifications sont sans effet en stratégie LIGNE.

        # '%;' force, via MARGES2 qui peut fixer une marge minimum, une
        # imbrication d'au moins une indentation et demie pour les lignes
        # de continuation, quant à `%:', il produit un deux-points et annule
        # l'effet du '%;' précédent.  `%!', via ECONOMIE, commande l'économie
        # de la paire de parenthèses qui serait possiblement provoquée pour
        # fins de ciselage par le `%(' suivant; son effet est désamorcé dès
        # une écriture.  `%#' force la priorité fournie en argument.

        # Dans l'ensemble des appels successifs à EDITER pour un arbre
        # syntaxique donné, à chaque `%(' doit correspondre éventuellement un
        # `%)', à chaque `%\' un `%/', et à chaque `%;' un `%:'.

        self.profondeur += 1
        try:
            # BRANCHEMENTS est une pile de branchements.  Chaque branchement
            # est créé lors d'un `%(' et éliminé lors d'un '%)'.
            # Les changements de stratégie ne se produisent que lors d'un
            # changement de branchement.
            branchements = []
            # Travailler tant que FORMAT n'a pas été complètement consommé,
            # ou qu'une impasse ne peut être davantage récupérée.
            position = 0
            index = 0
            self.debug_format(format, arguments, position, index)
            while True:
                if position:
                    self.debug_format(format, arguments, position, index)
                try:
                    # Trouver la prochaine spécification de format, traiter
                    # le fragment de format qui nous rend jusqu'à elle.
                    precedente = position
                    position = format.find('%', precedente)
                    if position < 0:
                        if precedente < len(format):
                            self.write(format[precedente:])
                        break
                    if position > precedente:
                        self.write(format[precedente:position])
                    # Aiguiller selon la spécification.
                    specification = format[position+1]
                    position += 2
                    strategie = self.strategies[-1]
                    if specification == '%':
                        self.write('%')
                    elif specification == '_':
                        if (self.priorites[-1] <= PRIORITE_ESPACEMENT
                              or self.espacements[-1] > 0):
                            self.write(' ')
                    elif specification == 's':
                        argument = arguments[index]
                        index += 1
                        if argument:
                            self.write(argument)
                    elif specification == '^':
                        argument = arguments[index]
                        index += 1
                        # Examiner ce qui suit dans FORMAT pour choisir un
                        # flottement supplémentaire.
                        flottement = 0
                        regard = position
                        while regard < len(format):
                            if format[regard] == '%':
                                regard += 1
                                if format[regard] in '%_():':
                                    flottement += 1
                                elif format[regard] in '|':
                                    if strategie != LIGNE:
                                        if format[regard-2] == ' ':
                                            flottement -= 1
                                        break
                            else:
                                flottement += 1
                            regard += 1
                        self.flottements.append(
                            self.flottements[-1] + flottement)
                        # Formatter récursivement.
                        self.visit(argument)
                        del self.flottements[-1]
                    elif specification == '(':
                        argument = arguments[index]
                        index += 1
                        # Un branchement sauve l'état courant de l'ÉDITEUR,
                        # ainsi que la prochaine POSITION dans le format et
                        # l'INDEX du prochain argument.
                        if len(self.strategies) == 1:
                            maximale = RETRAIT
                        else:
                            maximale = self.strategies[-1]
                        avenues = [LIGNE]
                        if Editeur.strategie != LIGNE:
                            avenues.append(COLONNE)
                        if (Editeur.strategie == RETRAIT
                              and maximale == RETRAIT):
                            avenues.append(RETRAIT)
                        def fonction(strategie):
                            self.strategies.append(strategie)
                            self.imbriquer_parentheses(
                                branchement, arguments[index - 1])
                        branchement = Branchement(self, position, index,
                                                  fonction, avenues)
                        branchements.append(branchement)
                        position, index, fonction, avenue = branchement.next()
                        fonction(avenue)
                    elif specification == ')':
                        branchement = branchements[-1]
                        self.desimbriquer_parentheses(branchement)
                        del self.strategies[-1]
                        branchement.sauver_solution()
                        try:
                            position, index, fonction, avenue = (
                                branchement.next())
                        except StopIteration:
                            branchement.completer()
                            del branchements[-1]
                        else:
                            fonction(avenue)
                    elif specification == '\\':
                        argument = arguments[index]
                        index += 1
                        self.imbriquer_marge()
                        self.priorites.append(argument)
                        # Note: ESPACEMENTS est remis à zéro lorsque `%\' est
                        # utilisé explicitement (comme à la suite de `[' ou
                        # `{'), mais pas lorsque l'effet de `%\' est implicite
                        # via `%('.  Au contraire, ESPACEMENTS est forcé à deux
                        # dans un contexte semblable à l'intérieur d'un tuple.
                        if argument == PRIORITE_TUPLE:
                            self.espacements.append(2)
                        else:
                            self.espacements.append(0)
                    elif specification == '/':
                        self.desimbriquer_marge()
                        del self.priorites[-1]
                        del self.espacements[-1]
                    elif specification == '|':
                        if strategie != LIGNE:
                            self.terminer_ligne()
                    elif specification == ';':
                        self.marges2.append(self.marges[-1]
                                            + self.indentation
                                            + (self.indentation + 1)//2)
                    elif specification == ':':
                        self.write(':')
                        del self.marges2[-1]
                        self.marges.append(self.marges[-1]
                                           + self.indentation)
                    elif specification == '!':
                        self.economie = True
                    elif specification == '#':
                        argument = arguments[index]
                        index += 1
                        self.priorites[-1] = argument
                        if argument == PRIORITE_TUPLE:
                            self.espacements[-1] = 2
                    else:
                        assert False, specification
                except Impasse, diagnostic:
                    while True:
                        if not branchements:
                            raise Impasse(_("This is too difficult for me..."))
                        branchement = branchements[-1]
                        try:
                            position, index, fonction, avenue = (
                                branchement.next())
                        except StopIteration:
                            del branchements[-1]
                        else:
                            fonction(avenue)
                            break
            assert index == len(arguments), (index, arguments)
        finally:
            self.profondeur -= 1

    def imbriquer_parentheses(self, branchement, priorite):
        if (priorite is not None
              and not priorite == self.priorites[-1] == PRIORITE_APPEL
              and priorite <= self.priorites[-1]):
            parentheser = True
        elif self.strategies[-1] == LIGNE:
            parentheser = False
        elif self.economie:
            parentheser = False
            self.economie = False
        else:
            parentheser = True
        if parentheser:
            self.write('(')
            self.imbrication += 1
            branchement.fermante = ')'
            self.espacements.append(2)
            self.imbriquer_marge()
        else:
            branchement.fermante = None
            self.espacements.append(self.espacements[-1])
        if priorite is None:
            self.priorites.append(self.priorites[-1])
        else:
            self.priorites.append(priorite)

    def desimbriquer_parentheses(self, branchement):
        if branchement.fermante is not None:
            self.write(branchement.fermante)
            self.imbrication -= 1
            self.desimbriquer_marge()
        del self.priorites[-1]
        del self.espacements[-1]

    def imbriquer_marge(self):
        if self.strategies[-1] is RETRAIT:
            self.marges.append(self.marges[-1] + self.indentation)
            if self.colonne > self.marges[-1]:
                self.debuts.append(len(self.blocs))
                self.terminer_ligne()
            else:
                self.debuts.append(len(self.blocs) - 1)
        else:
            self.marges.append(max(self.colonne, self.marges[-1]))
            self.debuts.append(len(self.blocs) - 1)

    def desimbriquer_marge(self):
        # Combiner en un seul tous les blocs de ligne depuis DEBUT.
        debut = self.debuts.pop()
        if self.remplir:
            index = debut
            while index + 1 < len(self.blocs):
                if (self.blocs[index].find('\n', 0, -1) < 0
                      and self.blocs[index + 1].find('\n', 0, -1) < 0
                      and ((len(self.blocs[index])
                            + len(self.blocs[index + 1].lstrip()) - 1)
                           <= Editeur.limite)):
                    self.blocs[index] = (
                        self.blocs[index][:-1]
                        + self.blocs.pop(index + 1).lstrip())
                    self.ligne -= 1
                    continue
                index += 1
        texte = ''.join(self.blocs[debut:])
        self.blocs[debut:] = [texte]
        self.colonne = len(texte)
        position = texte.rfind('\n')
        if position >= 0:
            self.colonne -= position + 1
        # Revenir à la marge précédente.
        del self.marges[-1]

    def terminer_ligne(self):
        if not self.imbrication:
            raise Impasse(_("Newline is not nested"))
        self.write('\n')
        if self.marges2[-1] is not None:
            self.marges[-1] = max(self.marges[-1], self.marges2[-1])

    def write(self, texte):
        if self.colonne == 0:
            self.blocs.append('')
            self.ligne += 1
            texte = ' '*self.marges[-1] + texte
        self.blocs[-1] += texte
        self.colonne += len(texte)
        position = texte.rfind('\n')
        if position >= 0:
            self.ligne += texte.count('\n')
            self.colonne = len(texte) - (position + 1)
            if self.colonne == 0:
                self.ligne -= 1
        if self.texte_deborde():
            raise Impasse(_("Line overflow"))
        self.economie = False

    def texte_deborde(self):
        if (self.remplir is not None
              and self.colonne + self.flottements[-1] > Editeur.limite):
            self.debug_texte(_("Overflow"))
            return True
        return False

class Branchement:
    generation = 0

    def __init__(self, editeur, position, index, fonction, avenues):
        self.reprise = Reprise(editeur)
        self.position = position
        self.index = index
        self.fonction = fonction
        self.avenues = avenues
        # Préparer l'itérateur.
        Branchement.generation += 1
        self.generation = Branchement.generation
        self.solutions = []
        self.next = iter(self).next

    def __del__(self):
        # Briser la circularité des références.
        for solution in self.solutions:
            del solution.editeur
        if self.reprise is not None:
            del self.reprise.editeur

    def __iter__(self):
        # Produire un itérateur fournissant à la fois un ARGUMENT propre au
        # branchement et l'une des AVENUES possibles.  ARGUMENT peut contenir
        # suffisamment d'information pour recommencer l'édition comme au
        # début du branchement: c'est alors une culbute spécialisée qui remplace
        # un peu, dans ce cas-ci, les continuations que Python n'offre pas.
        if not self.avenues:
            raise Impasse(_("This is too difficult for me..."))
        editeur = self.reprise.editeur
        for compteur, avenue in enumerate(self.avenues):
            if compteur > 0:
                self.reprise.ramener()
            editeur.debug('@%d %d/%d' % (Branchement.generation,
                                         compteur + 1,
                                         len(self.avenues)))
            yield self.position, self.index, self.fonction, avenue

    def sauver_solution(self):
        editeur = self.reprise.editeur
        self.solutions.append(Reprise(editeur))
        editeur.debug(_("Save-%d") % len(self.solutions))

    def completer(self):
        if not self.solutions:
            raise Impasse(_("This is too difficult for me..."))
        solution = min(self.solutions)
        if len(self.solutions) > 1:
            for compteur, reprise in enumerate(self.solutions):
                reprise.debug_texte(
                    '%s %d/%d' % (('  ', '->')[reprise is solution],
                                  compteur + 1, len(self.solutions)),
                    reprise.ligne, reprise.poids_visuel())
        solution.ramener()

class Reprise(Editeur):
    # Un point de reprise peut sauver, ou remettre en place, les listes et
    # les entiers contenus comme attributs dans un éditeur.  Il se garde
    # aussi contre les modifications ultérieures des listes dans l'éditeur.

    def __init__(self, editeur):
        self.editeur = editeur
        for nom, valeur in editeur.__dict__.iteritems():
            if isinstance(valeur, list):
                setattr(self, nom, valeur[:])
            elif isinstance(valeur, int):
                setattr(self, nom, valeur)

    def ramener(self):
        editeur = self.editeur
        for nom, valeur in self.__dict__.iteritems():
            if nom == 'editeur':
                continue
            if isinstance(valeur, list):
                getattr(editeur, nom)[:] = valeur
            elif isinstance(valeur, int):
                setattr(editeur, nom, valeur)

    def __cmp__(self, other):
        return (cmp(self.ligne, other.ligne)
                or cmp(self.poids_visuel(), other.poids_visuel())
                or cmp(self.strategies, other.strategies))

    def poids_visuel(self):
        # Le poids visuel d'un ensemble de lignes est d'autant plus élevé que
        # les lignes ont leur masse noire de largeur inégale.  La somme des
        # carrés des largeurs se minimise lorsque les lignes sont équilibrées
        # entre elles.  Toutefois, pour favoriser quand même les alignements
        # colonne, cette somme ne compte que les lignes de continuations, la
        # première ligne ne contribue que de manière linéaire au poids visuel.
        lignes = ''.join(self.blocs).splitlines()
        poids = len(lignes[0].strip()) * 12
        for ligne in lignes[1:]:
            largeur = len(ligne.strip())
            poids += largeur * largeur
        return poids

## Broutilles stylistiques.

if vim is not None:
    vim.command('highlight Broutille term=reverse cterm=bold ctermbg=1'
                ' gui=bold guibg=Cyan')

def corriger_broutille(mode):
    # Corriger la broutille directement sous le curseur s'il s'en trouve,
    # puis passer à la broutille suivante.
    for broutille in MetaBroutille.registre:
        if broutille.confirmer_erreur(*curseur_courant()):
            broutille.corriger()
            broutille.repositionner()
            return
    trouver_broutille(mode)

def trouver_broutille(mode):
    # Trouver la prochaine broutille stylistique.
    # REVOIR: `\\' répété sur une série de lignes vides n'avance pas le curseur.
    tampon = vim.current.buffer
    rangee, colonne = curseur_courant()
    ligne = tampon[rangee]
    # Si rien n'a changé depuis la fois précédente, avancer le curseur.
    # Sinon, ré-analyser la ligne courante à partir du début.
    if (rangee == Broutille.rangee_precedente
          and colonne == Broutille.colonne_precedente
          and ligne[colonne:].startswith(Broutille.fragment_precedent)):
        colonne += 1
        if colonne == len(ligne):
            rangee += 1
            colonne = 0
            if rangee + 1 <= len(tampon):
                ligne = tampon[rangee]
    else:
        colonne = 0
    # Fouiller à partir du curseur pour trouver une broutille.
    while rangee < len(tampon):
        # Retenir l'appariement le plus à gauche, et parmi eux, le plus long.
        debut = None
        for broutille in MetaBroutille.registre:
            paire = broutille.trouver_erreur(rangee, colonne)
            if (paire is not None
                    and (debut is None
                         or paire[0] < debut
                         or paire[0] == debut and paire[1] > fin)):
                debut, fin = paire
                plainte = broutille.plainte
        if debut is not None:
            # Enluminer la broutille et repositionner le curseur.
            changer_curseur_courant(rangee, debut)
            fragment = ligne[debut:fin]
            if fragment:
                argument = (fragment.replace('\\', '\\\\')
                            .replace('/', '\\/').replace('[', '\\[')
                            .replace('*', '\\*'))
                vim.command('match Broutille /%s/' % argument)
            else:
                vim.command('match')
            sys.stderr.write(plainte)
            Broutille.rangee_precedente = rangee
            Broutille.colonne_precedente = debut
            Broutille.fragment_precedent = fragment
            return
        # Aller au début de la ligne suivante.
        rangee += 1
        colonne = 0
        if rangee < len(tampon):
            ligne = tampon[rangee]
    sys.stderr.write("Le reste du fichier me semble beau...\n")

class MetaBroutille(type):
    # Tenir un registre d'une instance par classe de broutille stylistique.
    # Pré-compiler le gabarit de la classe, s'il s'en trouve.
    registre = []

    def __init__(self, nom, bases, dict):
        type.__init__(self, nom, bases, dict)
        if nom != 'Broutille':
            MetaBroutille.registre.append(self())
        if hasattr(self, 'gabarit'):
            import re
            self.gabarit = re.compile(self.gabarit)

class Broutille:
    __metaclass__ = MetaBroutille
    # PLAINTE contient une courte explication pour l'utilisateur.
    plainte = "Broutille syntaxique."
    # Si SYNTEXTE est None, le gabarit fourni peut s'apparier dans les chaìnes
    # de caractères ou les commentaires.  Autrement, SYNTEXTE est un nombre,
    # souvent 0, qui est un déplacement par rapport au début du texte apparié
    # (ou de sa fin s'il est négatif).  Le caractère à ce déplacement ne doit
    # alors faire partie ni d'une chaîne de caractères, ni d'un commentaire.
    syntexte = None
    # Après une correction automatique fiable, c'est-à-dire, qui ne change
    # pas la sémantique du code Python, REPOSITIONNEMENT peut être mis à True
    # dans l'instance de la broutille, pour indiquer que le curseur doit se
    # repositionner sur la broutille suivante.  Autrement, ou encore, s'il n'y
    # a pas de correction automatique, une intervention humaine est requise.
    repositionnement = False
    # Les trois variables suivantes sont `globales' à toutes les broutilles,
    # elles servent à détecter que rien n'a changé depuis que la dernière
    # broutille a été trouvée, et donc que l'utilisateur a choisi de l'ignorer.
    # Dans ce cas, il faut s'acheminer inconditionnellement à la broutille
    # suivante.  Si une correction a eu lieu, la ligne est réanalysée à partir
    # du début, au cas où la correction engendre elle-même une autre broutille.
    rangee_precedente = None
    colonne_precedente = None
    fragment_precedent = ''

    def trouver_erreur(self, rangee, colonne):
        tampon = vim.current.buffer
        ligne = tampon[rangee]
        if hasattr(self, 'gabarit'):
            match = self.gabarit.search(ligne, colonne)
            while match:
                if self.confirmer_erreur(rangee, match.start()):
                    return match.start(), match.end()
                match = self.gabarit.search(ligne, match.start() + 1)
        else:
            while True:
                if self.confirmer_erreur(rangee, colonne):
                    return colonne, len(ligne)
                if colonne == len(ligne):
                    break
                colonne += 1

    def confirmer_erreur(self, rangee, colonne):
        assert hasattr(self, 'gabarit'), self
        tampon = vim.current.buffer
        match = self.gabarit.match(tampon[rangee], colonne)
        if match is None:
            return
        syntexte = self.syntexte
        if syntexte is None:
            self.match = match
            return match
        if syntexte < 0:
            syntexte += match.end() - match.start()
        if (vim.eval('synIDattr(synID(%d, %d, 0), "name")'
                     % (rangee + 1, colonne + 1 + syntexte))
              in ('pythonComment', 'pythonRawString', 'pythonString')):
            return
        self.match = match
        return match

    def corriger(self):
        # Par défaut, le programmeur choisit et édite une correction.
        sys.stderr.write("Ici, il me faut l'aide d'un humain!\n")
        self.annuler_precedent()

    def repositionner(self):
        if self.repositionnement:
            trouver_broutille('n')

    def remplacer_texte(self, nouveau):
        assert hasattr(self, 'gabarit'), self
        tampon = vim.current.buffer
        rangee = curseur_courant()[0]
        ligne = tampon[rangee]
        tampon[rangee] = (ligne[:self.match.start()]
                          + self.match.expand(nouveau)
                          + ligne[self.match.end():])
        self.annuler_precedent()

    def annuler_precedent(self):
        Broutille.rangee_precedente = None
        Broutille.colonne_precedente = None
        Broutille.fragment_precedent = ''

class Fichier_Vide(Broutille):
    # Un module Python ne doit pas être vide.
    plainte = "Module vide."

    def trouver_erreur(self, rangee, colonne):
        if self.confirmer_erreur(rangee, colonne):
            return 0, 0

    def confirmer_erreur(self, rangee, colonne):
        tampon = vim.current.buffer
        return len(tampon) == 0 or len(tampon) == 1 and not tampon[0]

    def corriger(self):
        # Insérer un squelette de programme Python.
        vim.current.buffer[:] = [
            '#!/usr/bin/env python',
            '# -*- coding: utf-8 -*-',
            '# Copyright © 2009 Progiciels Bourbeau-Pinard inc.',
            '# François Pinard <pinard@iro.umontreal.ca>, 2009.',
            '',
            '"""\\',
            '',
            '"""',
            '',
            '__metaclass__ = type',
            'import sys',
            '',
            'class Main:',
            '',
            '    def main(self, *arguments):',
            '        import getopt',
            '        options, arguments = getopt.getopt(arguments, \'\')',
            '        for option, valeur in options:',
            '            pass',
            '',
            'run = Main()',
            'main = run.main',
            '',
            'if __name__ == \'__main__\':',
            '    main(*sys.argv[1:])',
            ]
        self.annuler_precedent()

    def repositionner(self):
        # Déclencher une insertion à l'intérieur du doc-string.
        changer_curseur_courant(6, 0)
        vim.command('startinsert')

class Double_LigneVide(Broutille):
    # Il n'est pas utile d'avoir plusieurs lignes vides d'affilée.
    plainte = _("Multiple blank lines in a row.")

    def trouver_erreur(self, rangee, colonne):
        if self.confirmer_erreur(rangee, colonne):
            return 0, 0

    def confirmer_erreur(self, rangee, colonne):
        tampon = vim.current.buffer
        if len(tampon[rangee]) == 0:
            return rangee + 1 < len(tampon) and len(tampon[rangee+1]) == 0

    def corriger(self):
        # Éliminer les lignes superflues.
        disposer_en_retrait_remplir(curseur_courant()[0])
        self.repositionnement = True

class Tab(Broutille):
    # Il ne doit pas avoir de HT dans un fichier.
    plainte = _("TAB within source.")
    gabarit = r'\t\t*'

    def corriger(self):
        # Dans la marge gauche, remplacer chaque HT par huit blancs.
        # Plus loin dans la ligne, utiliser plutôt l'écriture `\t'.
        if self.match.start() == 0:
            self.remplacer_texte(' ' * 8 * len(self.match.group()))
            self.repositionnement = True
        else:
            self.remplacer_texte(r'\t' * len(self.match.group()))

class Blancs(Broutille):
    # Les jetons ne doivent pas être séparés par plus d'un blanc.
    plainte = _("Multiple spaces in a row.")
    gabarit = '([^ ])   *([^ #])'
    syntexte = 1

    def corriger(self):
        # Éliminer les blancs superflus.
        avant, apres = self.match.group(1, 2)
        if avant in '([{' or apres in ',;.:)]}':
            self.remplacer_texte(avant + apres)
        else:
            self.remplacer_texte(avant + ' ' + apres)
        self.repositionnement = True

class Blanc_FinLigne(Broutille):
    # Une ligne ne peut avoir de blancs suffixes.
    plainte = _("Trailing spaces.")
    gabarit = r'[ \t][ \t]*$'

    def corriger(self):
        # Éliminer les blancs suffixes.
        self.remplacer_texte('')
        self.repositionnement = True

class Backslash_FinLigne(Broutille):
    # Le backslash en fin-de-ligne doit être tout simplement évité, à
    # l'exception du cas où il suit immédiatement un triple-guillemets.
    plainte = _("Escaped newline.")
    gabarit = r' *\\$'

    def confirmer_erreur(self, rangee, colonne):
        if Broutille.confirmer_erreur(self, rangee, colonne):
            tampon = vim.current.buffer
            ligne = tampon[rangee]
            return ((colonne == 0 or ligne[colonne-1] != ' ')
                    and not ligne.endswith('"""\\'))

    def corriger(self):
        self.remplacer_texte('')

class Par_Blanc(Broutille):
    # Une parenthèse ouvrante ne doit pas être suivie d'un blanc.  Même chose
    # pour les crochets ou accolades ouvrants.
    plainte = _("Space after opening bracket, brace or parenthesis.")
    gabarit = r'([(\[{])  *'

    def corriger(self):
        # Enlever les blancs qui suivent.
        self.remplacer_texte(r'\1')
        self.repositionnement = True

class Blanc_These(Broutille):
    # Une parenthèse fermante ne doit pas être précédée d'un blanc.
    # Même chose pour les crochets ou accolades ouvrants.
    plainte = _("Space before closing bracket, brace or parenthesis.")
    gabarit = r'([^ ])  *([)\]}])'

    def corriger(self):
        # Enlever les blancs qui précèdent.
        self.remplacer_texte(r'\1\2')
        self.repositionnement = True

class Virgule_Noir(Broutille):
    # Une virgule doit être suivie d'un blanc.  Même chose pour les
    # point-virgules.
    plainte = _("Punctuation not followed by space.")
    gabarit = '([,;])([^ )])'
    syntexte = 0

    def corriger(self):
        # Ajouter un blanc.
        self.remplacer_texte(r'\1 \2')
        self.repositionnement = True

class Blanc_Virgule(Broutille):
    # Une virgule ne doit pas être précédée d'un blanc.  Même chose pour
    # les deux-points et point-virgules.
    plainte = _("Punctuation preceded by space.")
    gabarit = '(  *)([,:;])'

    def confirmer_erreur(self, rangee, colonne):
        if Broutille.confirmer_erreur(self, rangee, colonne):
            tampon = vim.current.buffer
            return colonne == 0 or tampon[rangee][colonne-1] != ' '

    def corriger(self):
        # Déplacer la virgule avant les blancs.
        self.remplacer_texte(r'\2\1')
        self.repositionnement = True

class Noir_Egal(Broutille):
    # `=' ou `==' doivent généralement être précédés d'un blanc.  Par contre,
    # pour les définitions de paramètres avec mot-clé, il n'y a aucun blanc
    # de part et d'autre du `='.
    plainte = _("Assignment or comparison symbol not preceded by space.")
    gabarit = '([^-+*/ <=>!&|])=  *'
    syntexte = 0

    def corriger(self):
        # Insérer le blanc manquant.
        self.remplacer_texte(r'\1 = ')
        self.repositionnement = True

class Egal_Noir(Broutille):
    # `=' ou `==' doivent généralement être suivis d'un blanc.  Par contre,
    # pour les définitions de paramètres avec mot-clé, il n'y a aucun blanc
    # de part et d'autre du `='.
    plainte = _("Assignment or comparison symbol not followed by space.")
    gabarit = '  *=([^ =])'
    syntexte = 0

    def confirmer_erreur(self, rangee, colonne):
        if Broutille.confirmer_erreur(self, rangee, colonne):
            tampon = vim.current.buffer
            return colonne == 0 or tampon[rangee][colonne-1] != ' '

    def corriger(self):
        # Insérer le blanc manquant.
        self.remplacer_texte(r' = \1')
        self.repositionnement = True

class Enonce_Commentaire(Broutille):
    # Un commentaire doit être seule sur sa ligne, il ne peut terminer une
    # ligne logique qui contient déjà autre chose.
    plainte = _("In-line comment.")
    gabarit = '[^ ] *#'
    syntexte = -1

    def corriger(self):
        # Séparer le commentaire pour le mettre seul sur une ligne séparée.
        # Le commentaire précéde normalement la ligne, à moins que la ligne
        # Python se termine par deux-points, dans lequel cas le commentaire
        # suit la ligne.  Une majuscule sera forcée au début du commentaire,
        # et un terminateur de phrase sera ajouté au besoin.
        tampon = vim.current.buffer
        rangee = curseur_courant()[0]
        ligne = tampon[rangee]
        code_python = ligne[:self.match.start()+1]
        commentaire = ligne[self.match.end()+1:]
        if commentaire.startswith(' '):
            commentaire = commentaire[1:]
        if commentaire:
            if commentaire[0].islower():
                commentaire = commentaire[0].upper() + commentaire[1:]
            if commentaire[-1] not in '.!?':
                commentaire += '.'
            if code_python.endswith(':'):
                tampon[rangee:rangee+1] = [
                    code_python,
                    '%*s# %s' % (marge_gauche(tampon[rangee+1]), '',
                                 commentaire)]
            else:
                tampon[rangee:rangee+1] = [
                    '%*s# %s' % (marge_gauche(code_python), '', commentaire),
                    code_python]
        else:
            tampon[rangee] = code_python
        self.annuler_precedent()

class Operateur_FinLigne:
    # Un opérateur ne peut se trouver en fin de ligne.
    plainte = _("Operator at end of line.")
    gabarit = r'(\band|\bor|[-+*/%<=>!])$'
    syntexte = 0

    def corriger(self):
        # Rapporter l'opérateur au début de la ligne suivante.
        tampon = vim.current.buffer
        rangee = curseur_courant()[0]
        ligne = tampon[rangee]
        operateur = self.match.group().lstrip()
        tampon[rangee] = ligne[:self.match.start()].rstrip()
        ligne = tampon[rangee+1]
        marge = marge_gauche(ligne)
        tampon[rangee+1] = '%s%s %s' % (ligne[:marge], operateur, ligne[marge:])
        self.annuler_precedent()

class Guillemets_SansMot(Broutille):
    # Une apostrophe devrait être utilisé plutôt qu'un guillemet pour
    # délimiter une chaîne qui ne contient que des caractères spéciaux ou
    # des lettres isolées.
    plaine = _("Double-quotes with no words (consider single-quotes).")
    gabarit = r'"(\\.|[^"])*"'

    def confirmer_erreur(self, rangee, colonne):
        if Broutille.confirmer_erreur(self, rangee, colonne):
            tampon = vim.current.buffer
            texte = eval(self.match.group(), {}, {})
            if not texte:
                return True
            if (vim.eval("synIDattr(synID(%d, %d, 0), \"name\")"
                         % (rangee + 1, colonne + 1))
                  not in ('pythonRawString', 'pythonString')):
                return False
            return not re.search('[A-Za-z][A-Za-z]', texte)

    def corriger(self):
        texte = eval(self.match.group(), {}, {})
        self.remplacer_texte(chaine_python(texte, '\''))
        self.repositionnement = True

class Triple_Guillemets(Broutille):
    # Un triple-guillemets qui débute une chaîne doit débuter une ligne ou
    # suivre une virgule ou une parenthèse ouvrante, et n'être suivi que
    # d'un backslash.  S'il termine une chaîne, il doit être seul sur sa
    # ligne, ou n'être suivi que d'une virgule ou d'une parenthèse fermante.
    plainte = _("Questionnable formatting of triple quotes.")
    gabarit = '"""'

    def confirmer_erreur(self, rangee, colonne):
        if Broutille.confirmer_erreur(self, rangee, colonne):
            tampon = vim.current.buffer
            ligne = tampon[rangee]
            suffixe = ligne[colonne+3:]
            if suffixe == '\\':
                if colonne > 0 and ligne[colonne-1] == '(':
                    return False
                if colonne > 1 and ligne[colonne-2:colonne] == ', ':
                    return False
                if not ligne[:colonne].lstrip():
                    return False
                return True
            if suffixe in ('', ',', ')'):
                return colonne > 0
            return True

class GrandeLigne(Broutille):
    # Les lignes doivent tenir dans Editeur.LIMITE colonnes.
    plainte = _("Line exceeds %d characters.")

    def trouver_erreur(self, rangee, colonne):
        tampon = vim.current.buffer
        if colonne <= Editeur.limite and len(tampon[rangee]) > Editeur.limite:
            self.plainte = GrandeLigne.plainte % Editeur.limite
            return Editeur.limite, len(tampon[rangee])

    def confirmer_erreur(self, rangee, colonne):
        tampon = vim.current.buffer
        return (colonne == Editeur.limite
                and len(tampon[rangee]) > Editeur.limite)

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        disposer_en_retrait_remplir(curseur_courant()[0])

class Apply(Broutille):
    # `apply(FONCTION, ARGUMENTS)' s'écrit mieux `FONCTION(*ARGUMENTS)'.
    plainte = (_("Use of `apply' function -- `function(*arguments)' is"
                 " preferred."))
    gabarit = r'\bapply\('

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        Editeur.recriture_sans.append('apply')
        disposer_en_retrait_remplir(curseur_courant()[0])
        Editeur.recriture_sans.pop()

class Close(Broutille):
    # `OBJET.close()' est rarement nécessaire si OBJET est un fichier.
    plainte = _("Use of `close' method (possibly unnecessary).")
    gabarit = r'\.close\(\)'

class Eval(Broutille):
    # `eval()' doit être évité autant que possible.
    plainte = _("Use of `eval' function (rethink the algorithm).")
    gabarit = r'\beval\('

class Exec(Broutille):
    # `exec' doit être évité autant que possible.
    plainte = _("Use of `exec' statement (rethink the algorithm).")
    gabarit = r'\bexec\b'

class Execfile(Broutille):
    # `execfile()' doit être évité autant que possible.
    plainte = _("Use of `execfile' function (rethink the algorithm).")
    gabarit = r'\bexecfile\('

class Find(Broutille):
    # `CHAÎNE.find(SOUS_CHAÎNE)' s'écrit mieux `SOUS_CHAÎNE in CHAÎNE'.
    plainte = _("Use of `find' method (consider using `in' instead).")
    gabarit = r'\.find\('

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        Editeur.recriture_sans.append('find')
        disposer_en_retrait_remplir(curseur_courant()[0])
        Editeur.recriture_sans.pop()

class Global(Broutille):
    # `global' doit être évité autant que possible.
    plainte = (_("Use of `global' statement (consider using class variables"
                 " instead)."))
    gabarit = r'\bglobal\b'

class Has_Key(Broutille):
    # `OBJET.has_key(CLÉ)' s'écrit mieux `CLÉ in OBJET'.
    plainte = _("Use of `has_key' method (consider using `in' instead).")
    gabarit = r'\.has_key\('

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        Editeur.recriture_sans.append('has_key')
        disposer_en_retrait_remplir(curseur_courant()[0])
        Editeur.recriture_sans.pop()

class Input(Broutille):
    # `input()' doit être évité autant que possible.
    plainte = _("Use of `input' function (rethink the algorithm).")
    gabarit = r'\binput\('

class Import_Etoile(Broutille):
    # L'énoncé `import *' devrait généralement être évité.
    plainte = _("Use of `import *' (be explicit about what to import instead).")
    gabarit = r'\bimport \*'

class Items(Broutille):
    # `OBJET.items()' s'écrit souvent mieux `OBJET.iteritems()'.
    plainte = _("Use of `items' method (consider using `iteritems' instead).")
    gabarit = r'\.items\(\)'

    def corriger(self):
        # Utiliser `iteritems'.
        self.remplacer_texte('.iteritems()')

class Iterkeys(Broutille):
    # `OBJET.iterkeys()' s'écrit mieux `OBJET', utilisé comme itérateur.
    plainte = _("Use of `iterkeys' method (possibly unnecessary).")
    gabarit = r'\.iterkeys\(\)'

    def corriger(self):
        # Éliminer l'appel de `iterkeys'.
        self.remplacer_texte('')

class Keys(Broutille):
    # `OBJET.keys()' s'écrit mieux `OBJET', utilisé comme itérateur.
    plainte = _("Use of `keys' method (possibly unnecessary).")
    gabarit = r'\.keys\(\)'

    def corriger(self):
        # Éliminer l'appel de `keys'.
        self.remplacer_texte('')

class Open(Broutille):
    # `open(NOM_FICHIER)' s'écrit mieux `file(NOM_FICHIER)'.
    plainte = _("Use of `open' method (consider using `file' instead).")
    gabarit = r'\bopen\('

    def corriger(self):
        # Utiliser `file'.
        self.remplacer_texte('file(')

class Print(Broutille):
    # L'énoncé `print' devrait être réservé pour la mise-au-point.
    plainte = _("Use of `print' statement (is it meant for debugging?).")
    gabarit = r'\bprint\b'
    syntexte = 0

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        Editeur.recriture_sans.append('print')
        disposer_en_retrait_remplir(curseur_courant()[0])
        Editeur.recriture_sans.pop()

class Readlines(Broutille):
    # `OBJET.readlines()' s'écrit mieux `OBJET', utilisé comme itérateur.
    plainte = _("Use of `readlines' method (possibly unnecessary).")
    gabarit = r'\.readlines\(\)'

    def corriger(self):
        # Éliminer l'appel de `readlines'.
        self.remplacer_texte('')

class String(Broutille):
    # Le module `string' doit être considéré comme à peu près désuet.
    plainte = (_("Use of `string' module (consider using string methods"
                 " instead)."))
    gabarit = r'\bstring\.|\bimport.*\bstring\b'
    syntexte = 0

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        Editeur.recriture_sans.append('string')
        disposer_en_retrait_remplir(curseur_courant()[0])
        Editeur.recriture_sans.pop()

class Type(Broutille):
    # `OBJECT is type(CONSTANTE)' se récrit `isinstance(OBJET, TYPE)'.
    plainte = _("Use of `type' function (consider using `isinstance' instead).")
    gabarit = r'(\bis |==) *type\('

class Values(Broutille):
    # `OBJET.values()' s'écrit souvent mieux `OBJET.itervalues()'.
    plainte = _("Use of `values' method (consider using `itervalues' instead).")
    gabarit = r'\.values\(\)'

    def corriger(self):
        # Utiliser `itervalues'.
        self.remplacer_texte('.itervalues()')

class Xreadlines(Broutille):
    # `OBJET.xreadlines()' s'écrit mieux `OBJET', utilisé comme itérateur.
    plainte = _("Use of `xreadlines' method (possibly unnecessary).")
    gabarit = r'\.xreadlines\(\)'

    def corriger(self):
        # Éliminer l'appel de `xreadlines'.
        self.remplacer_texte('')

## Quelques autres actions simples.

def choisir_mise_au_point(mode):
    Editeur.mise_au_point = not Editeur.mise_au_point
    if Editeur.mise_au_point:
        sys.stdout.write(_("Tracing enabled, quite verbose."))
    else:
        sys.stdout.write(_("Tracing disabled."))

def choisir_remplisseur(mode):
    def valeur_suivante(valeur, choix):
        return choix[(list(choix).index(valeur) + 1) % len(choix)]
    Disposeur.remplisseur = valeur_suivante(Disposeur.remplisseur,
                                            Disposeur.choix_remplisseurs)
    sys.stdout.write("Les commentaires seront remplis par `%s'."
                     % Disposeur.remplisseur)

def ajouter_parentheses(mode):
    rangee, colonne = curseur_courant()
    tampon = vim.current.buffer
    ligne = tampon[rangee]
    if ligne.endswith(':'):
        tampon[rangee] = ligne[:colonne] + '(' + ligne[colonne:-1] + '):'
    else:
        tampon[rangee] = ligne[:colonne] + '(' + ligne[colonne:] + ')'
    changer_curseur_courant(rangee, colonne + 1)

def eliminer_parentheses(mode):
    rangee1, colonne1 = curseur_courant()
    vim.command('normal %')
    rangee2, colonne2 = curseur_courant()
    vim.command('normal %')
    if (rangee1, colonne1) > (rangee2, colonne2):
        rangee1, rangee2 = rangee2, rangee1
        colonne1, colonne2 = colonne2, colonne1
    tampon = vim.current.buffer
    for rangee, colonne in (rangee2, colonne2), (rangee1, colonne1):
        ligne = tampon[rangee]
        tampon[rangee] = ligne[:colonne] + ligne[colonne+1:]
    changer_curseur_courant(rangee1, colonne1)

def forcer_apostrophes(mode):
    changer_chaine('"', '\'')

def forcer_guillemets(mode):
    changer_chaine('\'', '"')

def changer_chaine(avant, apres):
    # AVANT et APRES sont des chaînes de un caractère: le délimiteur.
    rangee, colonne = curseur_courant()
    tampon = vim.current.buffer
    ligne = tampon[rangee]
    match = (re.compile(r'r?%s(\\.|[^%s])*%s' % (avant, avant, avant))
             .search)(ligne, colonne)
    if match:
        texte = chaine_python(eval(match.group(), {}, {}), apres)
        tampon[rangee] = ligne[:match.start()] + texte + ligne[match.end():]
        changer_curseur_courant(rangee, match.start() + len(texte))

## Routines de service.

# Doit-on compter les rangées et colonnes à partir de 0 ou de 1?  Dans la ligne
# de mode sous la fenêtre, Vim affiche rangée et colonne tous deux comptés
# à partir de 1.  Dans `vim.current.window.cursor', la rangée est comptée
# à partir de 1 et la colonne à partir de 0.  Dans `vim.current.buffer',
# les rangées sont indicées à partir de 0, comme il se doit en Python.
# Dans ce programme, rangées et colonnes sont indicées à partir de 0.

def curseur_courant():
    row, column = vim.current.window.cursor
    return row - 1, column

def changer_curseur_courant(rangee, colonne):
    vim.current.window.cursor = rangee + 1, colonne

def est_none(noeud):
    # Retourner True si le noeud représente la constante None.
    return isinstance(noeud, compiler.ast.Const) and noeud.value is None

def chaine_python(texte, delimiteur):
    # Retourner la représentation de TEXTE sous la forme d'une chaîne Python
    # delimitée par DELIMITEUR, qui est soit une apostrophe, soit un guillemet.
    # L'attribut "raw" est déterminé automatiquement.
    if meilleure_en_raw(texte, delimiteur):
        return 'r' + delimiteur + texte + delimiteur
    fragments = []
    write = fragments.append
    substitutions = {delimiteur: '\\' + delimiteur, '\\': r'\\', '\a': r'\a',
                     '\b': r'\b', '\f': r'\f', '\n': r'\n', '\t': r'\t',
                     '\v': r'\v'}
    write(delimiteur)
    for caractere in texte:
        if caractere in substitutions:
            write(substitutions[caractere])
        elif not est_imprimable(caractere):
            write(repr(caractere)[1:-1])
        else:
            write(caractere)
    write(delimiteur)
    return ''.join(fragments)

def meilleure_en_raw(texte, delimiteur):
    # Retourner True si la chaîne se présente mieux en format "raw".
    if '\\' not in texte:
        return False
    if (len(texte) - len(texte.rstrip('\\'))) % 2 != 0:
        return False
    for caractere in texte:
        if caractere == delimiteur or not est_imprimable(caractere):
            return False
    return True

try:
    import unicodedata
except ImportError:

    def est_imprimable(caractere):
        valeur = ord(caractere)
        # Retourner vrai si le caractère ISO 8859-1 est imprimable.
        return not (0 <= valeur < 32 or 127 <= valeur < 160)
else:

    def est_imprimable(caractere):
        # Retourner vrai si le caractère est imprimable selon Unicode.
        return unicodedata.category(unichr(ord(caractere))) != 'Cc'

def marge_gauche(texte):
    # Retourner le nombre de blancs consécutifs préfixant le texte.
    return len(texte) - len(texte.lstrip())

if vim is not None:
    installer_vim()
    for commande in ("""\
augroup Pynits
  autocmd!
  autocmd FileType python python pynits.installer_vim()
  autocmd BufWrite * python pynits.ajuster_codage()
augroup END
""").splitlines():
        vim.command(commande.lstrip())

if __name__ == '__main__':
    run = Main()
    run.main(*sys.argv[1:])
