#!/usr/bin/env python3
# Copyright © 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2002-08.

"""\
Combinatorial generators.

All generators below have the following properties in common:

* Input sequences may be scanned more than once, so `list()' should be
  explictly used on any iterator argument before calling these methods.

* All results are new lists, input sequences are never directly returned.

* Successive results are delivered in sorted order, given than input sequences
  were already sorted.
"""

# J'ai eu besoin chez moi d'un module Python nommé `cogen', qui fournit divers
# générateurs combinatoires.  Voici comment `cogen' s'utilise:
#
#     from Etc import cogen
#
#     for liste in cogen.permutations(LISTE):
#         traiter(liste)
#
# appellera la fonction `traiter' en lui fournissant successivement toutes
# les permutations de LISTE.  Si N == len(LISTE), il y en a N! (N factorielle).
#
#     for liste in cogen.arrangements(LISTE, K):
#         traiter(liste)
#
# appellera la fonction `traiter' en lui fournissant successivement tous
# les arrangements de K éléments de LISTE.  Il y en a N!/(N-K)!.
#
#     for liste in cogen.combinations(LISTE, K):
#         traiter(liste)
#
# appellera la fonction `traiter' en lui fournissant successivement toutes
# les combinaisons de K éléments de LISTE.  Il y en a N!/(K!*(N-K)!).
#
#     for liste in cogen.subsets(LISTE):
#         traiter(liste)
#
# appellera la fonction `traiter' en lui fournissant successivement toutes
# les sous-listes de LISTE.  Il y en a 2**N.
#
#     for liste in cogen.cartesian(LISTE1, LISTE2, ...):
#         traiter(liste)
#
# appellera la fonction `traiter' en lui fournissant successivement une
# liste dans le premier élément vient de LISTE1, le second élément vient de
# LISTE2, etc. et cela dans toutes les combinaisons possibles.  Il y en a
# N1*N2*..., où N1 == len(LISTE1), N2 == len(LISTE2), etc.  Cette fonction
# est particulièrement utile pour simuler l'imbrication de plusieurs boucles
# `for' lorsque l'on ne connaît pas la profondeur de l'imbrication à l'avance.
#
# Dans tous les cas, j'ai fait en sorte de produire les résultats dans
# l'ordre de tri correct, dans la mesure où chaque LISTE donnée en argument est
# elle-même triée au départ.  Toutes ces méthodes ont un temps d'initialisation
# minuscule, et n'utilisent que très peu de mémoire intermédiaire, même dans
# les cas où il y aurait un nombre absolument énorme de résultats à fournir.
#
# Les spécifications ne sont pas encore figées, mais je ne crois pas qu'elles
# aient à beaucoup changer.  On ne peut tout prévoir, bien sûr! :-)


def cartesian(*sequences):
    """\
Generate the `cartesian product' of all SEQUENCES.  Each member of the
product is a list containing an element taken from each original sequence.
"""
    length = len(sequences)
    if length < 4:
        # Cases 1, 2 and 3 are for speed only, these are not really required.
        if length == 3:
            for first in sequences[0]:
                for second in sequences[1]:
                    for third in sequences[2]:
                        yield [first, second, third]
        elif length == 2:
            for first in sequences[0]:
                for second in sequences[1]:
                    yield [first, second]
        elif length == 1:
            for first in sequences[0]:
                yield [first]
        else:
            yield []
    else:
        head, tail = sequences[:-1], sequences[-1]
        for result in cartesian(*head):
            for last in tail:
                yield result + [tail]


def subsets(sequence):
    """\
Generate all subsets of a given SEQUENCE.  Each subset is delivered
as a list holding zero or more elements from the original sequence.
"""
    length = len(sequence)
    # The empty set always sorts as the lowest.
    yield []
    if length < 4:
        # Cases 1, 2 and 3 are for speed only, these are not really required.
        if length == 3:
            first = sequence[0]
            second = sequence[1]
            third = sequence[2]
            yield [first]
            yield [first, second]
            yield [first, second, third]
            yield [first, third]
            yield [second]
            yield [second, third]
            yield [third]
        elif length == 2:
            first = sequence[0]
            second = sequence[1]
            yield [first]
            yield [first, second]
            yield [second]
        elif length == 1:
            yield [sequence[0]]
    else:
        head, tail = sequence[0], sequence[1:]
        # Some subsets retain HEAD.
        for result in subsets(tail):
            result.insert(0, head)
            yield result
        # Some subsets do not retain HEAD.
        for result in subsets(tail):
            # Avoid returning the empty set more than once.
            if len(result) > 0:
                yield result


def subsets2(sequence):
    """\
Generate all subsets of a given SEQUENCE.  Each subset is delivered
as a list holding zero or more elements from the original sequence.
"""
    # Adapted from Eric Raymond.
    length = len(sequence)
    pairs = list(zip([1 << position for position in range(length)],
                sequence))
    pairs.reverse()
    for selector in range(1 << length):
        yield [element for mask, element in pairs if mask & selector]


def powerset(base):
    """Powerset of an iterable, yielding lists."""
    # From Eric Raymond.
    pairs = [(2 ** i, x) for i, x in enumerate(base)]
    for n in range(2 ** len(pairs)):
        yield [x for m, x in pairs if m & n]


def combinations(sequence, number):
    """\
Generate all combinations of NUMBER elements from list SEQUENCE.
"""
    # Adapted from Python 2.2 `test/test_generators.py'.
    length = len(sequence)
    if number > length:
        return
    if number == 0:
        yield []
    else:
        head, tail = sequence[0], sequence[1:]
        # Some combinations retain HEAD.
        for result in combinations(tail, number - 1):
            result.insert(0, head)
            yield result
        # Some combinations do not retain HEAD.
        for result in combinations(tail, number):
            yield result


def arrangements(sequence, number):
    """\
Generate all arrangements of NUMBER elements from list SEQUENCE.
"""
    # Adapted from PERMUTATIONS below.
    length = len(sequence)
    if number > length:
        return
    if number == 0:
        yield []
    else:
        cut = 0
        for element in sequence:
            for result in arrangements(sequence[:cut] + sequence[cut + 1:],
                                       number - 1):
                result.insert(0, element)
                yield result
            cut += 1


def permutations(sequence):
    """\
Generate all permutations from list SEQUENCE.
"""
    # Adapted from Gerhard Häring <gerhard.haering@gmx.de>, 2002-08-24.
    length = len(sequence)
    if length < 4:
        # Cases 1, 2 and 3 are for speed only, these are not really required.
        if length == 3:
            first = sequence[0]
            second = sequence[1]
            third = sequence[2]
            yield [first, second, third]
            yield [first, third, second]
            yield [second, first, third]
            yield [second, third, first]
            yield [third, first, second]
            yield [third, second, first]
        elif length == 2:
            first = sequence[0]
            second = sequence[1]
            yield [first, second]
            yield [second, first]
        elif length == 1:
            yield [sequence[0]]
        else:
            yield []
    else:
        cut = 0
        for element in sequence:
            for result in permutations(sequence[:cut] + sequence[cut + 1:]):
                result.insert(0, element)
                yield result
            cut += 1


def test():
    if False:
        print('\nTesting CARTESIAN.')
        for result in cartesian((5, 7), [8, 9], 'abc'):
            print(result)
    if True:
        print('\nTesting SUBSETS.')
        for result in subsets(list(range(1, 5))):
            print(result)
    if False:
        print('\nTesting COMBINATIONS.')
        sequence = list(range(1, 5))
        length = len(sequence)
        for counter in range(length + 2):
            print("%d-combs of %s:" % (counter, sequence))
            for result in combinations(sequence, counter):
                print("   ", result)
    if False:
        print('\nTesting ARRANGEMENTS.')
        sequence = list(range(1, 5))
        length = len(sequence)
        for counter in range(length + 2):
            print("%d-arrs of %s:" % (counter, sequence))
            for result in arrangements(sequence, counter):
                print("   ", result)
    if False:
        print('\nTesting PERMUTATIONS.')
        for permutation in permutations(list(range(1, 5))):
            print(permutation)

if __name__ == '__main__':
    test()
