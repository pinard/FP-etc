#!/usr/bin/env python3
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003-06.

"""\
Ce module regroupe quelques déclarations utiles.
"""

def garantir_repertoire(nom):
    import os
    base = os.path.dirname(nom)
    if base and not os.path.isdir(base):
        # REVOIR: Plante s'il existe déjà un fichier à ce nom.
        garantir_repertoire(base)
        os.mkdir(base)

## Profilage de l'exécution

class Chronometre:
    # Chaque instance de chronomètre imprime la durée de son existence.
    # Par exemple, "chronometre = Chronometre()" mesure l'intervalle
    # de temps entre cet énoncé et la fin de la fonction qui l'exécute,
    # ou encore, le moment où la variable "chronometre" est affectée de
    # nouveau (généralement par une nouvelle instance de Chronometre.

    def __init__(self, titre=None):
        self.titre = titre
        from time import time
        self.depart = time()

    def __del__(self):
        from time import time
        delta = time() - self.depart
        if self.titre:
            info.chrono("%s : %.1f secondes." % (self.titre, delta))
        else:
            info.chrono("%.1f secondes." % delta)

class Profilage:
    deja = False
    profileur = None
    Stats = None

    def activer(self, effacer=False):
        if not self.deja:
            try:
                import lsprof
            except ImportError:
                pass
            else:
                self.profileur = lsprof.Profiler()
                self.Stats = lsprof.Stats
            self.deja = True
        if self.profileur is not None:
            if effacer:
                self.profileur.clear()
            self.profileur.enable(subcalls=False, builtins=True)

    def desactiver(self):
        if self.profileur is not None:
            self.profileur.disable()

    def rapport(self):
        if self.profileur is None:
            return "\n   Pas de rapport: le profilage n'a pas eu lieu.\n"
        stats = self.Stats(self.profileur.getstats())
        stats.sort('inlinetime')
        from io import StringIO
        tampon = StringIO()
        tampon.write('\n')
        stats.pprint(20, tampon)
        return tampon.getvalue()

profilage = Profilage()
