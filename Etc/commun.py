#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Routines de service communes pour le projet ÉCHO, et d'autres.
"""

### Facilitateur pour la mise-au-point.

class Debug:
    """\
Usage suggéré pour imprimer ITEM1, ITEM2, ... à la fin de NOM_FICHIER:

    from Local import commun
    debug = commun.Debug('NOM_FICHIER')
    ...
    debug(ITEM1, ITEM2, ...)
    ...

Et plus tard, pour inhiber ces traces en changeant très peu le programme:

    from Local import commun
    debug = commun.NoDebug('NOM_FICHIER')
    ...
    debug(ITEM1, ITEM2, ...)
    ...

Le fichier d'erreur standard est utilisé si NOM_FICHIER n'est pas fourni.
Si ITEM est une chaîne et que cette chaîne peut être compilée et évaluée
sans erreur, alors la chaîne et sa valeur sont toutes deux affichées.
"""

    def __init__(self, nom_fichier=None):
        import pprint, sys
        self.pretty = pprint.PrettyPrinter(width=75)
        if nom_fichier is None:
            self.fichier = sys.stderr
        else:
            self.fichier = open(nom_fichier, 'a')

    def __call__(self, *objets):
        write = self.fichier.write
        write('-' * 78 + '>\n')
        import sys
        for objet in objets:
            if isinstance(objet, str):
                frame = sys._getframe(1)
                try:
                    valeur = eval(objet, frame.f_globals, frame.f_locals)
                except:
                    texte = objet
                else:
                    texte = self.pretty.pformat(valeur)
                    if '\n' in texte or len(objet) + 3 + len(texte) > 79:
                        texte = (objet + ' :\n    '
                                 + texte.replace('\n', '\n    '))
                    else:
                        texte = objet + ' : ' + texte
            else:
                texte = self.pretty.pformat(objet)
            write(texte + '\n')
        write('-' * 78 + '<\n')
        self.fichier.flush()

class NoDebug:
    def __init__(self, nom_fichier=None): pass
    def __call__(self, *objets): pass

### Configuration des projets.

configdir = '/usr/local/etc'

class Erreur_configuration(Exception): pass
class Configuration_absente(Erreur_configuration): pass
class Vieille_configuration(Erreur_configuration): pass

_config_cache = {}

def config_invalider_cache():
    _config_cache.clear()

def config(projet=None, fichier=None):
    """\
Retourne une configuration `ConfigParser' pour le projet PROJET, mais en
faisant en sorte de ne la lire qu'une seule fois.  Si PROJET n'est pas
fourni, la variable d'environnement CONFIG_PROJET peut alors contenir le
nom du projet.  Dans ce qui suit, PROJET doit être remplacé par le projet
écrit tout en majuscules.

Si Python peut importer `PAQUETAGE', où PAQUETAGE est la forme capitalisée
du nom de projet, et si `PAQUETAGE.__version__' existe, alors cette valeur
sera utilisée comme version du projet.  Dans ce qui suit, VERSION doit
être remplacé par la version du projet obtenue de cette manière.

Pour obtenir la configuration pour un projet donné, cette routine lit
FICHIER s'il est fourni.  Autrement, elle lit le fichier indiqué par
la variable d'environnement `PROJET_CONFIG'.  Cette variable fournit
soit le nom du fichier (une oblique doit alors en faire partie et
'./FICHIER' peut indiquer un fichier dans le répertoire courant),
soit un nom de SAVEUR duquel on dérive le véritable nom de fichier via
`/usr/local/etc/PROJET-SAVEUR.conf'.  Si cette variable n'existe pas, alors
la configuration est lue soit de `/usr/local/etc/PROJET-VERSION.conf'
(lorsque la VERSION est connue) soit de `/usr/local/etc/PROJET.conf',
essayés dans cet ordre.  Si pour toute raison le fichier de configuration
ne peut être déterminé ou lu, une configuration est néanmoins produite,
mais sans être initialisée.

Lors de la lecture initiale d'une configuration, si `PythonPath' existe
dans la section `DEFAULT', cette variable contiendra alors une liste de
répertoires séparés par des `:'.  Les répertoires existant parmi ceux-là
sont alors ajoutés au début de `sys.path', dans le même ordre.
"""
    import os
    if projet is None:
        projet = os.environ.get('CONFIG_PROJET')
    if projet is not None:
        config = _config_cache.get(projet)
        if config is not None:
            return config
    # Produire une nouvelle configuration.
    import ConfigParser, sys
    config = ConfigParser.ConfigParser()
    if fichier is None and projet is not None:
        saveur = os.environ.get('%s_CONFIG' % projet.upper())
        if not saveur:
            # REVOIR: À faire disparaître l'un de ces jours.
            saveur = os.environ.get('CONFIG_%s' % projet.upper())
            if saveur:
                # REVOIR: Richard exige et demande mille et une vertus,
                # mais juge majeur le changement de la pratiquer lui-même.
                if projet != 'psep':
                    raise Vieille_configuration, (
                            "* Utiliser `%s_CONFIG' dans l'environnement"
                            " plutôt que `CONFIG_%s'.\n"
                            % (projet.upper(), projet.upper()))
        if saveur:
            if '/' in saveur:
                fichier = saveur
            else:
                fichier = '%s/%s-%s.conf' % (configdir, projet, saveur)
        else:
            try:
                version = getattr(__import__(projet.capitalize()),
                                  '__version__')
            except (ImportError, AttributeError):
                pass
            else:
                fichier = '%s/%s-%s.conf' % (configdir, projet, version)
                if not os.path.isfile(fichier):
                    fichier = None
        if fichier is None:
            fichier = '%s/%s.conf' % (configdir, projet)
        if not os.path.exists(fichier):
            raise Configuration_absente, (
                    "Le fichier de configuration `%s' n'existe pas" % fichier)
            fichier = None
    if fichier is not None:
        config.read(fichier)
    # Traiter PythonPath automatiquement, s'il est défini.
    try:
        chaine = config.get('DEFAULT', 'PythonPath')
    except ConfigParser.NoOptionError:
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
    if projet is not None:
        _config_cache[projet] = config
    return config

def permission(projet, permission):
    import os
    usager = os.environ['REMOTE_USER']
    from Authent import authent
    try:
        authent.Autorise(usager, projet, permission)
        return True
    except authent.PermissionRefusee:
        return False

### Interfaces Quid.

def connection_echo(propre_pour_nul=True):
    conf = config('écho')
    from Local import quid
    return quid.connection('am', propre_pour_nul=propre_pour_nul,
                           host=conf.get('ECHO', 'host'),
                           port=conf.get('ECHO', 'port'))

def connection_sigdec():
    conf = config('écho')
    from Local import quid
    return quid.connection('sigdec', dir=conf.get('SIGDEC', 'Directory'))
