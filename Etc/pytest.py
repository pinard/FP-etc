#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2005 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2005.

u"""\
Exécution d'une suite de validation du style de py.test (du projet pylib).

Usage: pytest [OPTION]... [CHEMIN]...

Options:
  -h   Imprimer cette aide et ne rien faire d'autre.
  -v   Produire une ligne par test, plutôt qu'un point par test.
  -n   Ne pas capturer ni la sortie ni l'erreur standard.
  -p   Profiler la suite de validation (utilise "lsprof").

  -s FICHIER    Sauver les ordinaux des tests échoués, un par ligne.
  -o ORDINAUX   Ne conserver que les tests avec ces ordinaux d'exécution.
  -k GABARIT    N'exécuter que les tests dont le nom est apparié par GABARIT.
  -x GABARIT    Exclure les tests dont le nom est apparié par GABARIT.
  -l LIMITE     Arrêter la suite de valdiation après LIMITE erreurs.

Si -l n'est pas utilisé, il y aura arrêt après 10 erreurs.  ORDINAUX
est une suite d'entiers séparés par des virgules.

Les options -k, -o et -x peuvent être répétées.  S'il y a au moins
une option -k, un test n'est retenu que s'il s'apparie à au moins l'une
des valeurs de -k.  S'il y a au moins une option -o, un test n'est
retenu que si son ordinal fait au moins partie de l'une des valeurs de
-o.  Il ne sera pas retenu s'il s'apparie à l'une des vakeurs de -x.

Lorsque CHEMIN est un fichier, le nom doit s'apparier à "test_.*\.py".
Si c'est un répertoire, il est récursivement fouillé pour trouver des
fichiers qui s'apparient de même.  Si aucun CHEMIN n'est fourni, le
répertoire courant est alors utilisé.

La progression des tests apparaît sur l'erreur standard.  Puis ensuite,
si l'option -s n'est pas choisie, alors 1) le détail des tests échoués
est écrit sur la sortie standard et 2) le statut d'erreur est différent
de zéro si au moins un test a failli.
"""

# Il s'agit de la reconstitution d'un choix minimal des spécifications
# du py.test de Codespeak, mais dans un environnement Unicode.

__metaclass__ = type
from Etc.Unicode import apply, deunicode, file, open, os, reunicode, sys
import inspect, time, traceback
from StringIO import StringIO

# Nombre de caractères affichables par ligne.
COLONNES = 79

class Limite_Atteinte(Exception):
    pass

class Main:
    gabarit = []
    exclusion = []
    ordinaux = []
    volubile = False
    profile = False
    limite = 10
    capture = True
    sauve = None

    def main(self, *arguments):
        import getopt
        options, arguments = getopt.getopt(arguments, u'hk:l:no:ps:vx:')
        for option, valeur in options:
            if option == u'-h':
                sys.stdout.write(__doc__)
                return
            elif option == u'-k':
                self.gabarit.append(valeur)
            elif option == u'-l':
                self.limite = int(valeur)
            elif option == u'-n':
                self.capture = False
            elif option == u'-o':
                self.ordinaux += [
                    int(texte) for texte in valeur.replace(u',', u' ').split()]
            elif option == u'-p':
                self.profile = True
            elif option == u'-s':
                self.sauve = valeur
            elif option == u'-v':
                self.volubile = True
            elif option == u'-x':
                self.exclusion.append(valeur)
        if not arguments:
            arguments = u'.',
        if self.gabarit:
            import re
            self.gabarit = re.compile(u'|'.join(self.gabarit))
        else:
            self.gabarit = None
        if self.exclusion:
            import re
            self.exclusion = re.compile(u'|'.join(self.exclusion))
        else:
            self.exclusion = None
        write = sys.stderr.write
        self.echecs = []
        self.compteur_total = 0
        self.compteur_sautes = 0
        temps_depart = time.time()
        if self.profile:
            try:
                import lsprof
            except ImportError:
                write(u"ATTENTION: profileur indisponible.\n")
                self.profileur = None
            else:
                self.profileur = lsprof.Profiler()
        else:
            self.profileur = None
        try:
            try:
                for argument in arguments:
                    for fichier in self.chaque_fichier(argument):
                        self.identificateur = fichier
                        self.colonne = 0
                        self.compteur = 0
                        repertoire, base = os.path.split(fichier)
                        sys.path.insert(0, repertoire)
                        try:
                            try:
                                module = __import__(base[:-3])
                            except ImportError:
                                if self.sauve:
                                    self.echecs.append(self.compteur_total + 1)
                                else:
                                    filature = StringIO()
                                    traceback.print_exc(file=filature)
                                    self.echecs.append(
                                        (self.compteur_total + 1, fichier,
                                         None, None,
                                         None, None,
                                         reunicode(filature.getvalue())))
                            else:
                                self.traiter_module(fichier, module)
                        finally:
                            del sys.path[0]
                        if self.compteur and not self.volubile:
                            texte = u'(%d)' % self.compteur
                            if self.colonne + 1 + len(texte) >= COLONNES:
                                write(u'\n%5d ' % self.compteur)
                            else:
                                texte = u' ' + texte
                            write(texte + u'\n')
            except KeyboardInterrupt:
                if not self.volubile:
                    write(u'\n')
                write(u'\n*** INTERRUPTION! ***\n')
            except Limite_Atteinte:
                if not self.volubile:
                    write(u'\n')
                if not self.sauve:
                    if len(self.echecs) == 1:
                        write(u'\n*** DÉJÀ UNE ERREUR! ***\n')
                    else:
                        write(u'\n*** DÉJÀ %d ERREURS! ***\n' % self.limite)
        finally:
            if self.profileur is not None:
                stats = lsprof.Stats(self.profileur.getstats())
                stats.sort(u'inlinetime')
                write(u'\n')
                stats.pprint(15)
            if self.echecs:
                if len(self.echecs) == 1:
                    texte = u"un test ÉCHOUÉ"
                else:
                    texte = u"%d tests ÉCHOUÉS" % len(self.echecs)
                premier = False
            else:
                texte = u''
                premier = True
            reussis = (self.compteur_total - self.compteur_sautes
                       - len(self.echecs))
            if reussis:
                if premier:
                    if reussis == 1:
                        texte += u"un test réussi"
                    else:
                        texte += u"%d tests réussis" % reussis
                    premier = False
                else:
                    if reussis == 1:
                        texte += u", un réussi"
                    else:
                        texte += u", %d réussis" % reussis
            if self.compteur_sautes:
                if premier:
                    if self.compteur_sautes == 1:
                        texte += u"un test sauté"
                    else:
                        texte += u"%d tests sautés" % self.compteur_sautes
                    premier = False
                else:
                    if self.compteur_sautes == 1:
                        texte += u", un sauté"
                    else:
                        texte += u", %d sautés" % self.compteur_sautes
            if premier:
                texte = u"Aucun test"
            en_bref = (u"\nEn bref: %s; en %.2f secondes.\n"
                       % (texte, time.time() - temps_depart))
            write(en_bref)
        if self.sauve:
            write = file(self.sauve, u'w').write
            for ordinal in self.echecs:
                write(u'%d\n' % ordinal)
        else:
            write = sys.stdout.write
            for (ordinal, prefixe, fonction, arguments, stdout, stderr,
                 filature) in self.echecs:
                write(u'\n' + u'=' * COLONNES + u'\n')
                write(u'%d. %s\n' % (ordinal, prefixe))
                if fonction and fonction.__name__ != os.path.basename(prefixe):
                    write(u"    Fonction %s\n" % fonction.__name__)
                if arguments:
                    for compteur, argument in enumerate(arguments):
                        write(u"    Arg %d = %r\n" % (compteur + 1, argument))
                for tampon, titre in ((stdout, u'STDOUT'), (stderr, u'STDERR')):
                    if tampon:
                        write(u'\n' + titre + u' >>>\n')
                        write(tampon)
                        if not tampon.endswith(u'\n'):
                            write(u'\n')
                write(u'-' * COLONNES + u'\n')
                write(filature)
            if self.echecs:
                write(en_bref)
                sys.exit(1)

    def chaque_fichier(self, chemin):
        if os.path.isdir(chemin):
            pile = [chemin]
            while pile:
                repertoire = pile.pop(0)
                for base in sorted(os.listdir(repertoire)):
                    fichier = os.path.join(repertoire, base)
                    if base.startswith(u'test_') and base.endswith(u'.py'):
                        yield fichier
                    elif os.path.isdir(fichier):
                        pile.append(fichier)
        else:
            repertoire, base = os.path.split(chemin)
            if base.startswith(u'test_') and base.endswith(u'.py'):
                yield chemin

    def traiter_module(self, prefixe, module):
        collection = []
        for nom, objet in inspect.getmembers(module):
            if nom.startswith(u'Test') and inspect.isclass(objet):
                if getattr(object, u'disabled', False):
                    continue
                minimum = None
                for _, methode in inspect.getmembers(objet, inspect.ismethod):
                    numero = methode.im_func.func_code.co_firstlineno
                    if minimum is None or numero < minimum:
                        minimum = numero
                if minimum is not None:
                    collection.append((minimum, nom, objet, False))
            elif nom.startswith(u'test_') and inspect.isfunction(objet):
                code = objet.func_code
                collection.append((code.co_firstlineno, nom, objet,
                                   bool(code.co_flags & 32)))
        if not collection:
            return
        if hasattr(module, u'setup_module'):
            module.setup_module(module)
        for _, nom, objet, generateur in sorted(collection):
            if inspect.isclass(objet):
                if not getattr(object, u'disabled', False):
                    self.traiter_classe(prefixe + u'/' + nom, objet)
            else:
                self.traiter_fonction(prefixe + u'/' + nom, objet,
                                      generateur, None)
        if hasattr(module, u'teardown_module'):
            module.teardown_module(module)

    def traiter_classe(self, prefixe, classe):
        collection = []
        for nom, methode in inspect.getmembers(classe, inspect.ismethod):
            if nom.startswith(u'test_'):
                code = methode.im_func.func_code
                collection.append((code.co_firstlineno, nom, methode,
                                   bool(code.co_flags & 32)))
        if not collection:
            return
        instance = classe()
        if hasattr(instance, u'setup_class'):
            instance.setup_class(classe)
        for _, nom, methode, generateur in sorted(collection):
            self.traiter_fonction(prefixe + u'/' + nom, getattr(instance, nom),
                                  generateur, instance)
        if hasattr(instance, u'teardown_class'):
            instance.teardown_class(classe)

    def traiter_fonction(self, prefixe, fonction, generateur, instance):
        if generateur:
            for compteur, arguments in enumerate(fonction()):
                self.lancer_test(prefixe + u'/' + unicode(compteur + 1),
                                 arguments[0], arguments[1:], instance)
        else:
            self.lancer_test(prefixe, fonction, (), instance)

    def lancer_test(self, prefixe, fonction, arguments, instance):
        # Déterminer si l'on doit retenir ce test.
        if (self.exclusion is not None and self.exclusion.search(prefixe)
              or self.gabarit is not None and not self.gabarit.search(prefixe)
              or self.ordinaux and self.compteur_total+1 not in self.ordinaux):
            self.noter_progression(prefixe, None)
            return
        # Le test doit définitivement être exécuté.
        if instance is not None and hasattr(instance, u'setup_method'):
            instance.setup_method(fonction)
        if self.capture:
            sauve_stdout = sys.stdout
            sauve_stderr = sys.stderr
            stdout = sys.stdout = StringIO()
            stderr = sys.stderr = StringIO()
        self.activer_profilage()
        try:
            try:
                apply(fonction, arguments)
            except KeyboardInterrupt, exception:
                raise
            except Exception, exception:
                pass
            else:
                exception = None
        finally:
            self.desactiver_profilage()
            if self.capture:
                sys.stdout = sauve_stdout
                sys.stderr = sauve_stderr
                stdout = stdout.getvalue()
                stderr = stderr.getvalue()
            else:
                stdout = None
                stderr = None
            if exception is None:
                self.noter_progression(prefixe, True)
            else:
                self.noter_progression(prefixe, False)
                if self.sauve:
                    self.echecs.append(self.compteur_total)
                else:
                    filature = StringIO()
                    traceback.print_exc(file=filature)
                    self.echecs.append(
                        (self.compteur_total, prefixe, fonction, arguments,
                         stdout, stderr, reunicode(filature.getvalue())))
            if instance is not None and hasattr(instance, u'teardown_method'):
                instance.teardown_method(fonction)
        if exception is not None and len(self.echecs) == self.limite:
            raise Limite_Atteinte

    def noter_progression(self, prefixe, succes):
        self.compteur_total += 1
        if succes is None:
            self.compteur_sautes += 1
        else:
            write = sys.stderr.write
            if self.volubile:
                write(u'%5d. [%s] %s\n' % (self.compteur_total, prefixe,
                                           (u'ERREUR', u'ok')[succes]))
            else:
                if self.colonne == COLONNES:
                    write(u'\n')
                    self.colonne = 0
                if not self.colonne:
                    if self.compteur:
                        texte = u'%5d ' % (self.compteur + 1)
                    else:
                        texte = self.identificateur + u' '
                    write(texte)
                    self.colonne = len(texte)
                write(u'E·'[succes])
                self.colonne += 1
                self.compteur += 1

    def activer_profilage(self):
        if self.profileur is not None:
            self.profileur.enable(subcalls=True, builtins=True)

    def desactiver_profilage(self):
        if self.profileur is not None:
            self.profileur.disable()

run = Main()
main = run.main

class ExceptionAttendue(Exception):
    pass

def raises(attendue, *args, **kws):
    try:
        if isinstance(args[0], unicode) and not kws:
            eval(args[0])
        else:
            apply(args[0], args[1:], kws)
    except attendue:
        return
    else:
        raise ExceptionAttendue(u"L'exception n'a pas eu lieu.")

if __name__ == u'__main__':
    main(*sys.argv[1:])
