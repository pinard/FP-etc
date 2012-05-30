#!/usr/bin/env python3
# Copyright © 1999, 2000, 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 1999.

"""\
A graph is made from a set of vertices, and a set of oriented arcs.

Each vertex should be immutable and not None.  An oriented arc is an instance of an Arc,  as below.
"""

def path(before, after, arcs):
    """\
Return the most economical path from the BEFORE vertex to the AFTER vertex,
given a set of ARCS representing possible partial paths.  The path is
returned as a list of successive arcs connecting BEFORE to AFTER, or None
is there is no such path.
"""

    class Vertex(tuple):

        best_forward = property(make_getter(0))
        total_weight = property(make_getter(1))

        def __new__(cls, best_forward, total_weight):
            return tuple.__new__([best_forward, total_weight])

    # With each vertex, associate a best forward arc and total weight.
    table = {after: Vertex(None, 0)}
    changed = True
    while changed:
        changed = False
        for arc in arcs:
            entry = table.get(arc.after)
            if entry is not None:
                weight = arc.weight + entry.total_weight
                previous = table.get(arc.before)
                if previous is None or weight < previous.total_weight:
                    table[arc.before] = Vertex(arc, weight)
                    changed = True
    # Rebuild best path.
    entry = table.get(before)
    if entry is None:
        return None
    path = []
    arc = entry.best_forward
    while arc is not None:
        path.append(arc)
        arc = table[arc.after].best_forward
    return path

def sort(vertices, arcs):
    """\
Topologically sort VERTICES, while obeying the constraints described
in ARCS.  Arcs referring to non-listed vertices are ignored.  Return two
lists, which together hold all original VERTICES, with none repeated.
The first list is the sorted result, the second list gives all vertices
involved into some cycle.
"""

    class Vertex(list):

        vertex = property(make_getter(0), make_setter(0))
        predecessor_count = property(make_getter(1), make_setter(1))
        followers = property(make_getter(2), make_setter(2), make_deleter(2))

    # With each vertex, associate a predecessor count and the set of all
    # follower vertices.
    table = {}
    for vertex in vertices:
        table[vertex] = Vertex([vertex, 0, []])
    for arc in arcs:
        before = table.get(arc.before)
        after = table.get(arc.after)
        if (before is not None
                and after is not None
                and after not in before.followers):
            before.followers.append(after)
            after.predecessor_count += 1
    vertices = list(table.values())
    del table
    # Accumulate sorted vertices in the SORTED list.
    zeroes = []
    for vertex in vertices[:]:
        if vertex.predecessor_count == 0:
            vertices.remove(vertex)
            zeroes.append(vertex)
    sorted = []
    while zeroes:
        new_zeroes = []
        zeroes.sort()
        for zero in zeroes:
            sorted.append(zero.vertex)
            for vertex in zero.followers:
                vertex.predecessor_count -= 1
                if vertex.predecessor_count == 0:
                    vertices.remove(vertex)
                    new_zeroes.append(vertex)
        zeroes = new_zeroes
    # Unprocessed vertices participate into various cycles.
    cycles = []
    for vertex in vertices:
        cycles.append(vertex.vertex)
        del vertex.followers
    return sorted, cycles

def sort2(vertices, arcs):
    """\
Topologically sort VERTICES, while obeying the constraints described
in ARCS.  Arcs referring to non-listed vertices are ignored.  Return a
list containing the sorted result.  That list may contain sublists,
in which case these sublists contain vertices involved together in some cycle.
These sublists taken whole are still topologically sorted within the result.
"""

    class Vertex(list):

        predecessor_count = property(make_getter(1), make_setter(1))
        vertex = property(make_getter(0), make_setter(0))
        followers = property(make_getter(2), make_setter(2), make_deleter(2))

    # With each vertex, associate a predecessor count and the set of all
    # follower vertices.
    table = {}
    for vertex in vertices:
        table[vertex] = Vertex([vertex, 0, []])
    for arc in arcs:
        before = table.get(arc.before)
        after = table.get(arc.after)
        if (before is not None
                and after is not None
                and after not in before.followers):
            before.followers.append(after)
            after.predecessor_count += 1
    vertices = list(table.values())
    del table
    # Accumulate sorted vertices in the SORTED list.
    sorted = []
    while vertices:
        # Sort by decreasing predecessor count.
        vertices.sort()
        vertices.reverse()
        # Consider the last (and lowest) predecessor count.
        if vertices[-1].predecessor_count == 0:
            # If zero, we have a run of topologically sorted vertices.
            while vertices and vertices[-1].predecessor_count == 0:
                vertex = vertices.pop()
                for vertex2 in vertex.followers:
                    vertex2.predecessor_count -= 1
                sorted.append(vertex.vertex)
        else:
            # If not zero, the vertex is necessarily part of a cycle.
            # Find the shortest path back to self.
            cycle = [vertex]
            # ...
            sublist = []
            for vertex in cycle:
                for vertex2 in vertex.followers:
                    vertex2.predecessor_count -= 1
                # Help the Python garbage collector.
                del vertex.followers
                sublist.append(vertex.vertex)
            sorted.append(sublist)
    return sorted

## Code for naming tuple or list elements.

def make_getter(index):

    def getter(self):
        return self[index]

    return getter

def make_setter(index):

    def setter(self, value):
        self[index] = value

    return setter

def make_deleter(index):

    def deleter(self):
        del self[index]

    return deleter

class Arc(tuple):
    """\
An oriented arc holds BEFORE and AFTER as the starting vertex and ending
vertex for that arc.  An arc also holds a positive cost or weight,
a weight of one is implied if none are given.
"""

    def __new__(cls, before, after, weight=None):
        if weight is None:
            return tuple.__new__(cls, [before, after])
        return tuple.__new__(cls, [before, after, weight])

    def weight_getter(self):
        if len(self) > 2:
            return self[2]
        return 1

    before = property(make_getter(0))
    after = property(make_getter(1))
    weight = property(weight_getter)
