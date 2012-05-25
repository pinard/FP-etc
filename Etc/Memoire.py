#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, décembre 2002.

"""\
Outils divers pour explorer l'utilisation dynamique des ressources par
un programme.  Une attention particulière est donnée aux problèmes de
déperdition de mémoire, puisque c'est le besoin à l'origine de ce module.
"""

__metaclass__ = type
import os, sys

## Examen de l'usage de la mémoire.

# Chaque appel à SURVEILLER_MÉMOIRE imprime sur l'erreur standard, en plus
# de l'ordinal de l'appel, le temps de calcul, la mémoire utilisée,
# le nombre de références à l'objet None, et s'il en existe, le nombre
# d'objets irrécupérables (miettes).  Puis, pour tous les appels sauf le
# tout premier, et séparément pour chacun des types, lorsque la quantité
# d'objets de ce type a changé depuis le dernier appel, la fonction imprime
# la grandeur du changement et la quantité résultante.

class Inventaire:

    # Moment, en secondes flottantes, du dernier affichage.
    moment = None
    # Objet de classe Graphique.
    graphique = None

    def __init__(self):
        self.references_par_classe = {}

    # La fonction qui suit doit être appelée à répétition durant
    # l'exécution d'un programme, typiquement une fois par exécution de sa
    # boucle principale.  Elle fournit simultanément plusieurs résultats
    # illustrant l'utilisation des ressources.

    # Si la variable d'environnement DISPLAY est définie et que le programme
    # Gnuplot existe le long du chemin de fouille, un graphique sera mis
    # à jour quant à la quantité de mémoire centrale occupée, et le
    # nombre d'objets Python que le programme utilise couramment.  Le double
    # graphique montre les 100 dernières valeurs accumulées.

    # Si TITRE ou WRITE est fourni, un rapport détaillé est fourni sur
    # le nombre d'objets Python qui ont été créés ou détruits depuis
    # l'appel précédent.  Après une ligne de titre, chaque ligne montre
    # le nombre d'objets avant le changement, un signe donnant le sens du
    # changement, et l'amplitude du changement pour la classe indiquée; les
    # lignes sont triées pour présenter d'abord la plus grande augmentation
    # et terminer par la plus grande diminution. Si TITRE n'est pas fourni,
    # une ligne de tirets est utilisée.  Si WRITE n'est pas fourni, le
    # rapport sera produit sur l'erreur standard.

    # Le nombre d'objets d'une classe donnée est estimé (en fait,
    # légèrement surestimé) par le nombre de références à cette classe.
    # Les classes, autant les traditionnelles que celles du nouveau style
    # (les types), sont trouvées dans l'espace global de tous les modules
    # couramment importés, et pas ailleurs.  Donc, les classes dont la portée
    # est imbriquée dans des fonctions ou d'autres classes sont ignorées.

    def surveiller(self, titre=None, write=None, force=False):
        import time
        moment = time.time()
        if force or self.moment is None or moment - self.moment > 1.:
            self.rapporter(titre, write)
            self.moment = moment

    def rapporter(self, titre=None, write=None):
        import types
        compteur_references = 0
        if titre is None and write is None:
            for module in sys.modules.values():
                if type(module) is types.ModuleType:
                    for nom, valeur in module.__dict__.items():
                        if type(valeur) in (type, type):
                            compteur_references += sys.getrefcount(valeur)
        else:
            avant = self.references_par_classe
            apres = self.references_par_classe = {}
            for module in sys.modules.values():
                if type(module) is types.ModuleType:
                    for nom, valeur in module.__dict__.items():
                        if type(valeur) in (type, type):
                            compteur = sys.getrefcount(valeur)
                            apres[module.__name__, nom] = compteur
                            compteur_references += compteur
            self.rapporter_differences(titre, write, avant, apres)
        if self.graphique is None:
            self.graphique = Graphique()
        self.graphique.avancer(compteur_references)

    def rapporter_differences(self, titre, write, avant, apres):
        if titre is None:
            titre = '-' * 79
        if write is None:
            write = sys.stderr.write
        write(titre + '\n')
        pertes = []
        for cle, auparavant in avant.items():
            if cle in apres:
                perte = auparavant - apres[cle]
                if perte != 0:
                    pertes.append((perte, cle, auparavant))
            else:
                pertes.append((auparavant, cle, auparavant))
        for cle, maintenant in apres.items():
            if cle not in avant:
                pertes.append((-maintenant, cle, 0))
        pertes.sort()
        for perte, (module, classe), auparavant in pertes:
            if perte < 0:
                write("%5d + %-5d références à %s.%s\n"
                      % (auparavant, -perte, module, classe))
            else:
                write("%5d - %-5d références à %s.%s\n"
                      % (auparavant, perte, module, classe))

    def essai(self):

        class Bulgroz: pass

        class Zorglub(object): pass

        def pause(): time.sleep(0.3)

        import time
        self.rapporter()
        pause()
        essai = Bulgroz(), Bulgroz(), Bulgroz()
        self.rapporter('Rapport 1')
        pause()
        zorglub = [Zorglub() for compteur in range(50)]
        self.rapporter('Rapport 2')
        pause()
        zorglub += list(essai)
        self.rapporter('Rapport 3')
        pause()
        zorglub = zorglub[:10]
        essai = None
        self.rapporter('Rapport 4')
        pause()

class Graphique:

    # Si l'échelle verticale doit être affichée logarithmiquement.
    echelle_logarithmique = False
    # Nombre de points horizontaux initialiement affichés.
    affichage_minimum = 20
    # Nombre de points horizontaux requis pour faire glisser l'affichage.
    affichage_maximum = 100

    # Lien vers le processus roulant Gnuplot, si possible.
    fichier = None
    # Compteur d'affichages.
    compteur = 0

    def __init__(self):
        if not os.environ.get('DISPLAY'):
            return
        for repertoire in os.environ['PATH'].split(':'):
            nom = repertoire + '/gnuplot'
            if os.access(nom, os.X_OK):
                break
        else:
            return
        self.references = Collection("Nombre références")
        self.statm = list(map(Collection, ("Mémoire totale (K)",
                                      "Mémoire résidente (K)",
                                      "Mémoire partagée (K)",
                                      "Mémoire pure (K)",
                                      "Mémoire impure (K)",
                                      "Mémoire bibliothèque (K)",
                                      "Mémoire modifiée (K)")))
        self.fichier = os.popen(
            # REVOIR: Comment faire ça tout en Python?
            'sh -c \'trap "" 1; %s -persist\'' % nom, 'w',
            'ISO-8859-1')
        write = self.fichier.write
        write('set data style lines\n'
              'set key right bottom\n')
        if self.echelle_logarithmique:
            write('set logscale y\n')

    def avancer(self, compteur_references):
        if self.fichier is not None:
            #if self.compteur == 511:
            #    # Gnuplot semble bloquer au 512ième graphique. :-(
            #    self.graphique.close()
            #    self.graphique = nouveau_gnuplot()
            #    if self.graphique is None:
            #        return
            #    self.compteur = 0
            compteur = 0
            for champ in file('/proc/self/statm').read().split():
                self.statm[compteur].append(int(champ))
                compteur += 1
            self.references.append(compteur_references)
            self.compteur += 1
            self.tracer_ensembles(self.statm, [self.references])
            self.fichier.flush()

    def tracer_ensembles(self, *ensembles):
        if len(ensembles) == 0:
            return
        if len(ensembles) == 1:
            self.tracer_collections(*ensembles[0])
            return
        write = self.fichier.write
        position = 1.0
        delta = 1.0 / len(ensembles)
        write('set multiplot\n')
        for ensemble in ensembles:
            position -= delta
            write('set size 1.0, %s\n' % formater_point(delta, '%f'))
            write('set origin 0.0, %s\n' % formater_point(position, '%f'))
            self.tracer_collections(*ensemble)
        write('set nomultiplot\n')

    def tracer_collections(self, *collections):
        if not collections:
            return
        # Déterminer les bornes communes.
        collection = collections[0]
        minx = collection.points_elimines
        maxx = max(self.affichage_minimum, minx + len(collection.array))
        miny = collection.minimum * 15 // 16
        maxy = collection.maximum * 17 // 16
        for collection in collections[1:]:
            minx = min(minx, collection.points_elimines)
            maxx = max(maxx, max(self.affichage_minimum,
                                 minx + len(collection.array)))
            miny = min(miny, collection.minimum * 15 // 16)
            maxy = max(maxy, collection.maximum * 17 // 16)
        if self.echelle_logarithmique:
            miny = max(1, miny)
        # Fabriquer la commande `plot'.
        write = self.fichier.write
        collection = collections[0]
        write('plot [%d:%d] [%d:%d] \'-\' title "%s"'
              % (minx, maxx, miny, maxy+100, collection.titre))
        for collection in collections[1:]:
            write(', \'-\' title "%s"' % collection.titre)
        write('\n')
        # Fournir toutes les données.
        for collection in collections:
            abcisse = collection.points_elimines
            for ordonnee in collection.array:
                if self.echelle_logarithmique:
                    ordonnee = max(1, ordonnee)
                write('%d %d\n' % (abcisse, ordonnee))
                abcisse += 1
            write('e\n')

class Collection:

    def __init__(self, titre=None, typecode='I'):
        self.titre = titre
        import array
        self.array = array.array(str(typecode))
        self.points_elimines = 0

    def append(self, valeur):
        if len(self.array) == 0:
            self.minimum = self.maximum = valeur
        else:
            self.minimum = min(self.minimum, valeur)
            self.maximum = max(self.maximum, valeur)
            if len(self.array) == Graphique.affichage_maximum:
                self.array.pop(0)
                self.points_elimines += 1
        self.array.append(valeur)

class Inventaire_Vieux:
    ordinal = 0
    compteurs = {}
    temps = 0.
    memoire = 0.

    def surveiller(self):
        write = sys.stderr.write
        write('\n' + '\\' * 59 + '\n')
        self.ordinal += 1
        write("nº%d  " % self.ordinal)
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        temps = usage.ru_utime + usage.ru_stime
        write("   %+.3f -> %.1f sec" % (temps - self.temps, temps))
        self.temps = temps
        # REVOIR: Les ressources de mémoire sont toujours indiquée à
        # zéro par getrusage(), alors je place le code en commentaire pour
        # le moment.
        #memoire = (usage.ru_ixrss + usage.ru_idrss + usage.ru_isrss) * 1e-6
        #write(u"   %+.1f -> %.1f Mo" % (memoire - self.memoire, memoire))
        #self.memoire = memoire
        write("   %d Nones" % sys.getrefcount(None))
        import gc
        gc.collect()
        if gc.garbage:
            write("   %d miettes" % len(gc.garbage))
        write('\n')
        compteurs = {}
        for objet in gc.get_objects():
            nom = type(objet).__name__
            if nom not in compteurs:
                compteurs[nom] = 0
            compteurs[nom] += 1
        if self.compteurs:
            for nom, compteur in sorted(compteurs.items()):
                if nom in self.compteurs:
                    delta = compteur - self.compteurs[nom]
                    del self.compteurs[nom]
                else:
                    delta = compteur
                if delta:
                    write("  %+7d -> %-7d   %s\n" % (delta, compteur, nom))
            for nom, compteur in sorted(self.compteurs.items()):
                write("  %+7d -> %-7d   %s\n" % (-compteur, 0, nom))
        self.compteurs = compteurs
        write('/' * 59 + '\n')

def formater_point(valeur, format):
    return (format % valeur).replace(',', '.')

def main(*arguments):
    Inventaire().essai()

if __name__ == '__main__':
    main(*sys.argv[1:])
