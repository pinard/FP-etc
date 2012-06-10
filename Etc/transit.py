#!/usr/bin/python3
# Copyright © 2001, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Transmission de structures Python sur le réseau.
"""

import marshal
import struct
#import sys

format_prefixe = '!I'
grandeur_fragment = 30000

Erreur = 'Erreur'


def envoyer(socket, structure):
    #sys.stderr.write('Envoyer!\n')
    chaine = marshal.dumps(structure)
    reponse = struct.pack(format_prefixe, len(chaine)) + chaine
    while reponse:
        transmis = socket.send(reponse)
        #sys.stderr.write('Envoi %d de %d\n' % (transmis, len(reponse)))
        if not transmis:
            raise Erreur("Connection rompue (vu par l'envoyeur).")
        reponse = reponse[transmis:]


def recevoir(socket):
    #sys.stderr.write('Recevoir!\n')
    attendu = struct.calcsize(format_prefixe)
    chaine = ''
    while len(chaine) < attendu:
        fragment = socket.recv(grandeur_fragment)
        #sys.stderr.write('Réception %d de %d\n' % (len(fragment), attendu))
        if not fragment:
            raise Erreur("Connection rompue (vu par le récipiendaire).")
        chaine += fragment
    valeurs = struct.unpack(format_prefixe, chaine[:attendu])
    chaine = chaine[attendu:]
    attendu = valeurs[0]
    while len(chaine) < attendu:
        fragment = socket.recv(grandeur_fragment)
        #sys.stderr.write('Réception %d de %d\n' % (len(fragment), attendu))
        if not fragment:
            raise Erreur("Connection rompue (vu par le récipiendaire).")
        chaine += fragment
    return marshal.loads(chaine)
