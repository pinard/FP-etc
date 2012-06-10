#!/usr/bin/env python3
# Copyright © 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2002-01.

"""\
Quelques petites fonctions de nature arithmétique.
"""


def is_prime(n):
    """\
Return True if integer N is prime.
"""
    if n < 11:
        return n in (2, 3, 5, 7)
    if n % 2 == 0:
        return False
    d = 3
    dd = 9
    while dd <= n:
        if n % d == 0:
            return False
        d += 1
        dd += 4 * d
        d += 1
    return True


def gcd(u, v):
    """\
Return greatest common divisor of integers U and V.
"""
    while v:
        u, v = v, u % v
    return u


def gcd_extended(u, v):
    """\
Return integer U1, U2, U3 such that U*U1 + V*U2 == U3 == gcd(U, V).
Algorithm X from Knuth vol. 2 for extended GCD, coded by Tim Peters.
"""
    u1, u2, u3 = 1, 0, u
    v1, v2, v3 = 0, 1, v
    while v3:
        q = u3 // v3
        t = u1 - v1 * q, u2 - v2 * q, u3 - v3 * q
        u1, u2, u3 = v1, v2, v3
        v1, v2, v3 = t
    # The next two lines by Tim for extending the algorithm to all ints,
    # as algorithm X Assumes U and V are non-negative.
    if u3 < 0:
        u1, u2, u3 = -u1, -u2, -u3
    assert u * u1 + v * u2 == u3
    return u1, u2, u3
