#!/usr/bin/env python3
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Interprète pour rendre "actives" certaines pages HTML.

Cet outil a pour but de traiter des pages HTML contenant des directives
spéciales, orientées vers le langage Python, et de les exécuter, donnant
ainsi l'illusion que ces pages HTML sont actives.

Usage: traiter [OPTION]... [PAGE [AFFECTATION]...]]

Options:
  -c CONFIG   Utiliser le fichier CONFIG plutôt que `traiter.conf'.
  -p PROJET   Utiliser PROJET comme nom de projet.
  -w          Formatter la page produite via le programme `w3m'.

La détermination du projet et de son fichier de configuration peut faire
intervenir plusieurs cas de figure.

Le projet et son fichier de configuration
Le fichier de configuration est dérivé du nom de projet.

le nom du fichier à
traiter, et 3) d'autres affectations à utiliser.  Voir les détails plus bas.

La valeur `-' pour PAGE représente l'entrée standard.  Si l'argument
PAGE est fourni, il contient le nom du fichier à traiter.  Sinon, la
variable d'environnement PATH_TRANSLATED doit contenir le nom du fichier
à traiter.

Les affectations proviennent de plusieurs sources.  Les affectations de
la commande d'appel ont la plus haute priorité, chaque AFFECTATION y
possède la forme CHAMP=VALEUR.  Les affectations comprennent aussi tous
les choix inscrits dans le fichier de configuration.  En basse priorité,
les affectations peuvent provenir d'un formulaire CGI rempli: soit par
le décodage de la variable QUERY_STRING lorsque REQUEST_METHOD vaut GET,
ou le décodage de l'entrée standard lorsque REQUEST_METHOD vaut POST.

Un argument PAGE vide, par exemple donné comme '', n'est pas considéré comme
fourni.  Le résultat est toujours produit sur la sortie standard.
"""

import cgi
import os
import sys


# Exception qui suit la production d'une page d'erreur dans Traiter.  Elle
# est utilisée pour inhiber toute production HTML supplémentaire.

class Interruption(Exception):
    pass


def main(*arguments):
    # Décoder l'appel.
    contexte = {}
    option_w3m = False
    if len(arguments) == 0:
        # On présume un appel en tant que script CGI.  Utiliser les variables
        # d'environnement pour déterminer la page à traiter et comment
        # retrouver le contenu du formulaire.
        fichier_a_traiter = os.environ.get('PATH_TRANSLATED')
        if fichier_a_traiter is None:
            sys.stdout.write(__doc__)
            sys.exit(0)
        formulaire = cgi.FieldStorage()
        for nom in list(formulaire.keys()):
            valeurs = formulaire[nom]
            if isinstance(valeurs, list):
                # REVOIR!
                #erreur("Le formulaire a fourni `%s' %d fois."
                #            % (nom, len(valeurs)))
                contexte[nom] = valeurs[-1].value
            else:
                contexte[nom] = valeurs.value
        # Produire le Content-Type immédiatement, pour que le fureteur soit
        # patient durant le traitement de la page.
        charset = os.environ.get('CHARSET', 'ISO-8859-1')
        sys.stdout.write("Content-type: text/html; charset=%s\n\n" % charset)
        sys.stdout.flush()
    else:
        # L'appel se fait probablement via un shell interactif.  Étudier les
        # arguments fournis par l'utilisateur.
        import getopt
        options, arguments = getopt.getopt(arguments, 'w')
        for option, valeur in options:
            if option == '-w':
                option_w3m = True
        fichier_a_traiter = arguments[0]
        for argument in arguments[1:]:
            assert '=' in argument, argument
            nom, valeur = argument.split('=', 1)
            contexte[nom] = valeur
    # En cas de conflit, oblitérer les variables du formulaire par celles
    # provenant de la configuration.  Sans cet ordre des choses, il y
    # aurait un vice important de sécurité.
    config = get_config(os.path.dirname(fichier_a_traiter))
    if config.has_section('contexte'):
        for option in config.options('contexte'):
            contexte[option] = config.get('contexte', option)
    # Ajuster PATH.
    import configparser
    try:
        library = config.get('DEFAULT', 'Library')
    except configparser.NoOptionError:
        pass
    else:
        os.environ['PATH'] = '%s:%s' % (library, os.environ['PATH'])
    # Déterminer comment écrire.
    try:
        if option_w3m:
            output = os.popen('w3m -T text/html -dump', 'w')
            try:
                Traiter(file(fichier_a_traiter), contexte, output.write)
            finally:
                output.close()  # Grrr!  REVOIR: pourquoi?
        else:
            Traiter(file(fichier_a_traiter), contexte, sys.stdout.write)
    except Interruption:
        pass


def get_config(repertoire=None,
               cache={}):
    try:
        from Local import commun
    except ImportError:
        pass
    else:
        return commun.config()
    # Hors du SRAM, le module `Local.commun' n'existe pas.  Alors, le code
    # qui suit est une version simplifiée de `Local.commun.config()'.
    # Obtenir un contexte de `config.py', en cherchant d'abord dans
    # le répertoire du fichier à traiter, puis dans deux répertoires
    # supérieurs au besoin.
    en_examen = repertoire or os.getcwd()
    for compteur in range(3):
        config = cache.get(en_examen)
        if config is not None:
            return config
        if os.path.exists(en_examen + '/config.py'):
            sys.path.insert(0, en_examen)
            from config import contexte
            del sys.path[0]
            break
        en_examen = os.path.dirname(en_examen)
    else:
        contexte = {}
    # Si le projet n'est pas défini dans le contexte, mais qu'il est
    # fourni par la variable d'environnement `CONFIG_PROJET', l'ajouter
    # au contexte.
    projet = contexte.get('projet')
    if projet is None:
        projet = os.environ.get('CONFIG_PROJET')
        if projet is not None:
            contexte['projet'] = projet
    # Produire une configuration, à partir d'un fichier de configuration
    # si nous le trouvons, vide autrement.
    import configparser
    config = configparser.ConfigParser()
    if projet is not None:
        fichier = (os.environ.get('CONFIG_%s' % projet.upper())
                   or '/usr/local/etc/%s.conf' % projet)
        if os.path.exists(fichier):
            config.read(fichier)
    # Compléter la section `[contexte]' à partir du contexte déjà obtenu.
    # Dans le cas de conflit entre définitions, un fichier `config.py'
    # a priorité sur un fichier de configuration.
    if contexte:
        if not config.has_section('contexte'):
            config.add_section('contexte')
        for nom, valeur in contexte.items():
            config.set('contexte', nom, valeur)
    # S'occuper de PythonPath automatiquement, s'il est défini.
    try:
        chaine = config.get('DEFAULT', 'PythonPath')
    except configparser.NoOptionError:
        chaine = None
    if chaine is not None:
        morceaux = chaine.split(':')
        morceaux.reverse()
        for repertoire in morceaux:
            if repertoire in sys.path:
                sys.path.remove(repertoire)
            if os.path.isdir(repertoire):
                sys.path.insert(0, repertoire)
    # Retourner la configuration.
    cache[repertoire] = config
    return config


class Traiter:

    def __init__(self, fichier, contexte, write, write_errors=None):
        # Traiter la page HTML présente dans NOM_FICHIER.  CONTEXTE est un
        # dictionnaire représentant le contexte d'évaluation, il est transmis
        # à toute instance de Traiter résultant d'une directive Inclure.
        # Utiliser WRITE pour toute écriture dans la page résultante.
        # WRITE_ERRORS est utilisé en cas d'erreur, None implique WRITE.
        self.compilateurs = {
            # Pré-traitement.
            'Délimiter': self.compiler_delimiter,
            # Énoncés simples.
            'Inclure': self.compiler_inclure,
            'Sauver': self.compiler_sauver,
            'FinSauver': self.compiler_finsauver,
            'Faire': self.compiler_faire,
            'Afficher': self.compiler_afficher,
            'Tracer': self.compiler_tracer,
            'FinTracer': self.compiler_fintracer,
            # Structures conditionnelles.
            'Si': self.compiler_si,
            'SinonSi': self.compiler_sinonsi,
            'Sinon': self.compiler_sinon,
            'FinSi': self.compiler_finsi,
            # Structures itératives.
            'Chacun': self.compiler_chacun,
            'FinChacun': self.compiler_finchacun,
            'Tantque': self.compiler_tantque,
            'FinTantque': self.compiler_fintantque,
            'Suffit!': self.compiler_suffit,
            }
        self.charset = os.environ.get('CHARSET', 'ISO-8859-1')
        self.write = write
        self.write_errors = write_errors or write
        self.dans_page_erreur = False
        self.contexte = contexte
        try:
            if isinstance(fichier, str):
                self.location = '<string>', 0, None
                self.compiler(fichier, '<string>')
            else:
                self.location = fichier.name, 0, None
                self.compiler(fichier.read(), fichier.name)
            self.executer()
        except Interruption:
            raise
        except:
            self.erreur("Erreur durant le traitement!", True)

    def compiler(self, texte, nom_fichier):
        # CODE, qui a la forme d'une liste d'instructions, est fabriqué à la
        # compilation et dirige l'exécution.  Toute adresse, comptée à partir
        # de zéro, est en fait un indice dans CODE.  Chaque instruction est un
        # triplet (LOCATION, FONCTION, ARGUMENTS).  LOCATION contient une
        # référence à la page source qui sert à clarifier les diagnostics émis
        # en cas d'erreur: c'est un triplet donnant le nom du fichier, le
        # numéro de la ligne dans ce fichier, ainsi qu'un fragment, si non
        # None, du texte original représentant l'instruction.  FONCTION est la
        # méthode à utiliser pour l'exécution de l'instruction.  ARGUMENTS
        # contient, si non None, une liste des arguments à utiliser, sa
        # constitution varie selon la nature de l'instruction.  Voici, mais
        # uniquement pour les méthode d'exécution qui exigent des arguments,
        # ceux qui sont attendus, dans l'ordre:
        # ALLER_A
        #   Adresse de la prochaine instruction.
        # CHACUN
        #   Adresse de la fin du bloc Chacun.
        #   Nom de la variable d'itération.
        #   Code Python compilé évaluant la liste d'itération.
        #   Indice dans la liste d'itération de la valeur à utiliser.  Ou None.
        #   Liste d'itération, lorsque bloc actif.  None si inactif.
        # COPIER
        #   Texte à copier.
        # FAIRE
        #   Code Python compilé qu'il faut exécuter.
        # INCLURE
        #   Nom du fichier inclus, relativement à DOCUMENT_ROOT.
        # SAUVER
        #   Adresse de la fin du bloc Sauver.
        #   Nom de la variable qui recevra le texte sauvé.
        # SI
        #   Adresse de la prochaine instruction si condition non réalisée.
        #   Code Python compilé évaluant la condition du test.
        # SUFFIT
        #   Adresse de l'instruction CHACUN ou TANTQUE débutant le bloc.
        #   Vrai s'il s'agit d'un bloc Chacun plutôt que Tantque.
        self.code = []
        # PILE décrit l'imbrication des structures de programmation durant la
        # compilation.  Le premier élément de PILE correspond à la structure
        # la plus externe, le dernier élément à la structure la plus interne.
        # Chaque élément [BLOC, LOCATION, ADRESSE...] est une liste de trois
        # sous-éléments, ou plus.  BLOC vaut `Chacun', `Si' ou `Tantque' selon
        # la nature du bloc.  LOCATION décrit la première instruction du bloc.
        # Chaque ADRESSE qui n'est pas None est l'adresse d'une instruction
        # dans CODE qu'il faudra altérer durant la compilation de ce bloc.
        self.pile = []
        # Pendant la compilation, PILE_DELIMITEURS décrit l'imbrication des
        # valeurs délimiteurs précédant les délimiteurs qui sont courants.
        # Chaque élément de la pile contient un doublet (DEBUT, FIN) qui donne
        # les délimiteurs de début et de fin.
        self.delimiteur_debut = '<!--:'
        self.delimiteur_fin = ':-->\n'
        self.pile_delimiteurs = []
        # LIGNE est le numéro de la ligne textuelle en cours d'analyse,
        # il tient compte de toutes les fins de ligne rencontrées entre le
        # début du texte et la position PRECEDENT.  La partie du texte après
        # la position CURSEUR n'a pas encore été vue par la compilation.
        ligne = 1
        precedent = 0
        curseur = 0
        self.location = nom_fichier, ligne, None
        while True:
            debut = texte.find(self.delimiteur_debut, curseur)
            if debut < 0:
                if curseur < len(texte):
                    self.compiler_copier(texte[curseur:])
                break
            if curseur < debut:
                self.compiler_copier(texte[curseur:debut])
            curseur = debut + len(self.delimiteur_debut)
            ligne += texte.count('\n', precedent, curseur)
            precedent = curseur
            self.location = nom_fichier, ligne, None
            position = texte.find(self.delimiteur_fin, curseur)
            if position < 0:
                fin = curseur
                self.erreur("Terminateur absent ou incorrect.")
                continue
            fin = curseur = position + len(self.delimiteur_fin)
            ligne += texte.count('\n', precedent, curseur)
            precedent = curseur
            fragment = (texte[(debut + len(self.delimiteur_debut)):
                              (fin - len(self.delimiteur_fin))]
                        .strip())
            self.location = nom_fichier, ligne, fragment
            fragments = fragment.split(None, 1)
            compilateur = self.compilateurs.get(fragments[0])
            if compilateur:
                if len(fragments) < 2:
                    compilateur('')
                else:
                    compilateur(fragment[len(fragments[0]):])  # FIXME: ???
                continue
            self.erreur("Directive non reconnue")
        while self.pile:
            self.location = self.pile[-1][1]
            self.erreur("Bloc `%s' mal terminé." % self.pile[-1][0])
            self.pile.pop()

    def compiler_afficher(self, texte):
        texte = texte.lstrip()
        if texte == 'arguments':
            afficheur = self.executer_afficher_arguments
        elif texte == 'code':
            afficheur = self.executer_afficher_code
        elif texte == 'environnement':
            afficheur = self.executer_afficher_environnement
        elif texte == 'variables':
            afficheur = self.executer_afficher_variables
        else:
            self.erreur("Requête invalide dans Afficher.")
            return
        self.code.append((self.location, afficheur, None))

    def compiler_chacun(self, texte):
        # REVOIR: Peut-être utiliser "Chaque VARIABLE dans EXPRESSION"?
        fragments = texte.split(':', 1)
        if len(fragments) != 2:
            self.erreur("Séparateur `:' attendu dans Chacun.")
            return
        nom = fragments[0].strip()
        expression = fragments[1].lstrip()
        if expression == '':
            self.erreur("Expression manquante dans Chacun.")
            return
        try:
            code = self.faire_code(expression, 'Chacun', 'eval')
        except:
            self.erreur("Expression invalide dans Chacun.", True)
            return
        self.empiler('Chacun')
        self.code.append((self.location, self.executer_chacun,
                          [None, nom, code, None, None]))

    def compiler_copier(self, texte):
        self.code.append((self.location, self.executer_copier, [texte]))

    def compiler_delimiter(self, texte):
        texte = texte.lstrip()
        if texte:
            try:
                valeurs = eval(texte, {}, {})
            except:
                self.erreur("Expression invalide dans Délimiter.", True)
                return
            if len(valeurs) != 2:
                self.erreur("Délimiter doit fournir deux valeurs.")
                return
            if not (isinstance(valeurs[0], str)
                    and isinstance(valeurs[1], str)):
                self.erreur("Délimiter doit fournir des chaînes.")
                return
            self.pile_delimiteurs.append((self.delimiteur_debut,
                                          self.delimiteur_fin))
        elif self.pile_delimiteurs:
            valeurs = self.pile_delimiteurs.pop()
        else:
            self.erreur("`Délimiter' mal placé.")
            return
        self.delimiteur_debut = valeurs[0]
        self.delimiteur_fin = valeurs[1]

    def compiler_faire(self, texte):
        lignes = texte.split('\n')
        if len(lignes) == 1:
            texte = texte.lstrip() + '\n'
        else:
            if lignes[0].rstrip():
                self.erreur("Faire doit être seul sur sa ligne"
                            " dans un Faire multi-lignes.")
                return
            lignes[0] = ''
            import re
            marge = re.match('[ \t]*', lignes[1]).group(0)
            for compteur in range(1, len(lignes)):
                if lignes[compteur].rstrip():
                    if lignes[compteur][:len(marge)] != marge:
                        self.erreur("Marge inconsistante dans Faire.")
                        return
                    lignes[compteur] = lignes[compteur][len(marge):] + '\n'
                else:
                    lignes[compteur] = '\n'
            texte = ''.join(lignes)
        try:
            code = self.faire_code(texte, 'Faire', 'exec')
        except:
            self.erreur("Énoncé invalide dans Faire.", True)
            return
        self.code.append((self.location, self.executer_faire, [code]))

    def compiler_finchacun(self, texte):
        texte = texte.lstrip()
        adresses = self.depiler('Chacun')
        if not adresses:
            return
        if texte:
            self.erreur("Texte intempestif dans FinChacun.")
            return
        # Retourner au début de la boucle.
        adresse = adresses[0]
        self.code.append((self.location, self.executer_saut, [adresse]))
        # Ajuster le saut du test conditionel.
        arguments = self.code[adresse][2]
        arguments[0] = len(self.code)

    def compiler_finsauver(self, texte):
        texte = texte.lstrip()
        adresses = self.depiler('Sauver')
        if not adresses:
            return
        if texte:
            self.erreur("Texte intempestif dans FinSauver.")
            return
        # Ajuster la fin de la région à sauver.
        adresse = adresses[0]
        arguments = self.code[adresse][2]
        arguments[0] = len(self.code)

    def compiler_finsi(self, texte):
        texte = texte.lstrip()
        adresses = self.depiler('Si')
        if not adresses:
            return
        if texte:
            self.erreur("Texte intempestif dans FinSi.")
            return
        # Ajuster tous les sauts qui doivent l'être:
        # - le saut du test conditionel précédent,
        # - le saut à la fin de chaque séquence après `si' ou `sinon'.
        for adresse in adresses:
            if adresse is not None:
                arguments = self.code[adresse][2]
                arguments[0] = len(self.code)

    def compiler_fintantque(self, texte):
        texte = texte.lstrip()
        adresses = self.depiler('Tantque')
        if not adresses:
            return
        if texte:
            self.erreur("Texte intempestif dans FinTantque.")
            return
        # Retourner au début de la boucle.
        adresse = adresses[0]
        self.code.append((self.location, self.executer_saut, [adresse]))
        # Ajuster le saut du test conditionel.
        arguments = self.code[adresse][2]
        arguments[0] = len(self.code)

    def compiler_fintracer(self, texte):
        texte = texte.lstrip()
        if texte:
            self.erreur("Texte intempestif dans FinTracer.")
            return
        self.code.append((self.location, self.executer_fintracer, None))

    def compiler_inclure(self, texte):
        fichier = texte.lstrip()
        self.code.append((self.location, self.executer_inclure, [fichier]))

    def compiler_sauver(self, texte):
        nom = texte.lstrip()
        self.empiler('Sauver')
        self.code.append((self.location, self.executer_sauver, [None, nom]))

    def compiler_si(self, texte):
        texte = texte.lstrip()
        try:
            code = self.faire_code(texte, 'Si', 'eval')
        except:
            self.erreur("Expression invalide dans Si.", True)
            return
        # Préparer un saut conditionnel à compléter plus tard.
        self.empiler('Si')
        self.code.append((self.location, self.executer_si, [None, code]))

    def compiler_sinon(self, texte):
        texte = texte.lstrip()
        if self.pile[-1][0] != 'Si' or self.pile[-1][2] is None:
            self.erreur("`Sinon' mal placé.")
            return
        if texte:
            self.erreur("Texte intempestif dans Sinon.")
            return
        # Préparer un saut inconditionnel à compléter au FinSi.
        self.pile[-1].append(len(self.code))
        self.code.append((self.location, self.executer_saut, [None]))
        # Ajuster le saut du test conditionel précédent.
        arguments = self.code[self.pile[-1][2]][2]
        arguments[0] = len(self.code)
        self.pile[-1][2] = None

    def compiler_sinonsi(self, texte):
        texte = texte.lstrip()
        if self.pile[-1][0] != 'Si' or self.pile[-1][2] is None:
            self.erreur("`SinonSi' mal placé.")
            return
        try:
            code = self.faire_code(texte, 'SinonSi', 'eval')
        except:
            self.erreur("Expression invalide dans SinonSi.", True)
            return
        # Préparer un saut inconditionnel à compléter au FinSi.
        self.pile[-1].append(len(self.code))
        self.code.append((self.location, self.executer_saut, [None]))
        # Ajuster le saut du test conditionel précédent.
        arguments = self.code[self.pile[-1][2]][2]
        arguments[0] = len(self.code)
        # Préparer un saut conditionnel à compléter plus tard.
        self.pile[-1][2] = len(self.code)
        self.code.append((self.location, self.executer_si, [None, code]))

    def compiler_suffit(self, texte):
        texte = texte.lstrip()
        chacun = None
        compteur = len(self.pile)
        while chacun is None and compteur > 0:
            compteur -= 1
            type = self.pile[compteur][0]
            if type == 'Chacun':
                chacun = True
            elif type == 'Tantque':
                chacun = False
        if chacun is None:
            self.erreur("`Suffit!' mal placé.")
            return
        if texte:
            self.erreur("Texte intempestif dans Suffit!.")
            return
        self.code.append((self.location, self.executer_suffit,
                          [self.pile[compteur][2], chacun]))

    def compiler_tantque(self, texte):
        texte = texte.lstrip()
        try:
            code = self.faire_code(texte, 'Tantque', 'eval')
        except:
            self.erreur("Expression invalide dans Tantque.", True)
            return
        # Préparer un saut conditionnel à compléter plus tard.
        self.empiler('Tantque')
        self.code.append((self.location, self.executer_si, [None, code]))

    def compiler_tracer(self, texte):
        texte = texte.lstrip()
        if texte:
            self.erreur("Texte intempestif dans Tracer.")
            return
        self.code.append((self.location, self.executer_tracer, None))

    def depiler(self, bloc):
        if self.pile:
            attendu = self.pile[-1][0]
        else:
            attendu = None
        if attendu == bloc:
            return self.pile.pop()[2:]
        self.erreur("Fin de `%s' vue alors que fin de `%s' attendue."
                    % (bloc, attendu))

    def empiler(self, bloc):
        self.pile.append([bloc, self.location, len(self.code)])

    def faire_code(self, texte, directive, action):
        if isinstance(texte, str):
            return compile(texte, directive, action)
        return compile('# -*- coding: %s -*-\n' % self.charset + texte,
                       directive, action)

    def executer(self):
        self.tracage = False
        self.curseur = 0
        while self.curseur < len(self.code):
            self.location, processeur, arguments = self.code[self.curseur]
            self.curseur += 1
            if arguments:
                processeur(*arguments)
            else:
                processeur()

    def executer_afficher_arguments(self):
        write = self.write
        write('<br>\n'
              '<table border=1>\n'
              "<tr><th>No.</th>"
              "<th>Argument du programme</th></tr>\n")
        for compteur in range(len(sys.argv)):
            write('<tr><td align=right>%d.</td><td>%s</td></tr>\n'
                  % (compteur, cgi.escape(repr(sys.argv[compteur]))))
        write('</table>\n'
              '<br>\n')

    def executer_afficher_code(self):
        nom_de_processeur = {
            self.executer_chacun: 'Chacun',
            self.executer_copier: 'Copier',
            self.executer_faire: 'Faire',
            self.executer_fintracer: 'FinTracer',
            self.executer_inclure: 'Inclure',
            self.executer_sauver: 'Sauver',
            self.executer_saut: 'Saut',
            self.executer_si: 'Si',
            self.executer_suffit: 'Suffit!',
            self.executer_tracer: 'Tracer'}
        write = self.write
        write('<br>\n'
              '<table border=1>\n'
              '<tr><th>#</th>'
              "<th>Code</th>"
              "<th>Arguments</th>"
              "<th>Référence</th>"
              '</tr>\n')
        import types
        for compteur in range(len(self.code)):
            write('<tr>')
            ((nom_fichier, ligne, texte),
             processeur, arguments) = self.code[compteur]
            write('<td align=right valign=top>%d</td>' % compteur)
            if processeur == self.executer_afficher_arguments:
                code = 'Afficher'
                arguments = ['arguments']
            elif processeur == self.executer_afficher_code:
                code = 'Afficher'
                arguments = ['code']
            elif processeur == self.executer_afficher_environnement:
                code = 'Afficher'
                arguments = ['environnement']
            elif processeur == self.executer_afficher_variables:
                code = 'Afficher'
                arguments = ['variables']
            else:
                code = nom_de_processeur[processeur]
                if arguments is None:
                    arguments = []
                if not isinstance(arguments, (list, tuple)):
                    arguments = ['*Erreur*', arguments]
            write('<td align=center valign=top>%s</td>' % code)
            fragments = []
            for argument in arguments:
                if type(argument) is types.CodeType:
                    argument = texte
                fragments.append(cgi.escape(repr(argument)))
            if fragments:
                write('<td>%s.</td>' % '; '.join(fragments))
            else:
                write('<td> </td>')
            write('<td align=left valign=top>%s:%d</td>'
                  % (nom_fichier, ligne))
            write('</tr>\n')
        write('</table>\n'
              '<br>\n')

    def executer_afficher_environnement(self):
        write = self.write
        items = list(os.environ.items())
        items.sort()
        write('<br>\n'
              '<table border=1>\n'
              "<tr><th>Variable</th>"
              "<th>Dans l'environnement</th></tr>\n")
        for nom, valeur in items:
            write('<tr><td>%s</td><td>%s</td></tr>\n'
                  % (nom, cgi.escape(repr(valeur))))
        write('</table>\n'
              '<br>\n')

    def executer_afficher_variables(self):
        write = self.write
        write('<br>\n'
              '<table border=1>\n'
              "<tr><th>Variable</th>"
              "<th>Substitution</th></tr>\n")
        items = list(self.contexte.items())
        items.sort()
        for nom, valeur in items:
            write('<tr><td>%s</td><td>%s</td></tr>\n'
                  % (nom, cgi.escape(repr(valeur))))
        write('</table>\n'
              '<br>\n')

    def executer_chacun(self, curseur, nom, code, compteur, valeurs):
        arguments = self.code[self.curseur - 1][2]
        if valeurs is None:
            # Entrée initiale dans la boucle, fixer la liste de valeurs.
            try:
                valeurs = eval(code, globals(), self.contexte)
            except:
                self.erreur("Erreur à l'exécution dans Chacun.", True)
                return
            compteur = 0
            arguments[4] = valeurs
        if compteur == len(valeurs):
            # Toutes les valeurs ont été vues, sauter hors de la boucle.
            arguments[4] = None
            if self.tracage:
                self.tracer("Saut [%d]" % curseur)
            if curseur is not None:
                self.curseur = curseur
            return
        # Affecter la valeur suivante à la variable de contrôle.
        valeur = valeurs[compteur]
        if self.tracage:
            self.tracer("`%s' reçoit `%s'" % (nom, valeur))
        self.contexte[nom] = valeur
        arguments[3] = compteur + 1

    def executer_copier(self, texte):
        while True:
            try:
                self.write(texte % self.contexte)
            except UnicodeError:
                # REVOIR: Traiter devra fonctionner en Unicode, un jour...
                if isinstance(texte, str):
                    texte = texte.encode('UTF-8')
                for nom, valeur in self.contexte.items():
                    if isinstance(valeur, str):
                        self.contexte[nom] = valeur.encode('UTF-8')
            except KeyError as exception:
                nom = exception.args[0]
                self.contexte[nom] = "@@@ `%s' inconnu! @@@" % nom
            else:
                return

    def executer_faire(self, code):
        if self.tracage:
            self.tracer()
        try:
            exec(code, globals(), self.contexte)
        except:
            self.erreur("Erreur à l'exécution dans Faire.", True)

    def executer_fintracer(self):
        self.tracage = False

    def executer_inclure(self, nom_fichier):
        nom_fichier = self.resoudre_nom_fichier(nom_fichier % self.contexte)
        if nom_fichier is None:
            self.erreur("Ne peut lire le fichier `%s'." % nom_fichier)
            return
        Traiter(file(nom_fichier), self.contexte,
                self.write, self.write_errors)

    def executer_sauver(self, limite, nom):
        write_sauve = self.write
        try:
            fragments = []
            self.write = fragments.append
            while self.curseur < limite:
                self.location, processeur, arguments = self.code[self.curseur]
                self.curseur += 1
                if arguments:
                    processeur(*arguments)
                else:
                    processeur()
        finally:
            self.write = write_sauve
        self.contexte[nom] = ''.join(fragments)

    def executer_saut(self, curseur):
        if self.tracage:
            self.tracer('Saut [%d]' % curseur)
        if curseur is not None:
            self.curseur = curseur

    def executer_si(self, curseur, code):
        try:
            valeur = eval(code, globals(), self.contexte)
            if self.tracage:
                self.tracer('Condition: %s' % valeur)
            if not valeur:
                if curseur is not None:
                    self.curseur = curseur
        except:
            self.erreur("Erreur à l'exécution dans Si ou Tantque.", True)
            if curseur is not None:
                self.curseur = curseur

    def executer_suffit(self, adresse, chacun):
        arguments = self.code[adresse][2]
        curseur = arguments[0]
        if self.tracage:
            self.tracer('Saut [%d]' % curseur)
        if curseur is not None:
            self.curseur = curseur
        if chacun:
            arguments[4] = None

    def executer_tracer(self):
        self.tracage = True

    def tracer(self, message=None):
        adresse = self.curseur - 1
        nom_fichier, ligne, texte = self.location
        write = self.write
        write("\n")
        if message:
            write("<!-- Trace [%d]: %s -->\n" % (adresse, message))
        else:
            write("<!-- Trace [%d] -->\n" % adresse)
        write("<!-- %s:%d: %s -->\n" % (nom_fichier, ligne, str(texte)))

    def erreur(self, lignes, montrer_pile=False):
        from io import StringIO as StringIO
        tampon = StringIO()
        write = tampon.write
        # Fabriquer le diagnostic principal.
        nom_fichier, ligne, texte = self.location
        write("\n%s:%d: %s\n\n" % (nom_fichier, ligne, texte or 'Oups!'))
        if isinstance(lignes, str):
            petit_diagnostic = lignes
        else:
            petit_diagnostic = '\n'.join(lignes)
        write('%s\n' % petit_diagnostic)
        if montrer_pile:
            write('\n')
            import traceback
            traceback.print_exc(file=tampon)
        # Fabriquer l'information sur les variables.
        write("\nVariables en traitement\n")
        items = list(self.contexte.items())
        items.sort()
        for nom, valeur in items:
            write('  %-24s  %s\n' % (nom, repr(valeur)))
        write("\nVariables de l'environnement\n")
        items = list(os.environ.items())
        items.sort()
        for nom, valeur in items:
            write('  %-24s  %s\n' % (nom, repr(valeur)))
        config = get_config()
        # En mode production uniquement, envoyer un message à adresse fixe,
        # et traiter le contenu de `erreur.page' dans la page Web fabriquée.
        import configparser
        try:
            if config.getboolean('traiter', 'Production'):
                import smtplib
                smtplib.SMTP(config.get('traiter', 'MailRelay')).sendmail(
                    config.get('traiter', 'MailFrom'),
                    config.get('traiter', 'MailTo'),
                    # REVOIR: Garantir un "To:" explicite dans le message!
                    #("Subject: Problème durant l'exécution de `traiter'\n"
                    ("Subject: =?ISO-8859-1?Q?Probl=E8me?= durant"
                     " =?ISO-8859-1?Q?l'ex=E9cution?= de `traiter'\n"
                     + "To: %s" % config.get('traiter', 'MailTo')
                     + "\nContent-Type: text/plain; charset=UTF-8\n"
                     + tampon.getvalue()))
        except configparser.NoSectionError:
            pass
        except configparser.NoOptionError:
            pass
        self.write = self.write_errors
        if self.dans_page_erreur:
            self.write(
                "Ehbedon!  Erreur durant le traitement d'une erreur.\n"
                "C'est trop pour le pauvre petit moi, j'abandonne!\n")
            raise Interruption
        # Indépendamment du mode production, préparer une page HTML pour
        # signaler l'erreur à l'usager, idéalement par le traitement du
        # contenu de la page de rapport d'erreur, si une telle page existe.
        # Si elle n'existe pas, fournir en vrac l'information que nous avons.
        try:
            nom_fichier = self.resoudre_nom_fichier(
                config.get('traiter', 'PageErreur'))
        except configparser.NoSectionError:
            nom_fichier = None
        except configparser.NoOptionError:
            nom_fichier = None
        if nom_fichier is None:
            self.write("<html>\n"
                       " <head><title>Page d'erreur</title></head>\n"
                       " <body><pre>%s</pre></body>\n"
                       "</html>\n"
                       % cgi.escape(tampon.getvalue()))
        else:
            self.dans_page_erreur = True
            self.contexte['petit_diagnostic'] = petit_diagnostic
            self.contexte['gros_diagnostic'] = tampon.getvalue()
            self.compiler(file(nom_fichier).read(),
                          nom_fichier)
            self.executer()
        raise Interruption

    def resoudre_nom_fichier(self, nom_fichier):
        nom_fichier = os.path.join(os.path.dirname(self.location[0]),
                                   nom_fichier)
        if os.access(nom_fichier, os.R_OK):
            return nom_fichier

if __name__ == '__main__':
    main(*sys.argv[1:])
