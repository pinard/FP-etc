#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2004 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2004.

"""\
Détails supplémentaires pour le support de Python.
"""

__metaclass__ = type
import re, sys, vim

def installer_vim():
    leader = '\\'
    if int(vim.eval('exists("maplocalleader")')):
        leader = vim.eval('maplocalleader')
    # REVOIR: Je ne réussis pas à utiliser ni `,s' ni `,t': bizarre!
    # REVOIR: Délai inexpliqué pour les commandes `,c' et `,m'.
    register_keys('pynits',
                  ((leader, 'n', 'trouver_broutille'),
                   ('"', 'n', 'forcer_guillemets'),
                   ('\'', 'n', 'forcer_apostrophes'),
                   ('(', 'n', 'ajouter_parentheses'),
                   (')', 'n', 'eliminer_parentheses'),
                   ('.', 'n', 'corriger_broutille'),
                   ('c', 'n', 'disposer_en_colonne'),
                   ('l', 'n', 'disposer_en_ligne'),
                   ('m', 'n', 'disposer_en_mixte'),
                   ('od', 'n', 'choisir_mise_au_point'),
                   ('om', 'n', 'montrer_syntaxe'),
                   ('or', 'n', 'choisir_remplisseur'),
                   ('q', 'n', 'disposer_en_mixte_remplie'),
                   ('r', 'n', 'disposer_en_colonne_remplie')))
    Disposeur.indentation = int(vim.eval('&shiftwidth'))

def register_keys(plugin, triplets):
    import os
    local = True
    map = 'map <buffer>'
    variable = ('mapleader', 'maplocalleader')[local]
    if int(vim.eval('exists("%s")' % variable)):
        normal_leader = vim.eval(variable)
    else:
        normal_leader = '\\'
    insert_leader = ord('\x02')
    for key, modes, name in triplets:
        for mode in modes:
            python_command = ':python %s.%s(\'%s\')' % (plugin, name, mode)
            sid_name = '<SID>%s_%s' % (mode, name)
            plug_name = '<Plug>%s_%s_%s' % (plugin.capitalize(), mode, name)
            mapped = int(vim.eval('hasmapto(\'%s\')' % plug_name))
            if mode == 'i':
                if not mapped:
                    vim.command('%s%s <unique> %s%s %s'
                                % (mode, map, insert_leader, key, plug_name))
                vim.command('%snore%s <silent> %s <C-O>%s<CR>'
                            % (mode, map, sid_name, python_command))
            else:
                if not mapped:
                    vim.command('%s%s <unique> %s%s %s'
                                % (mode, map, normal_leader, key, plug_name))
                vim.command('%snore%s <silent> %s %s<CR>'
                            % (mode, map, sid_name, python_command))
            vim.command('%snore%s <unique> <script> %s %s'
                         % (mode, map, plug_name, sid_name))

# Doit-on compter les rangées et colonnes à partir de 0 ou de 1?  Dans la
# ligne de mode sous la fenêtre, Vim affiche rangée et colonne tous deux
# comptés à partir de 1.  Dans `vim.current.cursor', la rangée est comptée
# à partir de 1 et la colonne à partir de 0.  Dans `vim.current.buffer',
# les rangées sont indicées à partir de 0, comme il se doit en Python.
# Ce programme se colle à la convention de `vim.current.cursor'; il faut
# donc systématiquement soustraire 1 à la rangée pour manipuler le tampon.

## Quelques actions simples.

PIED_DE_MOUCHE = '¶'

def choisir_mise_au_point(mode):
    Editeur.mise_au_point = valeur_suivante(Editeur.mise_au_point,
        range(len(Editeur.explications_mise_au_point)))
    sys.stdout.write(Editeur.explications_mise_au_point[Editeur.mise_au_point])

def choisir_remplisseur(mode):
    Disposeur.remplisseur = valeur_suivante(Disposeur.remplisseur,
                                             Disposeur.choix_remplisseurs)
    sys.stdout.write("Les commentaires seront remplis par `%s'."
                     % Disposeur.remplisseur)

def valeur_suivante(valeur, choix):
    return choix[(list(choix).index(valeur) + 1) % len(choix)]

def ajouter_parentheses(mode):
    rangee, colonne = vim.current.window.cursor
    tampon = vim.current.buffer
    ligne = tampon[rangee-1]
    if ligne.endswith(':'):
        tampon[rangee-1] = ligne[:colonne] + '(' + ligne[colonne:-1] + '):'
    else:
        tampon[rangee-1] = ligne[:colonne] + '(' + ligne[colonne:] + ')'
    vim.current.window.cursor = rangee, colonne + 1

def eliminer_parentheses(mode):
    rangee1, colonne1 = vim.current.window.cursor
    vim.command('normal %')
    rangee2, colonne2 = vim.current.window.cursor
    vim.command('normal %')
    if (rangee1, colonne1) > (rangee2, colonne2):
        rangee1, rangee2 = rangee2, rangee1
        colonne1, colonne2 = colonne2, colonne1
    tampon = vim.current.buffer
    for rangee, colonne in (rangee2, colonne2), (rangee1, colonne1):
        ligne = tampon[rangee-1]
        tampon[rangee-1] = ligne[:colonne] + ligne[colonne+1:]
    vim.current.window.cursor = rangee1, colonne1

def forcer_apostrophes(mode):
    rangee, colonne = vim.current.window.cursor
    tampon = vim.current.buffer
    ligne = tampon[rangee-1]
    ouvrant = ligne[colonne:].find('"')
    if ouvrant >= 0:
        ouvrant += colonne
        fermant = ligne[ouvrant+1:].find('"')
        if fermant >= 0:
            fermant += ouvrant + 1
            tampon[rangee-1] = (ligne[:ouvrant] + '\''
                                + ligne[ouvrant+1:fermant].replace('\'', r'\'')
                                + '\'' + ligne[fermant+1:])
            vim.current.window.cursor = rangee, ouvrant + 1

def forcer_guillemets(mode):
    rangee, colonne = vim.current.window.cursor
    tampon = vim.current.buffer
    ligne = tampon[rangee-1]
    ouvrant = ligne[colonne:].find('\'')
    if ouvrant >= 0:
        ouvrant += colonne
        fermant = ligne[ouvrant+1:].find('\'')
        if fermant >= 0:
            fermant += ouvrant + 1
            tampon[rangee-1] = (ligne[:ouvrant] + '"'
                                + ligne[ouvrant+1:fermant].replace('"', r'\"')
                                + '"' + ligne[fermant+1:])
            vim.current.window.cursor = rangee, ouvrant + 1

## Broutilles stylistiques.

vim.command('highlight Broutille'
            ' term=reverse cterm=bold ctermbg=1'
            ' gui=bold guibg=Cyan')

def corriger_broutille(mode):
    # Corriger la broutille directement sous le curseur s'il s'en trouve,
    # puis passer à la broutille suivante.
    for broutille in MetaBroutille.registre:
        if broutille.confirmer_erreur(vim.current.window.cursor):
            broutille.corriger()
            broutille.repositionner()
            return
    trouver_broutille(mode)

def trouver_broutille(mode):
    # Trouver la prochaine broutille stylistique.
    # REVOIR: `,,' répété sur une série de lignes vides n'avance pas le curseur.
    tampon = vim.current.buffer
    rangee, colonne = vim.current.window.cursor
    ligne = tampon[rangee-1]
    # Si rien n'a changé depuis la fois précédente, avancer le curseur.
    # Sinon, ré-analyser la ligne courante à partir du début.
    if (rangee == Broutille.rangee_precedente
            and colonne == Broutille.colonne_precedente
            and ligne[colonne:].startswith(Broutille.fragment_precedent)):
        colonne += 1
        if colonne == len(ligne):
            rangee += 1
            colonne = 0
            if rangee <= len(tampon):
                ligne = tampon[rangee-1]
    else:
        colonne = 0
    # Fouiller à partir du curseur pour trouver une broutille.
    while rangee <= len(tampon):
        # Retenir l'appariement le plus à gauche, et parmi eux, le plus long.
        debut = None
        for broutille in MetaBroutille.registre:
            paire = broutille.trouver_erreur((rangee, colonne))
            if (paire is not None
                    and (debut is None
                         or paire[0] < debut
                         or paire[0] == debut and paire[1] > fin)):
                debut, fin = paire
                plainte = broutille.plainte
        if debut is not None:
            # Enluminer la broutille et repositionner le curseur.
            vim.current.window.cursor = rangee, debut
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
        if rangee <= len(tampon):
            ligne = tampon[rangee-1]
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
    # Après une correction automatique, le curseur se repositionne normalement
    # sur la broutille suivante, c'est l'action par défaut.  Mais si une
    # broutille ne fournit pas sa propre méthode CORRIGER, la méthode CORRIGER
    # par défaut intervient pour indiquer qu'une intervention humaine est
    # requise et change REPOSITIONNEMENT à True, dans l'instance seulement.
    repositionnement = True
    # Les trois variables suivantes sont `globales' à toutes les broutilles,
    # elles servent à détecter que rien n'a changé depuis que la dernière
    # broutille a été trouvée, et donc que l'utilisateur a choisi de l'ignorer.
    # Dans ce cas, il faut s'acheminer inconditionnellement à la broutille
    # suivante.  Si une correction a eu lieu, la ligne est réanalysée à partir
    # du début, au cas où la correction engendre elle-même une autre broutille.
    rangee_precedente = None
    colonne_precedente = None
    fragment_precedent = ''

    def trouver_erreur(self, curseur):
        tampon = vim.current.buffer
        rangee, colonne = curseur
        ligne = tampon[rangee-1]
        if hasattr(self, 'gabarit'):
            match = self.gabarit.search(ligne, colonne)
            while match:
                if self.confirmer_erreur((rangee, match.start())):
                    return match.start(), match.end()
                match = self.gabarit.search(ligne, match.start()+1)
        else:
            while True:
                if self.confirmer_erreur((rangee, colonne)):
                    return colonne, len(ligne)
                if colonne == len(ligne):
                    break
                colonne += 1

    def confirmer_erreur(self, curseur):
        assert hasattr(self, 'gabarit'), self
        tampon = vim.current.buffer
        rangee, colonne = curseur
        match = self.gabarit.match(tampon[rangee-1], colonne)
        if match is None:
            return
        syntexte = self.syntexte
        if syntexte is None:
            self.match = match
            return match
        if syntexte < 0:
            syntexte += match.end() - match.start()
        if (vim.eval('synIDattr(synID(%d, %d, 0), "name")'
                     % (rangee, colonne + 1 + syntexte))
              in ('pythonComment', 'pythonRawString', 'pythonString')):
            return
        self.match = match
        return match

    def corriger(self):
        # Par défaut, le programmeur choisit et édite une correction.
        sys.stderr.write("Ici, il me faut l'aide d'un humain!\n")
        self.repositionnement = False
        self.annuler_precedent()

    def repositionner(self):
        if self.repositionnement:
            trouver_broutille('n')

    def remplacer_texte(self, nouveau):
        assert hasattr(self, 'gabarit'), self
        tampon = vim.current.buffer
        rangee = vim.current.window.cursor[0]
        ligne = tampon[rangee-1]
        tampon[rangee-1] = (ligne[:self.match.start()]
            + self.match.expand(nouveau) + ligne[self.match.end():])
        self.annuler_precedent()

    def annuler_precedent(self):
        Broutille.rangee_precedente = None
        Broutille.colonne_precedente = None
        Broutille.fragment_precedent = ''

class Fichier_Vide(Broutille):
    # Un module Python ne doit pas être vide.
    plainte = "Module vide."

    def trouver_erreur(self, curseur):
        if self.confirmer_erreur(curseur):
            return 0, 0

    def confirmer_erreur(self, curseur):
        tampon = vim.current.buffer
        return len(tampon) == 0 or len(tampon) == 1 and not tampon[0]

    def corriger(self):
        # Insérer un squelette de programme Python.
        vim.current.buffer[:] = [
            '#!/usr/bin/env python',
            '# -*- coding: Latin-1',
            '# Copyright © 2004 Progiciels Bourbeau-Pinard inc.',
            '# François Pinard <pinard@iro.umontreal.ca>, 2004.',
            '',
            '"""\\',
            '',
            '"""',
            '',
            '__metaclass__ = type',
            '',
            'class Main:',
            '    def __init__(self):',
            '        pass',
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
            '    import sys',
            '    main(*sys.argv[1:])',
            ]
        self.annuler_precedent()

    def repositionner(self):
        # Déclencher une insertion à l'intérieur du doc-string.
        vim.current.window.cursor = 7, 0
        vim.command('startinsert')

class Double_LigneVide(Broutille):
    # Il n'est pas utile d'avoir plusieurs lignes vides d'affilée.
    plainte = "Plusieurs lignes vides d'affilée."

    def trouver_erreur(self, curseur):
        if self.confirmer_erreur(curseur):
            return 0, 0

    def confirmer_erreur(self, curseur):
        tampon = vim.current.buffer
        rangee, colonne = curseur
        if len(tampon[rangee-1]) == 0:
            return rangee < len(tampon) and len(tampon[rangee]) == 0

    def corriger(self):
        # Éliminer les lignes superflues.
        disposer_en_mixte_remplie(vim.current.window.cursor[0])

class Tab(Broutille):
    # Il ne doit pas avoir de HT dans un fichier.
    plainte = "Tabulation dans le source."
    gabarit = r'\t\t*'

    def corriger(self):
        # Dans la marge gauche, remplacer chaque HT par huit blancs.
        # Plus loin dans la ligne, utiliser plutôt l'écriture `\t'.
        if self.match.start() == 0:
            self.remplacer_texte(' ' * 8 * len(self.match.group()))
        else:
            self.remplacer_texte(r'\t' * len(self.match.group()))

class Blancs(Broutille):
    # Les jetons ne doivent pas être séparés par plus d'un blanc.
    plainte = "Plusieurs blancs d'affilée."
    gabarit = '([^ ])   *([^ #])'
    syntexte = 1

    def corriger(self):
        # Éliminer les blancs superflus.
        avant, apres = self.match.group(1, 2)
        if avant in '([{' or apres in ',;.:)]}':
            self.remplacer_texte(avant + apres)
        else:
            self.remplacer_texte(avant + ' ' + apres)

class Blanc_FinLigne(Broutille):
    # Une ligne ne peut avoir de blancs suffixes.
    plainte = "Blancs suffixes."
    gabarit = r'[ \t][ \t]*$'

    def corriger(self):
        # Éliminer les blancs suffixes.
        self.remplacer_texte('')

class GrandeLigne(Broutille):
    # Les lignes doivent tenir dans 80 colonnes.
    plainte = "Ligne trop longue."

    def trouver_erreur(self, curseur):
        tampon = vim.current.buffer
        rangee, colonne = curseur
        if colonne <= Editeur.limite and len(tampon[rangee-1]) > Editeur.limite:
            return Editeur.limite, len(tampon[rangee-1])

    def confirmer_erreur(self, curseur):
        tampon = vim.current.buffer
        rangee, colonne = curseur
        return (colonne == Editeur.limite
                and len(tampon[rangee-1]) > Editeur.limite)

    def corriger(self):
        # Redisposer l'entièreté du code Python.
        disposer_en_mixte_remplie(vim.current.window.cursor[0])

class Triple_Guillemets(Broutille):
    # Un triple-guillemets qui débute une chaîne doit débuter une ligne ou
    # suivre une virgule ou une parenthèse ouvrante, et n'être suivi que d'un
    # backslash.  S'il termine une chaîne, il doit être seul sur sa ligne, ou
    # n'être suivi que d'une virgule ou d'une parenthèse fermante.
    plainte = "Triple guillemets mal disposé."
    gabarit = r'"""'

    def confirmer_erreur(self, curseur):
        if Broutille.confirmer_erreur(self, curseur):
            tampon = vim.current.buffer
            rangee, colonne = curseur
            ligne = tampon[rangee-1]
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

class Enonce_Commentaire(Broutille):
    # Un commentaire doit être seule sur sa ligne, il ne peut terminer une
    # ligne logique qui contient déjà autre chose.
    plainte = "Commentaire `en ligne'."
    gabarit = '[^ ] *#'
    syntexte = -1

    def corriger(self):
        # Séparer le commentaire pour le mettre seul sur une ligne séparée.
        # Le commentaire précéde normalement la ligne, à moins que la ligne
        # Python se termine par deux-points, dans lequel cas le commentaire
        # suit la ligne.  Une majuscule sera forcée au début du commentaire,
        # et un terminateur de phrase sera ajouté au besoin.
        tampon = vim.current.buffer
        rangee = vim.current.window.cursor[0]
        ligne = tampon[rangee-1]
        code_python = ligne[:self.match.start() + 1]
        commentaire = ligne[self.match.end() + 1:]
        if commentaire.startswith(' '):
            commentaire = commentaire[1:]
        if commentaire:
            if commentaire[0].islower():
                commentaire = commentaire[0].upper() + commentaire[1:]
            if commentaire[-1] not in '.!?':
                commentaire += '.'
            if code_python.endswith(':'):
                tampon[rangee-1:rangee] = [
                    code_python,
                    '%*s# %s' % (marge_gauche(tampon[rangee]), '', commentaire)]
            else:
                tampon[rangee-1:rangee] = [
                    '%*s# %s' % (marge_gauche(code_python), '', commentaire),
                    code_python]
        else:
            tampon[rangee-1] = code_python
        self.annuler_precedent()

class Par_Blanc(Broutille):
    # Une parenthèse ouvrante ne doit pas être suivie d'un blanc.
    # Même chose pour les crochets ou accolades ouvrants.
    plainte = "Blanc après symbole ouvrant."
    gabarit = r'([(\[{])  *'

    def corriger(self):
        # Enlever les blancs qui suivent.
        self.remplacer_texte(r'\1')

class Blanc_These(Broutille):
    # Une parenthèse fermante ne doit pas être précédée d'un blanc.
    # Même chose pour les crochets ou accolades ouvrants.
    plainte = "Blanc avant symbole fermant."
    gabarit = r'([^ ])  *([)\]}])'

    def corriger(self):
        # Enlever les blancs qui précèdent.
        self.remplacer_texte(r'\1\2')

class Virgule_Noir(Broutille):
    # Une virgule doit être suivie d'un blanc.
    # Même chose pour les point-virgules.
    plainte = "Ponctuation non-suivie d'un blanc."
    gabarit = r'([,;])([^ )])'
    syntexte = 0

    def corriger(self):
        # Ajouter un blanc.
        self.remplacer_texte(r'\1 \2')

class Blanc_Virgule(Broutille):
    # Une virgule ne doit pas être précédée d'un blanc.
    # Même chose pour les deux-points et point-virgules.
    plainte = "Ponctuation précédée d'un blanc."
    gabarit = r'(  *)([,:;])'

    def confirmer_erreur(self, curseur):
        if Broutille.confirmer_erreur(self, curseur):
            tampon = vim.current.buffer
            rangee, colonne = curseur
            return colonne == 0 or tampon[rangee-1][colonne-1] != ' '

    def corriger(self):
        # Déplacer la virgule avant les blancs.
        self.remplacer_texte(r'\2\1')

class Noir_Egal(Broutille):
    # `=' ou `==' doivent généralement être précédés d'un blanc.
    # Par contre, pour les définitions de paramètres avec mot-clé, il n'y
    # a aucun blanc de part et d'autre du `='.
    plainte = "Symbole d'affectation ou de comparaison non précédé d'un blanc."
    gabarit = r'([^-+*/ <=>!&|])=  *'
    syntexte = 0

    def corriger(self):
        # Insérer le blanc manquant.
        self.remplacer_texte(r'\1 = ')

class Egal_Noir(Broutille):
    # `=' ou `==' doivent généralement être suivis d'un blanc.
    # Par contre, pour les définitions de paramètres avec mot-clé, il n'y
    # a aucun blanc de part et d'autre du `='.
    plainte = "Symbole d'affectation ou de comparaison non suivi d'un blanc."
    gabarit = r'  *=([^ =])'
    syntexte = 0

    def confirmer_erreur(self, curseur):
        if Broutille.confirmer_erreur(self, curseur):
            tampon = vim.current.buffer
            rangee, colonne = curseur
            return colonne == 0 or tampon[rangee-1][colonne-1] != ' '

    def corriger(self):
        # Insérer le blanc manquant.
        self.remplacer_texte(r' = \1')

class Backslash_FinLigne(Broutille):
    # Le backslash en fin-de-ligne doit être tout simplement évité, à
    # l'exception du cas où il suit immédiatement un triple-guillemets.
    plainte = "Fin de ligne échappée."
    gabarit = r' *\\$'

    def confirmer_erreur(self, curseur):
        if Broutille.confirmer_erreur(self, curseur):
            tampon = vim.current.buffer
            rangee, colonne = curseur
            ligne = tampon[rangee-1]
            return ((colonne == 0 or ligne[colonne-1] != ' ')
                    and not ligne.endswith('"""\\'))

    def corriger(self):
        self.remplacer_texte('')

class Operateur_FinLigne:
    # Un opérateur ne peut se trouver en fin de ligne.
    plainte = "Opérateur en fin de ligne."
    gabarit = r'(\band|\bor|[-+*/%<=>!])$'
    syntexte = 0

    def corriger(self):
        # Rapporter l'opérateur au début de la ligne suivante.
        tampon = vim.current.buffer
        rangee = vim.current.window.cursor[0]
        ligne = tampon[rangee-1]
        operateur = self.match.group().lstrip()
        tampon[rangee-1] = ligne[:self.match.start()].rstrip()
        ligne = tampon[rangee]
        marge = marge_gauche(ligne)
        tampon[rangee] = '%s%s %s' % (ligne[:marge], operateur, ligne[marge:])
        self.annuler_precedent()

class Import_Etoile(Broutille):
    # L'énoncé `import *' devrait généralement être évité.
    plainte = "Usage de l'énoncé `import *' (énumérer ce qu'il faut importer)."
    gabarit = r'\bimport \*'

class Print(Broutille):
    # L'énoncé `print' devrait être réservé pour la mise-au-point.
    plainte = "Usage de l'énoncé `print' (peut-être pour mise-au-point)."
    gabarit = r'\bprint\b'
    syntexte = 0

class Apply(Broutille):
    # `apply(FONCTION, ARGUMENTS)' s'écrit mieux `FONCTION(*ARGUMENTS)'.
    plainte = "Usage de la fonction `apply' (utiliser `fonction(*arguments)')."
    gabarit = r'\bapply\('

class Close(Broutille):
    # `OBJET.close()' est rarement nécessaire si OBJET est un fichier.
    plainte = "Usage de la méthode `close' (peut-être inutile)."
    gabarit = r'\.close\('

class Eval(Broutille):
    # `eval()' doit être évité autant que possible.
    plainte = "Usage de la fonction `eval' (repenser l'algorithme)."
    gabarit = r'\beval\('

class Exec(Broutille):
    # `exec' doit être évité autant que possible.
    plainte = "Usage de l'énoncé `exec' (repenser l'algorithme)."
    gabarit = r'\bexec\b'

class Execfile(Broutille):
    # `execfile()' doit être évité autant que possible.
    plainte = "Usage de la fonction `execfile' (repenser l'algorithme)."
    gabarit = r'\bexecfile\('

class Find(Broutille):
    # `CHAÎNE.find(SOUS_CHAÎNE)' s'écrit mieux `SOUS_CHAÎNE in CHAÎNE'.
    plainte = "Usage de la méthode `find' (peut-être utiliser `in')."
    gabarit = r'\.find\('

class Global(Broutille):
    # `global' doit être évité autant que possible.
    plainte = "Usage de l'énoncé `global' (utiliser des variables de classe)."
    gabarit = r'\bglobal\b'

class Has_Key(Broutille):
    # `OBJET.has_key(CLÉ)' s'écrit mieux `CLÉ in OBJET'.
    plainte = "Usage de la méthode `has_key' (peut-être utiliser `in')."
    gabarit = r'\.has_key\('

class Input(Broutille):
    # `input()' doit être évité autant que possible.
    plainte = "Usage de la fonction `input' (repenser l'algorithme)."
    gabarit = r'\binput\('

class Keys(Broutille):
    # `OBJET.keys()' s'écrit mieux `OBJET', utilisé comme itérateur.
    plainte = "Usage de la méthode `keys' (peut-être inutile)."
    gabarit = r'\.keys\(\)'

    def corriger(self):
        # Éliminer l'appel de `keys'.
        self.remplacer_texte('')

class Open(Broutille):
    # `open(NOM_FICHIER)' s'écrit mieux `file(NOM_FICHIER)'.
    plainte = "Usage de la méthode `open' (peut-être utiliser `file')."
    gabarit = r'\bopen\('

    def corriger(self):
        # Utiliser `file'.
        self.remplacer_texte('file(')

class Readlines(Broutille):
    # `OBJET.readlines()' s'écrit mieux `OBJET', utilisé comme itérateur.
    plainte = "Usage de la méthode `readlines' (peut-être inutile)."
    gabarit = r'\.readlines\(\)'

    def corriger(self):
        # Éliminer l'appel de `readlines'.
        self.remplacer_texte('')

class String(Broutille):
    # Le module `string' doit être considéré comme à peu près désuet.
    plainte = "Usage de la méthode `string' (peut-être méthodes chaînes)."
    gabarit = r'\bstring\.|\bimport.*\bstring\b'
    syntexte = 0

class Type(Broutille):
    # `OBJECT is type(CONSTANTE)' se récrit `isinstance(OBJET, TYPE)'.
    plainte = "Usage de la fonction `type' (peut-être utiliser `isinstance')."
    gabarit = r'(\bis |==) *type\('

class Dates_Richard(Broutille):
    # Richard Nault a sa méthode bien personnelle pour écrire les dates.
    plainte = "Date à la Richard Nault (utiliser la notation ISO-8601)."
    mois = {
        # Écriture américaine.
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
        # Ajouts pour le français.
        'Fév': 2, 'Avr': 4, 'Mai': 5, 'Aoû': 8, 'Déc': 12,
        # Écriture française majuscule.
        'JAN': 1, 'FÉB': 2, 'MAR': 3, 'AVR': 4, 'MAI': 5, 'JUN': 6,
        'JUL': 7, 'AOÛ': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DÉC': 12,
        # Écriture française minuscule.
        'jan': 1, 'féb': 2, 'mar': 3, 'avr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'aoû': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'déc': 12,
        # Erreurs orthographiques observées.
        'AOU': 8, 'aou': 8,
        }
    gabarit = r'([0-3][0-9])\.(%s)\.(200[0-4])' % '|'.join(mois)

    def corriger(self):
        self.remplacer_texte(r'\3-%02d-\1' % self.mois[self.match.group(2)])

## Redisposition contrôlé par la syntaxe.

import compiler, compiler.ast, compiler.consts, compiler.visitor

# Noeuds syntaxiques bidon représentant quelques codes Python accessoires.
class Elif(compiler.ast.If): pass
class Else(compiler.ast.Pass): pass
class Except(compiler.ast.Tuple): pass
class Finally(compiler.ast.Pass): pass
class Try(compiler.ast.Pass): pass

class Disposeur:

    # Accroissement de la marge par niveau d'intentation.
    indentation = 4

    # Limite en lignes d'exploration vers l'arrière pour trouver le début d'une
    # ligne logique de code Python.
    limite_arriere = 12

    # Limite en lignes de l'exploration vers l'avant pour trouver la fin d'une
    # ligne logique de code Python.
    limite_avant = 25

    # Outil à utiliser pour remplir les commentaires.
    choix_remplisseurs = 'fmt', 'par', 'vim', 'python'
    remplisseur = 'fmt'

    def montrer_syntaxe(self, mode):
        # Imprimer la syntaxe d'une ligne (pour aider la mise-au-point).
        rangee = vim.current.window.cursor[0]
        try:
            debut, fin, marge, commentaires, arbre = self.trouver_ligne_python(
                rangee)
        except SyntaxError, diagnostic:
            sys.stderr.write(str(diagnostic))
        else:
            sys.stdout.write(str(arbre))

    def disposer_en_ligne(self, mode):
        self.traiter_ligne(Editeur.LIGNE, None)

    def disposer_en_colonne(self, mode):
        self.traiter_ligne(Editeur.COLONNE, False)

    def disposer_en_colonne_remplie(self, mode):
        self.traiter_ligne(Editeur.COLONNE, True)

    def disposer_en_mixte(self, mode):
        self.traiter_ligne(Editeur.MIXTE, False)

    def disposer_en_mixte_remplie(self, mode):
        self.traiter_ligne(Editeur.MIXTE, True)

    def traiter_ligne(self, strategie, remplir):
        # Redisposer la ligne selon STRATEGIE et possiblement REMPLIR.
        rangee = vim.current.window.cursor[0]
        tampon = vim.current.buffer
        ligne = tampon[rangee - 1].lstrip()
        if ligne.startswith('#'):
            fin = self.traiter_commentaire(rangee)
        elif ligne:
            fin = self.traiter_code_python(rangee, strategie, remplir)
        else:
            fin = self.traiter_blanche(rangee)
        # Placer le curseur sur la ligne suivante.
        if fin <= len(tampon):
            colonne = marge_gauche(tampon[fin-1])
        else:
            fin = len(tampon)
            colonne = 0
        vim.current.window.cursor = fin, colonne

    def traiter_blanche(self, rangee):
        debut = fin = rangee
        tampon = vim.current.buffer
        if '\f' in tampon[rangee-1]:
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
        prefixe = ' ' * marge_gauche(tampon[rangee-1]) + '#'
        while debut > 1 and tampon[debut-2].startswith(prefixe):
            debut -= 1
        while fin < len(tampon) and tampon[fin].startswith(prefixe):
            fin += 1
        if self.remplisseur == 'vim':
            vim.command('normal %dGgq%dG' % (debut, fin))
            return vim.current.window.cursor[0] + 1
        if self.remplisseur == 'fmt':
            import os, tempfile
            nom = tempfile.mktemp()
            file(nom, 'w').writelines([tampon[rangee - 1] + '\n'
                                       for rangee in range(debut, fin + 1)])
            insertion = (os.popen('fmt -u -w%d -p\'%s\' <%s'
                                  % (Editeur.limite, prefixe+' ', nom))
                         .read)()
            os.remove(nom)
        elif self.remplisseur == 'par':
            import os, tempfile
            nom = tempfile.mktemp()
            file(nom, 'w').writelines([tampon[rangee-1] + '\n'
                                       for rangee in range(debut, fin + 1)])
            # REVOIR: Examiner PARINIT et voir s'il faut l'intégrer.
            insertion = os.popen('par w%d <%s' % (Editeur.limite, nom)).read()
            os.remove(nom)
        elif self.remplisseur == 'python':
            import textwrap
            lignes = [tampon[rangee-1][len(prefixe):]
                      for rangee in range(debut, fin + 1)]
            insertion = textwrap.fill(textwrap.dedent('\n'.join(lignes)),
                                      width=Editeur.limite,
                                      fix_sentence_endings=True,
                                      initial_indent=prefixe + ' ',
                                      subsequent_indent=prefixe + ' ')
        return self.modifier_tampon(debut, fin + 1, insertion)

    def traiter_code_python(self, rangee, strategie, remplir):
        try:
            debut, fin, marge, commentaires, arbre = self.trouver_ligne_python(
                rangee)
        except SyntaxError, diagnostic:
            sys.stderr.write(str(diagnostic))
            return rangee
        editeur = Editeur(marge, strategie, remplir)
        try:
            compiler.walk(arbre, editeur,
                          walker=compiler.visitor.ExampleASTVisitor(),
                          verbose=True)
        except Editeur.Impasse, diagnostic:
            sys.stderr.write('%s...  (%s)'
                             % (str(diagnostic), editeur.statistiques()))
            return rangee
        else:
            sys.stdout.write('OK!  (%s)' % editeur.statistiques())
        resultat = str(editeur)
        if resultat.endswith(':\n'):
            resultat += self.recommenter(marge + self.indentation, commentaires)
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
                        "Erreur de syntaxe, peut-être recul insuffisant.")
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
                if debut <= 1 or debut <= rangee - self.limite_arriere:
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
        ligne = tampon[rangee-1].rstrip()
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
                        raise SyntaxError("`%s' intempestif." % ligne[0])
                    attendu = pile.pop()
                    if ligne[0] != attendu:
                        raise SyntaxError("`%s' vu, `%s' attendu!"
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
                    if rangee > len(tampon):
                        break
                    rangee += 1
                    ligne = tampon[rangee-1].lstrip()
                    lignes.append(ligne)
                    continue
                match = re.match(r'u?r?(\'\'\'|""")', ligne)
                if match:
                    quelque_chose = True
                    terminateur = match.group(1)
                    ligne = ligne[match.end():]
                    while terminateur not in ligne:
                        if rangee > len(tampon):
                            ligne = None
                            break
                        rangee += 1
                        ligne = tampon[rangee-1].rstrip()
                        lignes.append(ligne)
                    else:
                        position = ligne.find(terminateur)
                        ligne = ligne[position+3:].lstrip()
                    continue
                match = re.match(r'u?r?'
                                 r'(\'([^\\\']+|\\.)*\'|"([^\\"]+|\\.)*")',
                                 ligne)
                if match:
                    quelque_chose = True
                    ligne = ligne[match.end():].lstrip()
                    continue
                ligne = ligne[1:].lstrip()
                quelque_chose = True
            if not pile and quelque_chose:
                break
            if len(lignes) == self.limite_avant or rangee >= len(tampon):
                if pile:
                    raise SyntaxError("`%s' attendu!"
                                      % '\', `'.join(pile[::-1]))
                raise SyntaxError("Pas de code Python!")
            rangee += 1
            ligne = tampon[rangee-1].strip()
        return (debut + len(lignes), marge, commentaires,
                '\n'.join(lignes) + '\n')

    def recommenter(self, marge, commentaires):
        if commentaires:
            while len(commentaires) > 1 and not commentaires[-1]:
                commentaires.pop()
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
        if fin-debut != len(lignes) or tampon[debut-1:fin-1] != lignes:
            tampon[debut-1:fin-1] = lignes
        return debut + len(lignes)

disposeur = Disposeur()
montrer_syntaxe = disposeur.montrer_syntaxe
disposer_en_ligne = disposeur.disposer_en_ligne
disposer_en_colonne = disposeur.disposer_en_colonne
disposer_en_colonne_remplie = disposeur.disposer_en_colonne_remplie
disposer_en_mixte = disposeur.disposer_en_mixte
disposer_en_mixte_remplie = disposeur.disposer_en_mixte_remplie

## Outil d'édition d'un arbre syntaxique.

NON_ASSOC, ASSOC_GAUCHE, ASSOC_DROITE = range(3)

def preparer_editeur():
    # Cette fonction modifie les classes structurales de `compiler.ast' pour
    # leur ajouter les notions de priorité, d'associativité et possiblement
    # aussi, la chaîne représentant l'opérateur.  Ces informations sont
    # bien utiles, par exemple pour choisir quand et comment insérer des
    # parenthèses lors de la reconstruction de la surface d'un énoncé Python.
    for donnees in (
            (0, NON_ASSOC, 'AssTuple', 'Tuple'),
            (1, NON_ASSOC ,'Lambda'),
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
# par la variable RUSTINE_ESPACES.
PRIORITE_RUSTINE = 6
# La priorité des phénomènes tels que l'appel de fonction, l'indicage et
# le choix d'attributs.  Ces phénomènes sont associatifs à gauche entre eux,
# et les parenthèses sont supprimées directement dans la fonction EDITER.
PRIORITE_APPEL = 14
## Une priorité qui, étant plus grand que toutes les autres, a pour effet de
## forcer la production de parenthèses sur tout texte inclus.
#PRIORITE_FORCE = 16

class Editeur(list):

    # Trois niveaux de mise-au-point sont définis.
    explications_mise_au_point = ("Trace inactive.",
                                  "Stratégies par région de texte.",
                                  "Trace des choix entre solutions.",
                                  "Trace détaillée, très verbeuse.")
    mise_au_point = 0

    # Énumération des diverses stratégies de disposition.  Garder cet ordre.
    LIGNE, COLONNE, MIXTE = range(3)
    noms_strategies = 'Ligne', 'Colonne', 'Mixte'

    # Les lignes doivent idéalement tenir dans 80 colonnes par défaut.
    limite = 80
    # La stratégie initiale, qui limite les stratégies de disposition.
    strategie = MIXTE

    # Lorsqu'une tentative de disposition aboutit dans un cul-de-sac logique.
    class Impasse(Exception): pass

    def __init__(self, marge, strategie, remplir):
        list.__init__(self)
        # MARGE donne le nombre de blancs en début de toute nouvelle ligne.
        self.marge = marge
        # REMPLIR à True indique que l'on doit remplir les lignes produites
        # tantque la marge ne change pas, False ou None sinon.  La valeur
        # None indique en plus qu'il n'y a pas de nombre maximum de colonnes.
        self.remplir = remplir
        # Niveau de récursion dans les appels à EDITER.
        self.niveau = 0
        # STRATEGIE indique la stratégie maximale à essayer.  Les stratégies
        # d'ordinal plus petit seront toujours essayées d'abord.
        self.strategie = strategie
        # PRIORITE est la priorité du texte couramment engendré.
        self.priorite = PRIORITE_ENONCE
        # ENONCE_DEL indique qu'il s'agit d'un énoncé `del' et que le
        # mot-clé `del' est déjà écrit.
        self.enonce_del = False
        # RUSTINE_MARGE peut établir un minimum supplémentaire pour la marge.
        # Voir la documentation de la fonction EDITER pour plus de détails.
        self.rustine_marge = None
        # RUSTINE_PARENTHESES commande l'économie possible de parenthèses.
        # Voir la documentation de la fonction EDITER pour plus de détails.
        self.rustine_parentheses = False
        # RUSTINE_ESPACES contrôle l'économie possible de certaines espaces.
        # Voir la documentation de la fonction EDITER pour plus de détails.
        self.rustine_espaces = 2
        # LIGNE donne le nombre de lignes complétées ou débutées.
        self.ligne = 0
        # COLONNE donne le nombre de colonnes dans la dernière ligne.
        self.colonne = 0
        # Nombre de choix qu'il a fallu faire.  Un choix survient lorsque
        # TENTER_ESSAIS voit plus d'une possibilité à explorer.
        self.compteur_choix = 0
        # Nombre de stratégies effectivement essayées.  Une stratégie n'est pas
        # comptée lorsqu'elle est la seule possibilité dans TENTER_ESSAIS.
        self.compteur_essais = 0
        # Nombre d'impasses rencontrées durant les essais.
        self.compteur_impasses = 0

    def __str__(self):
        return ('\n'.join([ligne.rstrip(' ')
                           for ligne in ''.join(self).splitlines()])
                + '\n')

    def statistiques(self):
        fragments = []
        write = fragments.append
        write(self.noms_strategies[self.strategie])
        if self.remplir:
            write(" remplie")
        write(': ')
        if self.compteur_essais:
            if self.compteur_essais > 1:
                write("%d essais" % self.compteur_essais)
            else:
                write("un essai")
        else:
            write("aucun essai")
        if self.compteur_choix:
            if self.compteur_choix > 1:
                write(", %d choix" % self.compteur_choix)
            else:
                write(", un choix")
        if self.compteur_impasses:
            if self.compteur_impasses > 1:
                write(", %d impasses" % self.compteur_impasses)
            else:
                write(", une impasse")
        return ''.join(fragments)

    def debug(self, indice, texte=None):
        if Editeur.mise_au_point > 2:
            if texte is None:
                texte = ''
            else:
                texte = ': ' + str(texte)
            sys.stdout.write('%2d%s %s %s %d %d| %d:%d [%s %s %s]%s\n'
                % (self.niveau, '  ' * self.niveau, indice,
                   Editeur.noms_strategies[self.strategie], self.priorite,
                   self.marge, self.ligne, self.colonne, self.rustine_marge,
                   self.rustine_parentheses, self.rustine_espaces, texte))

    def debug_texte(self, indice):
        if Editeur.mise_au_point > 2:
            self.debug('Texte ' + indice)
            sys.stdout.write(''.join(self) + PIED_DE_MOUCHE + '\n')

    ## Énoncés.

    def visitAssert(self, noeud):
        format = 'assert %=%^'
        arguments = [PRIORITE_TUPLE, noeud.test]
        if noeud.fail is not None:
            format += ', %^'
            arguments.append(noeud.fail)
        self.disposer(format, *arguments)

    def visitAssign(self, noeud):
        format = ''
        arguments = []
        for gauche in noeud.nodes:
            format += '%^ = '
            arguments.append(gauche)
        format += '%^'
        arguments.append(noeud.expr)
        self.disposer(format, *arguments)

    def visitAugAssign(self, noeud):
        self.disposer('%^ %s %^', noeud.node, noeud.op, noeud.expr)

    def visitBreak(self, noeud):
        self.disposer('break')

    def visitContinue(self, noeud):
        self.disposer('continue')

    def visitDiscard(self, noeud):
        self.disposer('%^', noeud.expr)

    def visitElif(self, noeud):
        format = 'elif '
        arguments = []
        assert len(noeud.tests) == 1, noeud.tests
        for test, enonce in noeud.tests:
            format += '%^%:'
            arguments.append(test)
        assert noeud.else_ is None, noeud.else_
        self.disposer(format, *arguments)

    def visitElse(self, noeud):
        self.disposer('else:')

    def visitExcept(self, noeud):
        if len(noeud.nodes) == 0:
            self.disposer('except:')
        elif len(noeud.nodes) == 1:
            self.disposer('except %^%:', noeud.nodes[0])
        else:
            self.disposer('except %^%:', compiler.ast.Tuple(noeud.nodes))

    def visitExec(self, noeud):
        format = 'exec %=%^'
        arguments = [PRIORITE_TUPLE, noeud.expr]
        if noeud.locals is not None or noeud.globals is not None:
            format += ' in %^'
            arguments += [None, noeud.locals]
        if noeud.globals is not None:
            format += ', %^'
            arguments += [None, noeud.globals]
        self.disposer(format, *arguments)

    def visitFinally(self, noeud):
        self.disposer('finally:')

    def visitFor(self, noeud):
        self.disposer('for %^ in %^%:', noeud.assign, noeud.list)
        self.disposer_pass(noeud, noeud.body)
        assert noeud.else_ is None, noeud.else_

    def visitFrom(self, noeud):
        format = 'from %s import'
        arguments = [noeud.modname]
        separateur = ' '
        for nom, as in noeud.names:
            format += separateur + '%s'
            arguments.append(nom)
            if as is not None:
                format += ' as %s'
                arguments.append(as)
            separateur = ', '
        self.disposer(format, *arguments)

    def visitGlobal(self, noeud):
        format = 'global'
        arguments = []
        separateur = ' '
        for nom in noeud.names:
            format += separateur + '%s'
            arguments.append(nom)
            separateur = ', '
        self.disposer(format, *arguments)

    def visitIf(self, noeud):
        format = 'if '
        arguments = []
        assert len(noeud.tests) == 1, noeud.tests
        for test, enonce in noeud.tests:
            format += '%^%:'
            arguments.append(test)
            self.disposer_pass(noeud, enonce)
        assert noeud.else_ is None, noeud.else_
        self.disposer(format, *arguments)

    def visitImport(self, noeud):
        format = 'import'
        arguments = []
        separateur = ' '
        for nom, as in noeud.names:
            format += separateur + '%s'
            arguments.append(nom)
            if as is not None:
                format += ' as %s'
                arguments.append(as)
            separateur = ', '
        self.disposer(format, *arguments)

    def visitPass(self, noeud):
        self.disposer('pass')

    def visitPrint(self, noeud):
        self.disposer_print(noeud, False)

    def visitPrintnl(self, noeud):
        self.disposer_print(noeud, True)

    def visitRaise(self, noeud):
        format = 'raise%='
        arguments = [PRIORITE_TUPLE]
        if noeud.expr1 is not None:
            format += ' %^'
            arguments.append(noeud.expr1)
        if noeud.expr2 is not None:
            format += ', %^'
            arguments.append(noeud.expr2)
        if noeud.expr3 is not None:
            format += ', %^'
            arguments.append(noeud.expr3)
        self.disposer(format, *arguments)

    def visitReturn(self, noeud):
        if est_none(noeud.value):
            format = 'return'
            arguments = []
        else:
            format = 'return %^'
            arguments = [noeud.value]
        self.disposer(format, *arguments)

    def visitTry(self, noeud):
        self.disposer('try:')

    def visitTryExcept(self, noeud):
        # body, handlers, else_
        assert False

    def visiTryFinally(self):
        assert False

    def visitWhile(self, noeud):
        self.disposer('while %^%:', noeud.test)
        self.disposer_pass(noeud, noeud.body)
        assert noeud.else_ is None, noeud.else_

    def visitYield(self, noeud):
        self.disposer('yield %^', noeud.value)

    ## Expressions.

    def operateur_unaire(self, noeud):
        operateur = noeud.operateur
        if operateur.isalpha():
            format = '%(%s %^%)'
        else:
            format = '%(%s%^%)'
        rustine_espaces = self.rustine_espaces
        self.rustine_espaces -= 1
        try:
            self.disposer(format, noeud.priorite, operateur, noeud.expr)
        finally:
            self.rustine_espaces = rustine_espaces

    def operateur_binaire(self, noeud):
        priorite = noeud.priorite
        if noeud.associativite == ASSOC_DROITE:
            format = '%(%^%_%|%s%_'
            arguments = [priorite, noeud.left, noeud.operateur]
            noeud = noeud.right
            while noeud == priorite:
                format += '%^%_%|%s%_'
                arguments += [noeud.left, noeud.operateur]
                noeud = noeud.right
            format += '%^%)'
            arguments.append(noeud)
        else:
            paires = []
            while noeud.priorite == priorite:
                paires.append((noeud.operateur, noeud.right))
                noeud = noeud.left
            paires.reverse()
            format = '%(%^'
            arguments = [priorite, noeud]
            for operateur, expression in paires:
                format += '%_%|%s%_%^'
                arguments += [operateur, expression]
            format += '%)'
        rustine_espaces = self.rustine_espaces
        self.rustine_espaces -= 1
        try:
            self.disposer(format, *arguments)
        finally:
            self.rustine_espaces = rustine_espaces

    def operateur_multiple(self, noeud):
        rustine_espaces = self.rustine_espaces
        self.rustine_espaces -= 1
        try:
            self.operateur_multiple_logique(noeud)
        finally:
            self.rustine_espaces = rustine_espaces

    def operateur_multiple_logique(self, noeud):
        format = '%(%^'
        arguments = [noeud.priorite, noeud.nodes[0]]
        for expression in noeud.nodes[1:]:
            if noeud.operateur.isalpha():
                format += ' %|%s %^'
            else:
                format += '%_%|%s%_%^'
            arguments += [noeud.operateur, expression]
        format += '%)'
        self.disposer(format, *arguments)

    visitAdd = operateur_binaire
    visitAnd = operateur_multiple_logique

    def visitBackquote(self, noeud):
        self.disposer('repr(%^)', noeud.expr)

    visitBitand = operateur_multiple
    visitBitor = operateur_multiple
    visitBitxor = operateur_multiple

    def visitCallFunc(self, noeud):
        compte = (len(noeud.args) + bool(noeud.star_args)
                  + bool(noeud.dstar_args))
        if compte == 0:
            self.disposer('%!%(%^()%)', noeud.priorite, noeud.node)
            return
        format = r'%!%(%^(%\%='
        arguments = [noeud.priorite, noeud.node, PRIORITE_TUPLE]
        if compte == 1:
            format += '%!'
        separateur = ''
        for expression in noeud.args:
            format += separateur + '%^'
            arguments.append(expression)
            separateur = ', %|'
        if noeud.star_args is not None:
            format += separateur + '*%^'
            arguments.append(noeud.star_args)
            separateur = ', %|'
        if noeud.dstar_args is not None:
            format += separateur + '**%^'
            arguments.append(noeud.dstar_args)
        format += ')%)%/'
        self.disposer(format, *arguments)

    def visitCompare(self, noeud):
        format = '%(%^'
        arguments = [noeud.priorite, noeud.expr]
        for operateur, comparand in noeud.ops:
            if operateur.isalpha():
                format += ' %|%s %^'
            else:
                format += '%_%|%s%_%^'
            arguments += [operateur, comparand]
        format += '%)'
        self.disposer(format, *arguments)

    def visitConst(self, noeud):
        if isinstance(noeud.value, str):
            self.disposer_chaine(noeud.value)
        elif isinstance(noeud.value, (int, float)):
            self.disposer_constante(noeud.value)
        else:
            assert False, (type(noeud.value), noeud.value)

    def visitDict(self, noeud):
        format = r'%!%({%\%='
        arguments = [noeud.priorite, PRIORITE_TUPLE]
        separateur = ''
        for cle, valeur in noeud.items:
            format += separateur + '%^: %^'
            arguments += [cle, valeur]
            separateur = ', %|'
        format += '}%)%/'
        self.disposer(format, *arguments)

    visitDiv = operateur_binaire
    visitFloorDiv = operateur_binaire

    def visitGetattr(self, noeud):
        attributs = [noeud.attrname]
        noeud = noeud.expr
        while isinstance(noeud, compiler.ast.Getattr):
            attributs.append(noeud.attrname)
            noeud = noeud.expr
        attributs.reverse()
        self.disposer('%(%^' + '%|.%s'*len(attributs) + '%)',
                       noeud.priorite, noeud, *attributs)

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
            arguments.append(ordinaire)
            separateur = ', %|'
        if noeud.defaults:
            for cle, valeur in zip(cles, noeud.defaults):
                format += separateur + '%s=%^'
                arguments += [cle, valeur]
                separateur = ', %|'
        if star_args is not None:
            format += separateur + '*%s'
            arguments.append(star_args)
            separateur = ', %|'
        if dstar_args is not None:
            format += separateur + '**%s'
            arguments.append(dstar_args)
        format += ': %^%)'
        arguments.append(noeud.code)
        self.disposer(format, *arguments)

    visitLeftShift = operateur_binaire

    def visitList(self, noeud):
        format = r'%!%([%\%='
        arguments = [PRIORITE_APPEL, PRIORITE_TUPLE]
        separateur = ''
        for expression in noeud.nodes:
            format += separateur + '%^'
            arguments.append(expression)
            separateur = ', %|'
        format += ']%)%/'
        self.disposer(format, *arguments)

    def visitListComp(self, noeud):
        format = r'%!%([%\%=%^'
        arguments = [PRIORITE_TUPLE, noeud.expr]
        for expression in noeud.quals:
            format += ' %|%^'
            arguments.append(expression)
        format += ']%)%/'
        self.disposer(format, *arguments)

    visitMod = operateur_binaire
    visitMul = operateur_binaire

    def visitName(self, noeud):
        self.disposer('%s', noeud.name)

    visitNot = operateur_unaire
    visitOr = operateur_multiple_logique
    visitPower = operateur_binaire
    visitRightShift = operateur_binaire

    def visitSlice(self, noeud):
        format = self.peut_etre_del(noeud) + r'%^%!%([%\%='
        arguments = [noeud.expr, noeud.priorite, PRIORITE_ENONCE]
        if noeud.lower is not None:
            format += '%|%^'
            arguments.append(noeud.lower)
        format += '%|:'
        if noeud.upper is not None:
            format += '%^'
            arguments.append(noeud.upper)
        format += ']%)%/'
        self.disposer(format, *arguments)

    visitSub = operateur_binaire

    def visitSubscript(self, noeud):
        assert len(noeud.subs) == 1, noeud.subs
        self.disposer(self.peut_etre_del(noeud) + r'%^%!%([%\%=%|%^]%)%/',
            noeud.expr, noeud.priorite, PRIORITE_ENONCE, noeud.subs[0])

    def visitTuple(self, noeud):
        if len(noeud.nodes) == 0:
            format = '()'
            arguments = []
        elif len(noeud.nodes) == 1:
            format = '%(%^,%)'
            arguments = [PRIORITE_TUPLE, noeud.nodes[0]]
        else:
            format = '%('
            arguments = [PRIORITE_TUPLE]
            separateur = ''
            for expression in noeud.nodes:
                format += separateur + '%^'
                arguments.append(expression)
                separateur = ', %|'
            format += '%)'
        self.disposer(format, *arguments)

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
        self.disposer(
            format + '%(%^' + '%|.%s'*len(attributs) + '%)',
            noeud.priorite, noeud, *attributs)

    def visitAssName(self, noeud):
        self.disposer(self.peut_etre_del(noeud) + '%s', noeud.name)

    visitAssList = visitList
    visitAssTuple = visitTuple

    def visitClass(self, noeud):
        format = 'class %s'
        arguments = [noeud.name]
        if noeud.bases:
            format += '('
            separateur = ''
            for base in noeud.bases:
                format += separateur + '%^'
                arguments.append(base)
                separateur = ', %|'
            format += ')'
        format += '%:'
        self.disposer(format, *arguments)
        assert noeud.doc is None, noeud.doc
        self.disposer_pass(noeud, noeud.code)

    def visitEllipsis(self, noeud):
        self.disposer('...')

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
        format = 'def %s(%='
        arguments = [noeud.name, PRIORITE_TUPLE]
        separateur = ''
        for ordinaire in ordinaires:
            format += separateur + '%s'
            arguments.append(ordinaire)
            separateur = ', %|'
        if noeud.defaults:
            for cle, valeur in zip(cles, noeud.defaults):
                format += separateur + '%s=%^'
                arguments += [cle, valeur]
                separateur = ', %|'
        if star_args is not None:
            format += separateur + '*%s'
            arguments.append(star_args)
            separateur = ', %|'
        if dstar_args is not None:
            format += separateur + '**%s'
            arguments.append(dstar_args)
        format += ')%:'
        self.disposer(format, *arguments)
        assert noeud.doc is None, noeud.doc
        self.disposer_pass(noeud, noeud.code)

    def visitKeyword(self, noeud):
        self.disposer('%s=%^', noeud.name, noeud.expr)

    def visitListCompFor(self, noeud):
        format = 'for %^ in %^'
        arguments = [noeud.assign, noeud.list]
        for expression in noeud.ifs:
            format += ' %^'
            arguments.append(expression)
        self.disposer(format, *arguments)

    def visitListCompIf(self, noeud):
        self.disposer('if %^', noeud.test)

    def visitModule(self, noeud):
        if noeud.doc is None:
            self.disposer('%^', noeud.node)
        else:
            assert isinstance(noeud.node, compiler.ast.Stmt)
            assert len(noeud.node.nodes) == 0, noeud.node
            self.disposer_chaine(noeud.doc, triple=True)

    def visitSliceobj(self, noeud):
        format = ''
        arguments = []
        separateur = '%|'
        for expression in noeud.nodes:
            format += separateur
            if not est_none(expression):
                format += '%^'
                arguments.append(expression)
            separateur = '%|:'
        self.disposer(format, *arguments)

    def visitStmt(self, noeud):
        assert len(noeud.nodes) == 1, noeud
        self.disposer('%^' * len(noeud.nodes), *noeud.nodes)

    ## Méthodes de service.

    def peut_etre_del(self, noeud):
        if self.enonce_del:
            assert noeud.flags == compiler.consts.OP_DELETE, (
                    noeud, noeud.flags)
            return ''
        if noeud.flags == compiler.consts.OP_DELETE:
            self.enonce_del = True
            return 'del '
        assert (noeud.flags in (compiler.consts.OP_APPLY,
                                compiler.consts.OP_ASSIGN)), (
                    noeud, noeud.flags)
        return ''

    def disposer_pass(self, noeud, enonce):
        assert isinstance(enonce, compiler.ast.Stmt), enonce
        assert len(enonce.nodes) == 1, enonce
        assert isinstance(enonce.nodes[0], compiler.ast.Pass), enonce
        if not hasattr(noeud, 'rustine'):

            def essai():
                self.editer(' pass')

            def essai_2():
                self.editer('%|    pass')

            self.tenter_triplet(essai, essai_2, essai_2)

    def disposer_print(self, noeud, nl):
        format = 'print%='
        arguments = [PRIORITE_TUPLE]
        separateur = ' '
        if noeud.dest is not None:
            format += separateur + '>>%^'
            arguments.append(noeud.dest)
            separateur = ', '
        for expression in noeud.nodes:
            format += separateur + '%^'
            arguments.append(expression)
            separateur = ', '
        if not nl:
            format += ','
        self.disposer(format, *arguments)

    # REVOIR: Peut-être transporter le type original? (raw, '', "", """)
    def disposer_chaine(self, texte, triple=False):
        # Formatter TEXTE au mieux.  Si TRIPLE, forcer un triple délimiteur.

        # DELIMITEUR reçoit le meilleur délimiteur pour représenter TEXTE,
        # c'est-à-dire un guillemet si la chaîne semble être écrite en langue
        # naturelle, ou un apostrophe autrement.
        delimiteur = '\''
        # RAW est vrai si la chaîne peut avoir le préfixe `r'.
        raw = '\\' in texte and (len(texte) - len(texte.rstrip('\\'))) % 2 == 0
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
                if raw and caractere != '\\' and not est_imprimable(caractere):
                    raw = False
        # Comment déterminer si une chaîne est un fragment en langue naturelle?
        # Je dois me contenter d'heuristiques simples.  Voici celle que
        # Richard Stallman m'a suggérée et que j'ai mise en application dans
        # `po-mode.el'.  Trois lettres d'affilée?  Alors oui.  Jamais deux
        # lettres d'affilée?  Alors non.  Sinon, alors oui si plus de lettres
        # que de non-lettres.  Mais ce code ne me satisfait pas vraiment,
        # je le laisse en commentaire ici!
        if False:
            if meilleure >= 3 or meilleure == 2 and 2*compteur > len(texte):
                delimiteur = '"'
        # Je préfère tenter l'heuristique suivante, qui considère qu'un
        # fragment est en langue naturelle si un blanc y apparaît, si l'on
        # y trouve un mot d'au moins quatre lettres, et s'il y a au moins
        # trois fois plus de lettres que de non-lettres.
        if ' ' in texte and meilleure >= 4 and 4*compteur > len(texte):
            delimiteur = '"'

        def essai_delimiteur_ligne():
            # Tenter une disposition tout d'un pain sur une ligne.
            write = self.write
            if raw:
                write('r' + delimiteur + texte + delimiteur)
            else:
                substitutions = {delimiteur: '\\'+delimiteur, '\\': r'\\',
                                 '\a': r'\a', '\b': r'\b', '\f': r'\f',
                                 '\n': r'\n', '\t': r'\t', '\v': r'\v'}
                write(delimiteur)
                for caractere in texte:
                    if caractere in substitutions:
                        write(substitutions[caractere])
                    elif not est_imprimable(caractere):
                        write(repr(caractere)[1:-1])
                    else:
                        write(caractere)
                write(delimiteur)

        def essai_delimiteur_simple():
            # Tenter une disposition avec des délimiteurs simples, quitte
            # à découper la chaîne en plusieurs morceaux à concaténer et à
            # disposer chacun sur une ligne.
            if raw:
                format_debut = 'r' + delimiteur
            else:
                format_debut = delimiteur
                substitutions = {delimiteur: '\\'+delimiteur, '\\': r'\\',
                                 '\a': r'\a', '\b': r'\b', '\f': r'\f',
                                 '\n': r'\n', '\t': r'\t', '\v': r'\v'}
            format_fin = '%s' + delimiteur
            format = '%(' + format_debut
            arguments = [None]
            # Effectuer une édition bidon, juste pour savoir dans quelle
            # colonne la chaîne débuterait.  Nous prévoierons nous-mêmes
            # les coupures de ligne une fois cette colonne connue.
            point = Point_reprise(self)
            self.editer(format, *arguments)
            marge = colonne = self.colonne
            point.reprise()
            del point.editeur
            # Formatter un mot à la fois, blancs préfixes inclus.
            # Changer de ligne si il n'y a plus de place pour le mot.
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
                                    and colonne+len(mot) > Editeur.limite-2):
                                if self.strategie == self.LIGNE:
                                    raise Editeur.Impasse("Chaîne trop longue")
                                format += format_fin
                                arguments.append(''.join(fragments_ligne))
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
                                and colonne+len(mot) > Editeur.limite-2):
                            if self.strategie == self.LIGNE:
                                raise Editeur.Impasse("Chaîne trop longue")
                            format += format_fin
                            arguments.append(''.join(fragments_ligne))
                            del fragments_ligne[:]
                        if not fragments_ligne:
                            format += '%|' + format_debut
                        fragments_ligne.append(mot)
                        format += format_fin
                        arguments.append(''.join(fragments_ligne))
                        del fragments_ligne[:]
                        colonne = marge
                        etat = BLANC
            if fragments_mot:
                mot = ''.join(fragments_mot)
                # Pour le `-2', voir le commentaire plus haut.
                if remplir is not None and colonne+len(mot) > Editeur.limite-2:
                    if self.strategie == self.LIGNE:
                        raise Editeur.Impasse("Chaîne trop longue")
                    format += format_fin
                    arguments.append(''.join(fragments_ligne))
                    del fragments_ligne[:]
                if not fragments_ligne:
                    format += '%|' + format_debut
                fragments_ligne.append(mot)
            if fragments_ligne:
                format += format_fin
                arguments.append(''.join(fragments_ligne))
            format += '%)'
            # S'assurer aussi qu'aucun remplissage n'aura lieu.
            if remplir is not None:
                self.remplir = False
            try:
                self.editer(format, *arguments)
            finally:
                self.remplir = remplir

        def essai_delimiteur_triple():
            # Tenter une disposition avec un triple délimiteur.
            fragments = []
            write = fragments.append
            if raw:
                write('r' + delimiteur * 3 + '\\\n')
            else:
                write(delimiteur * 3 + '\\\n')
                # `\n' se substitue par lui-même, tout simplement.
                substitutions = {'\n': '\n', '\\': r'\\', '\a': r'\a',
                                 '\b': r'\b', '\f': r'\f', '\v': r'\v'}
            for caractere in texte:
                if raw:
                    write(caractere)
                elif caractere in substitutions:
                    write(substitutions[caractere])
                elif not est_imprimable(caractere):
                    write(repr(caractere)[1:-1])
                else:
                    write(caractere)
            if caractere != '\n':
                write('\\\n')
            write(delimiteur * 3)
            self.write(''.join(fragments))

        essais = []
        if not texte or not triple:
            essais.append((essai_delimiteur_ligne, self.LIGNE))
        if texte and not triple:
            essais.append((essai_delimiteur_simple, self.COLONNE))
            essais.append((essai_delimiteur_simple, self.MIXTE))
        if texte:
            essais.append((essai_delimiteur_triple, self.COLONNE))
            essais.append((essai_delimiteur_triple, self.MIXTE))
        self.tenter_essais(*essais)

    def disposer_constante(self, valeur):
        # Formatter la constante VALEUR, qui ne peut être une chaîne.
        if isinstance(valeur, float):
            sys.stderr.write(
                "ATTENTION: les valeurs flottantes ne sont pas fiables.\n"
                "(Il s'agit d'un bug dans `import compiler'.  Misère!)\n")
        self.write(repr(valeur))

    def disposer(self, format, *arguments):
        # DISPOSER tente possiblement plusieurs stratégies, alors que EDITER
        # se contente de la stratégie déclarée courante.
        if '%' in format:

            def essai():
                self.editer(format, *arguments)

            for specification in '%(', '%\\', '%|', '%:':
                if specification in format:
                    self.tenter_triplet(essai, essai, essai)
                    break
            else:
                essai()
        else:
            assert not arguments, (format, arguments)
            self.write(format)

    def tenter_triplet(self, fonction_ligne, fonction_colonne, fonction_mixte):
        self.tenter_essais((fonction_ligne, self.LIGNE),
                           (fonction_colonne, self.COLONNE),
                           (fonction_mixte, self.MIXTE))

    def tenter_essais(self, *essais):
        # Établir une liste d'essais admissibles dans le contexte courant.
        essais_retenus = []
        for fonction, strategie in essais:
            if fonction is not None and strategie <= self.strategie:
                essais_retenus.append((fonction, strategie))
        if len(essais_retenus) == 0:
            raise self.Impasse("Comment faire?!")
        # Tenter tous les essais admissibles de la liste.
        strategie = self.strategie
        try:
            if len(essais_retenus) == 1:
                # Exécuter l'essai sans prévoir de reprises.
                fonction, self.strategie = essais_retenus[0]
                self.debug('Essai', '1/1')
                fonction()
            else:
                # Il faudra choisir.  Accumuler un point de reprise par succès.
                self.compteur_choix += 1
                self.compteur_essais += len(essais_retenus)
                point = Point_reprise(self)
                points = []
                for compteur, (fonction, self.strategie) in (
                        enumerate(essais_retenus)):
                    point.reprise()
                    self.debug('Essai',
                               '%d/%d' % (compteur + 1, len(essais_retenus)))
                    try:
                        fonction()
                    except self.Impasse:
                        self.compteur_impasses += 1
                    else:
                        points.append(Point_reprise(self))
                        self.debug('Sauve-%d' % len(points),
                            '%d/%d' % (compteur + 1, len(essais_retenus)))
                        if self.strategie == self.LIGNE:
                            # On ne peut théoriquement pas améliorer une
                            # stratégie LIGNE réussie.
                            break
                # Conserver la meilleure stratégie.
                if not points:
                    raise self.Impasse("Comment faire?!")
                meilleur = min(points)
                if len(points) > 1:
                    for compteur, point in enumerate(points):
                        point.debug(point is meilleur, compteur + 1,
                                    len(points))
                meilleur.reprise()
                # Briser la circularité des références.
                for point in points:
                    del point.editeur
        finally:
            self.strategie = strategie

    def editer(self, format, *arguments):
        # Produire FORMAT en sortie tout en interprétant les séquences
        # formées d'un pourcent et d'une lettre de spécification.  Certaines
        # spécifications consomment l'un des ARGUMENTS supplémentaires fournis,
        # tous les arguments doivent être finalement consommés par le format.

        # La séquence `%%' produit un seul `%'.  `%_' produit une espace ou
        # non, selon la priorité courante ou la valeur de RUSTINE_ESPACES,
        # RUSTINE_ESPACES indique un nombre de niveaux d'expression pour
        # lesquels on ajoute un blanc de part et d'autre de chaque opérateur.
        # S'il vaut zéro ou est négatif, de tels blancs ne sont pas ajoutés.
        # `%s' et `%^' disposent respectivement une chaîne ou un sous-arbre,
        # fournis en argument.

        # `%(' et `%)' encadrent un fragment de texte dont la priorité est
        # possiblement différente, la nouvelle priorité est donnée en argument
        # pour `%(', cet argument est None si la priorité ne doit pas changer.
        # Le fragment de texte est placé entre parenthèses si sa priorité du
        # fragment n'est pas plus grande que celle du texte environnant, ou
        # encore, pour permettre souligner le cisèlement en stratégie COLONNE
        # ou MIXTE, et dans le cas de cisèlement, ces parenthèses servent
        # aussi à continuer une ligne de code Python.  Lorsqu'une paire `%('
        # et `%)' produit effectivement des parenthèses, l'effet de `%('
        # implique automatiquement `%=%\' avec un argument de -1 pour la
        # nouvelle priorité, l'effet de '%)' implique automatiquement `%/'.
        # `%=' force une priorité fournie en argument, sans production de
        # parenthèses, c'est utile après un délimiteur ouvrant explicite.

        # '%\' imbrique la marge davantage, cette marge sera effective pour
        # les lignes de continuation, '%/' rétablit la marge à sa valeur
        # précédente et possiblement, tente de combiner les lignes accumulées
        # depuis le changement de marge afin de mieux remplir les lignes.
        # `%|' termine la ligne courante et force le commencement d'une autre.
        # Ces trois spécifications sont sans effet en stratégie LIGNE.

        # `%:' produit un deux-points et aussi, dans l'interprétation du format
        # qui précède, via RUSTINE_MARGE qui peut fixer une marge minimum,
        # force une imbrication d'au moins une indentation et demie pour les
        # lignes de continuation. `%!', via RUSTINE_PARENTHESES, commande
        # l'économie de la paire de parenthèses qui serait possiblement
        # provoquée pour fins de ciselage par le `%(' suivant.  Mais l'effet
        # de RUSTINE_PARENTHESES est désamorcé dès une écriture.

        self.niveau += 1
        self.debug('Format', format)
        strategie = self.strategie
        pile_delimiteurs = []
        # Les piles suivantes sont traitées à la fin du `try:/finally:'.
        pile_marges = []
        pile_priorites = []
        pile_rustines_marge = []
        pile_rustine_parentheses = [self.rustine_parentheses]
        pile_rustines_espaces = []
        if '%:' in format:
            pile_rustines_marge.append(self.rustine_marge)
            self.rustine_marge = (self.marge + Disposeur.indentation
                                  + (Disposeur.indentation + 1) // 2)
        try:
            index = 0
            position = format.find('%')
            while position >= 0:
                if position > 0:
                    self.write(format[:position])
                specification = format[position + 1]
                argument = None
                if specification == '%':
                    self.write('%')
                elif specification == '_':
                    if (self.priorite <= PRIORITE_RUSTINE
                          or self.rustine_espaces > 0):
                        self.write(' ')
                elif specification == 's':
                    argument = arguments[index]
                    index += 1
                    if argument:
                        self.write(argument)
                elif specification == '^':
                    argument = arguments[index]
                    index += 1
                    self.debug('Visit', argument)
                    self.visit(argument)
                elif specification == '(':
                    argument = arguments[index]
                    index += 1
                    pile_rustines_espaces.append(self.rustine_espaces)
                    if (argument is not None
                          and not argument == self.priorite == PRIORITE_APPEL
                          and argument <= self.priorite):
                        parentheser = True
                    elif self.strategie == self.LIGNE:
                        parentheser = False
                    elif self.rustine_parentheses:
                        self.rustine_parentheses = False
                        parentheser = False
                    else:
                        parentheser = True
                    if parentheser:
                        self.write('(')
                        #self.rustine_parentheses = True
                        pile_delimiteurs.append(')')
                        self.rustine_espaces = 2
                        # Même code que pour `%\' plus bas.
                        pile_marges.append(self.marge)
                        debut = self.ligne - 1
                        if strategie is self.MIXTE:
                            self.marge += Disposeur.indentation
                            if self.colonne > self.marge:
                                self.write('\n')
                        else:
                            self.marge = max(self.colonne, self.marge)
                    else:
                        pile_delimiteurs.append(None)
                    pile_priorites.append(self.priorite)
                    if argument is not None:
                        self.priorite = argument
                elif specification == ')':
                    delimiteur = pile_delimiteurs.pop()
                    if delimiteur is not None:
                        self.write(delimiteur)
                        # Même code que pour '%/' plus bas.
                        self.remplir_lignes_depuis(debut)
                        self.marge = pile_marges.pop()
                    self.priorite = pile_priorites.pop()
                    self.rustine_espaces = pile_rustines_espaces.pop()
                elif specification == '=':
                    argument = arguments[index]
                    index += 1
                    self.priorite = argument
                    if argument == PRIORITE_TUPLE:
                        self.rustine_espaces = 2
                elif specification == '\\':
                    # Note: RUSTINE_ESPACES est remis à zéro lorsque `%\' est
                    # utilisé explicitement (comme à la suite de `[' ou `{'),
                    # mais pas lorsque l'effet de `%\' est implicite via `%('.
                    self.rustine_espaces = 0
                    if strategie is not self.LIGNE:
                        pile_marges.append(self.marge)
                        debut = self.ligne - 1
                        if strategie is self.MIXTE:
                            # Cas de la stratégie MIXTE.
                            self.marge += Disposeur.indentation
                            if self.colonne > self.marge:
                                self.write('\n')
                        else:
                            # Cas de la stratégie COLONNE.
                            self.marge = max(self.colonne, self.marge)
                elif specification == '/':
                    if strategie is not self.LIGNE:
                        self.remplir_lignes_depuis(debut)
                        self.marge = pile_marges.pop()
                elif specification == '|':
                    if strategie is not self.LIGNE:
                        self.write('\n')
                        if self.rustine_marge is not None:
                            self.marge = max(self.rustine_marge, self.marge)
                elif specification == ':':
                    self.write(':')
                    if '%:' not in format[position+2:]:
                        self.rustine_marge = pile_rustines_marge.pop()
                    pile_marges.append(self.marge)
                    self.marge += Disposeur.indentation
                elif specification == '!':
                    self.rustine_parentheses = True
                else:
                    assert False, specification
                self.debug("Après %" + specification, argument)
                format = format[position+2:]
                position = format.find('%')
            assert index == len(arguments), (index, arguments)
            if format:
                self.write(format)
        finally:
            while pile_rustines_espaces:
                self.rustine_espaces = pile_rustines_espaces.pop()
            while pile_rustine_parentheses:
                self.rustine_parentheses = pile_rustine_parentheses.pop()
            while pile_rustines_marge:
                self.rustine_marge = pile_rustines_marge.pop()
            while pile_priorites:
                self.priorite = pile_priorites.pop()
            while pile_marges:
                self.marge = pile_marges.pop()
            self.niveau -= 1

    def write(self, texte):
        if self.colonne == 0:
            self.ligne += 1
            texte = ' '*self.marge + texte
        if self.mise_au_point == 1:
            texte2 = ''
            marque = Editeur.noms_strategies[self.strategie][0]
            for caractere in texte:
                if caractere.isalnum():
                    texte2 += marque
                else:
                    texte2 += caractere
            texte = texte2
        self.append(texte)
        if '\n' in texte:
            if texte.endswith('\n'):
                self.ligne += texte.count('\n') - 1
                self.colonne = 0
            else:
                self.ligne += texte.count('\n')
                self.colonne = len(texte.split('\n')[-1])
        else:
            self.colonne += len(texte)
        if self.remplir is not None and self.colonne > Editeur.limite:
            self.debug_texte('I')
            raise self.Impasse("Débordement de ligne")
        self.debug_texte('w')
        self.rustine_parentheses = False

    def remplir_lignes_depuis(self, index):
        lignes = ''.join(self).splitlines()
        if index < len(lignes) - 2:
            marge = marge_gauche(lignes[index+1])
            if len(lignes[index]) == marge:
                # Si le positionnement vertical de la seconde ne change pas,
                # remplir inconditionnellement des deux premières lignes.
                lignes[index] += lignes.pop(index + 1)[marge:]
            if self.remplir:
                while index < len(lignes) - 1:
                    if (marge_gauche(lignes[index+1]) == marge
                          and ((len(lignes[index])
                                + len(lignes[index+1].rstrip()) - marge)
                               <= Editeur.limite)):
                        lignes[index] += lignes.pop(index + 1)[marge:]
                    else:
                        index += 1
                        while (index < len(lignes) - 1
                               and marge_gauche(lignes[index]) != marge):
                            index += 1
            self[:] = ['\n'.join(lignes)]
            self.ligne = len(lignes)
            self.colonne = len(lignes[-1])
            self.debug_texte('r')

class Point_reprise:
    def __init__(self, editeur):
        self.editeur = editeur
        self.texte = ''.join(editeur)
        self.ligne = editeur.ligne
        self.colonne = editeur.colonne
        self.strategie = editeur.strategie

    def __cmp__(self, other):
        return (cmp(self.ligne, other.ligne)
                or cmp(self.longueur_noire(), other.longueur_noire())
                or cmp(self.strategie, other.strategie))

    def debug(self, meilleur, ordinal, total):
        if Editeur.mise_au_point > 1:
            Editeur.mise_au_point += 1
            self.editeur.debug("Point " + '·+'[meilleur],
                               ('%d/%d L%d N%d %s'
                                % (ordinal, total, self.ligne,
                                   self.longueur_noire(),
                                   Editeur.noms_strategies[self.strategie])))
            Editeur.mise_au_point -= 1
            sys.stdout.write(self.texte + PIED_DE_MOUCHE + '\n')

    def reprise(self):
        self.editeur[:] = [self.texte]
        self.editeur.ligne = self.ligne
        self.editeur.colonne = self.colonne

    def longueur_noire(self):
        # Retourner le nombre de caractères non-blancs du texte.
        return len(self.texte.replace(' ', '').replace('\n', ''))

def est_none(noeud):
    # Retourner True si le noeud représente la constante None.
    return isinstance(noeud, compiler.ast.Const) and noeud.value is None

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

installer_vim()
vim.command('autocmd FileType python python pynits.installer_vim()')
