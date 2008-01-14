#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Routines et outils de services pour le reste de Conf.
"""

import os, sys

class Tache:
    options_courtes = ''
    options_longues = []
    mise_au_point = 0
    galop_essai = False
    aide = False
    volubile = True
    serveur = None
    chemin_fouille = None

    #def __del__(self):
    #    if self.serveur is not None:
    #        self.serveur.close()

    def getopt(self, arguments):
        machine = None
        autres_options = []
        import getopt
        options, arguments = getopt.getopt(
            arguments, self.options_courtes + 'dh:nqv',
            self.options_longues + ['debug', 'dry-run', 'help', 'machine',
                                    'quiet', 'volubile'])
        for option, value in options:
            if option in ('--debug', '-d'):
                self.mise_au_point += 1
            elif option in ('--dry-run', '-n'):
                self.galop_essai = self.volubile = True
            elif option == '--help':
                sys.stdout.write(__doc__)
                self.aide = True
            elif option in ('--machine', '-h'):
                machine = value
            elif option in ('--quiet', '-q'):
                self.volubile = False
            elif option in ('--volubile', '-v'):
                self.volubile = True
            else:
                autres_options.append((option, value))
        if (machine is not None
                and os.popen('uname -n 2>/dev/null').read()[:-1] == machine):
            machine = None
        from Etc import remote
        serveur = remote.Server(machine, trace=self.mise_au_point)
        serveur.execute(remote_prolog)
        self.serveur = serveur
        return autres_options, arguments

    #try:
    #    process(self, *arguments)
    #except remote.error, traceback:
    #    self.write(repr(traceback))
    #    raise

    ## Services divers.

    def write(self, texte):
        # Atomic write, may be overridden.
        sys.stdout.write(texte)

    ## Consultation distante.

    def __getattr__(self, variable):
        # `machine', `site' - identification de l'appareil.
        # `usager', `maison' - usager exécutant.
        # `osname', `oslevel', `umachine', `nodename' - via `uname'.
        # `release' - identification de la distribution.
        if variable in ('site', 'machine'):
            self.machine = self.nodename.split('.')[0].lower()
            self.site = 'bpi'
        elif variable in ('usager', 'maison'):
            champs = self.serveur.eval('list(pwd.getpwuid(os.geteuid()))')
            self.usager = champs[0]
            self.maison = champs[5]
        elif variable == 'osname':
            self.osname = self.serveur.eval(
                'os.popen(\'uname -s 2>/dev/null\').read()[:-1]')
        elif variable == 'oslevel':
            self.oslevel = self.serveur.eval(
                'os.popen(\'uname -r 2>/dev/null\').read()[:-1]')
        elif variable == 'umachine':
            self.umachine = self.serveur.eval(
                'os.popen(\'uname -m 2>/dev/null\').read()[:-1]')
        elif variable == 'nodename':
            if self.osname == 'QNX':
                self.nodename = self.serveur.eval(
                    'os.popen(\'/etc/hostname\').read()[:-1]')
            else:
                self.nodename = self.serveur.eval(
                    'os.popen(\'uname -n 2>/dev/null\').read()[:-1]')
        elif variable == 'release':
            if self.osname == 'QNX':
                self.release = 'QNX-?'
            else:
                texte = self.serveur.eval(
                    'file(\'/etc/SuSE-release\').read()[:-1]')
                self.release = 'SuSE-' + texte.split()[-1]
        else:
            raise AttributeError(variable)
        return getattr(self, variable)

    def access(self, nom, bits):
        return self.serveur.call('os.access', nom, bits)

    def environ(self, nom):
        return self.serveur.call('os.environ.get', nom)

    def exists(self, nom):
        return self.serveur.call('os.path.exists', nom)

    def expanduser(self, nom):
        return self.serveur.call('os.path.expanduser', nom)

    def forced_popen_read(self, commande, doublure=None):
        self._system(commande, doublure)
        return self.serveur.call('popen_read', commande)

    def forced_system(self, commande, doublure=None):
        self._system(commande, doublure)
        handle = Remote_Popen(self, commande)
        lignes = handle.readlines()
        statut = handle.close()
        if self.volubile and lignes:
            lignes.insert(0, '-' * 78 + '>\n')
            lignes.append('-' * 78 + '<\n')
            self.write(''.join(lignes))
        return statut

    def isdir(self, nom):
        return self.serveur.call('os.path.isdir', nom)

    def isfile(self, nom):
        return self.serveur.call('os.path.isfile', nom)

    def islink(self, nom):
        return self.serveur.call('os.path.islink', nom)

    def listdir(self, nom):
        self.doit_exister(nom)
        return self.serveur.call('os.listdir', nom)

    def read_file(self, nom):
        self.doit_exister(nom)
        return self.serveur.call('read_file', nom)

    def readlink(self, nom):
        return self.serveur.call('os.readlink', nom)

    def doit_exister(self, nom):
        if not self.exists(nom) and not self.islink(nom):
            raise IOError, "%s:%s: No such file.\n" % (self.machine, nom)

    def stat(self, nom):
        self.doit_exister(nom)
        return self.serveur.call('os.stat', nom)

    def trouver_programme(self, *programs):
        if self.chemin_fouille is None:
            self.chemin_fouille = self.environ('PATH').split(':')
        import os
        for program in programs:
            for repertoire in self.chemin_fouille:
                if repertoire:
                    nom = os.path.join(repertoire, program)
                    try:
                        if self.access(nom, os.X_OK):
                            return nom
                    except AttributeError:
                        if self.isfile(nom):
                            return nom

    def trouver_python_gtk(self):
        if self.chemin_fouille is None:
            self.chemin_fouille = self.environ('PATH').split(':')
        pythons = []
        for repertoire in self.chemin_fouille:
            if repertoire:
                for base in self.listdir(repertoire):
                    if base.startswith('python') and base != 'python':
                        try:
                            version = map(int, base[6:].split('.'))
                        except ValueError:
                            continue
                        pythons.append((version, repertoire))
        pythons.sort()
        pythons.reverse()
        for version, repertoire in pythons:
            python = '%s/python%s' % (repertoire, '.'.join(map(str, version)))
            if not self.system('%s -c \'import gtk\' 2>/dev/null' % python):
                return python

    ## Modification distante.

    def popen(self, commande, doublure=None):
        self._system(commande, doublure)
        if self.galop_essai:
            return file('/dev/null')
        return Remote_Popen(self, commande)

    def popen_read(self, commande, doublure=None):
        self._system(commande, doublure)
        if self.galop_essai:
            return ''
        return self.serveur.call('popen_read', commande)

    def system(self, commande, doublure=None):
        self._system(commande, doublure)
        if self.galop_essai:
            lignes = []
            statut = 0
        else:
            handle = Remote_Popen(self, commande)
            lignes = handle.readlines()
            statut = handle.close()
        if self.volubile and lignes:
            lignes.insert(0, '-' * 78 + '>\n')
            lignes.append('-' * 78 + '<\n')
            self.write(''.join(lignes))
        return statut

    def _system(self, commande, doublure):
        if doublure is None:
            doublure = commande
        if self.volubile:
            if doublure[-1] == '\n':
                self.write(doublure)
            else:
                self.write(doublure + '\n')

    def chmod(self, nom, nouveau_mode):
        from stat import ST_MODE
        ancien_mode = self.stat(nom)[ST_MODE] & 07777
        nouveau_mode &= 07777
        if nouveau_mode == ancien_mode:
            return
        if self.volubile:
            self.write('chmod %s: %.3o -> %.3o\n'
                       % (nom, ancien_mode, nouveau_mode))
        if not self.galop_essai:
            self.serveur.call('os.chmod', nom, nouveau_mode)

    def chown(self, nom, owner, group):
        info = self.stat(nom)
        from stat import ST_GID, ST_UID
        ancien_uid = info[ST_UID]
        ancien_gid = info[ST_GID]
        if owner is None:
            nouveau_uid = ancien_uid
        elif isinstance(owner, int):
            nouveau_uid = owner
        else:
            nouveau_uid = self.serveur.call('uid_from_owner', owner)
            if nouveau_uid is None:
                nouveau_uid = int(owner)
        if group is None:
            nouveau_gid = ancien_gid
        elif isinstance(group, int):
            nouveau_gid = group
        else:
            nouveau_gid = self.serveur.call('gid_from_group', group)
            if nouveau_gid is None:
                nouveau_gid = int(group)
        if nouveau_uid == ancien_uid and nouveau_gid == ancien_gid:
            return
        if self.volubile:
            self.write('chown %s: %d.%d -> %d.%d\n'
                       % (nom, ancien_uid, ancien_gid,
                          nouveau_uid, nouveau_gid))
        if not self.galop_essai:
            self.serveur.call('os.chown', nom, nouveau_uid, nouveau_gid)

    def mkdir(self, nom, mode, owner=None, group=None, parents=False):
        if parents:
            if self.isdir(nom):
                return
            repertoire, base = os.path.split(nom)
            self.mkdir(repertoire, mode, owner, group, True)
        if self.volubile:
            self.write('mkdir %s: %.3o\n' % (nom, mode))
        if not self.galop_essai:
            self.serveur.call('os.mkdir', nom, mode)
            if owner is not None or group is not None:
                self.chown(nom, owner, group)

    def rename(self, nom, nouveau_nom):
        self.doit_exister(nom)
        if self.volubile:
            self.write('mv %s %s\n' % (nom, nouveau_nom))
        if not self.galop_essai:
            self.serveur.call('os.rename', nom, nouveau_nom)

    def remove(self, nom):
        self.doit_exister(nom)
        if self.volubile:
            self.write('rm %s\n' % nom)
        if not self.galop_essai:
            self.serveur.call('os.remove', nom)

    def remplacer(self, nom, nouveau_texte,
                  owner=None, group=None, mode=None, binaire=False):
        """\
Si le nouveau contenu est identique à l'ancien, ne rien faire et retourner
False.  Autrement, faire le remplacement et retourner True.
"""
        # Étudier la copie pré-existante du fichier.
        try:
            ancien_texte = self.read_file(nom)
        except IOError:
            ancien_texte = None
        if nouveau_texte == ancien_texte:
            return False
        if ancien_texte is None:
            info = None
        else:
            info = self.stat(nom)
            from stat import ST_MODE
            ancien_mode = info[ST_MODE] & 07777
            if ancien_mode & 0600 != 0600:
                self.chmod(nom, ancien_mode | 0600)
        if self.volubile:
            self._remplacer(nom, info, ancien_texte, nouveau_texte, binaire)
        # Créer un répertoire, au besoin, pour un nouveau fichier.
        if ancien_texte is None:
            repertoire, base = os.path.split(nom)
            if repertoire:
                self.mkdir(repertoire, 0755, parents=True,
                           owner=owner, group=group)
        # Pour le super-usager, archiver l'ancien contenu cumulativement dans
        # RCS.  Utiliser un fichier vide si le fichier ne pré-existait pas.
        if self.usager == 'root':
            if ancien_texte is None:
                if self.volubile:
                    self.write('touch %s\n' % nom)
                if not self.galop_essai:
                    self.write_file(nom, '')
                    self.chmod(nom, 0600)
            repertoire, base = os.path.split(nom)
            if not self.isdir('%s/RCS' % repertoire):
                self.mkdir('%s/RCS' % repertoire, 0700)
            self.system('ci -t- -l %s </dev/null 2>&1' % nom)
        # Produire un fichier avec son nouveau contenu.
        if not self.galop_essai:
            nouveau_nom = nom + '+'
            self.write_file(nouveau_nom, nouveau_texte)
            if owner is not None or group is not None:
                self.chown(nouveau_nom, owner, group)
            if mode is not None:
                self.chmod(nouveau_nom, mode)
            # Pour un usager ordinaire, archiver l'ancien contenu avec un
            # suffixe `-'.  Écraser une telle archive si elle existait déjà.
            if ancien_texte is not None:
                if self.usager != 'root':
                    ancien_nom = nom + '-'
                    if self.exists(ancien_nom):
                        self.remove(ancien_nom)
                    self.rename(nom, ancien_nom)
                else:
                    self.remove(nom)
            # Mettre le nouveau contenu à sa place finale.
            self.rename(nouveau_nom, nom)
        return True

    def _remplacer(self, nom, info, ancien_texte, nouveau_texte, binaire):
        if ancien_texte is None:
            if binaire:
                self.write("# Mise-en-place du fichier binaire `%s'.\n" % nom)
                return
            self.write('cat > %s << ...\n' % nom)
            lignes = nouveau_texte.split('\n')
            if lignes and lignes[-1] == '':
                del lignes[-1]
            fragments = []
            write = fragments.append
            write('-' * 78 + '>\n')
            if len(lignes) > 8:
                write('\n'.join(lignes[:4]))
                write('\n')
                write('   .\n' * 3)
                write('\n'.join(lignes[-4:]))
                write('\n')
            else:
                write(nouveau_texte)
            write('-' * 78 + '<\n')
            self.write(''.join(fragments))
        else:
            if binaire:
                self.write("# Remplacement du fichier binaire `%s'.\n" % nom)
                return
            import tempfile
            ancien = tempfile.mktemp()
            nouveau = tempfile.mktemp()
            file(ancien, 'w').write(ancien_texte)
            file(nouveau, 'w').write(nouveau_texte)
            from stat import ST_ATIME, ST_MTIME
            os.utime(ancien, (info[ST_ATIME], info[ST_MTIME]))
            commande = ('diff -u -L \'%s\' -L \'%s+\' %s %s'
                        % (nom, nom, ancien, nouveau))
            texte = os.popen(commande).read()
            fragments = []
            write = fragments.append
            write('patch %s << ...\n' % nom)
            write('-' * 78 + '>\n')
            write(texte)
            write('-' * 78 + '<\n')
            self.write(''.join(fragments))
            os.remove(ancien)
            os.remove(nouveau)

    def symlink(self, value, nom):
        if self.islink(nom):
            ancien_value = self.readlink(nom)
            if ancien_value == value:
                return
            if self.volubile:
                self.write("# Le lien valait `%s'\n" % ancien_value)
            self.remove(nom)
        elif not self.galop_essai:
            assert not self.exists(nom), "* Le fichier `%s' existe\n" % nom
        if self.volubile:
            self.write('ln -s %s %s\n' % (value, nom))
        if not self.galop_essai:
            self.serveur.call('os.symlink', value, nom)

    def write_file(self, nom, contents):
        if not self.galop_essai:
            self.serveur.call('write_file', nom, contents)

class Remote_Popen:
    global_popen_count = 0

    def __init__(self, tache, commande):
        self.global_popen_count += 1
        self.serveur = tache.serveur
        self.indice_fichier = self.global_popen_count
        self.serveur.call('popen_open', self.indice_fichier, commande)

    def __del__(self):
        if self.indice_fichier is not None:
            self.close()

    def __iter__(self):
        return self

    def close(self):
        statut = self.serveur.call('popen_close', self.indice_fichier)
        self.indice_fichier = None
        return statut

    def next(self):
        ligne = self.readline()
        if ligne:
            return ligne
        raise StopIteration

    def readline(self):
        return self.serveur.call('popen_readline', self.indice_fichier)

    def readlines(self):
        return self.serveur.call('popen_readlines', self.indice_fichier)

remote_prolog = '''\
import os, pwd, sys

global fichier_selon_index
fichier_selon_index = {}

def read_file(nom):
    try:
        file
    except NameError:
        file = open
    return file(nom).read()

def write_file(nom, contents):
    try:
        file
    except NameError:
        file = open
    file(nom, 'w').write(contents)

def popen_read(commande):
    import os
    return os.popen(commande).read()

def popen_open(indice, commande):
    fichier_selon_index[indice] = os.popen(commande)

def popen_close(indice):
    statut = fichier_selon_index[indice].close()
    del fichier_selon_index[indice]
    return statut

def popen_readline(indice):
    return fichier_selon_index[indice].readline()

def popen_readlines(indice):
    return fichier_selon_index[indice].readlines()

def gid_from_group(nom):
    import grp
    try:
        gid = grp.getgrnam(nom)[2]
    except KeyError:
        gid = None
    return gid

def uid_from_owner(nom):
    import pwd
    try:
        uid = pwd.getpwnam(nom)[2]
    except KeyError:
        uid = None
    return uid

def compile_file(nom):
    import py_compile
    py_compile.compile(nom)
'''
