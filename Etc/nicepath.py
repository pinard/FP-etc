#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2000, 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2000.

import os

def canonical(path, viewpoint=None):
    return '/'.join(canonical_parts(path, viewpoint))

def nicest(path, viewpoint=None, relative=False):
    if viewpoint is None:
        eye_parts = canonical_parts(os.getcwd())
    else:
        eye_parts = canonical_parts(viewpoint)
    path_parts = canonical_parts(path, viewpoint)
    maximum = min(len(eye_parts), len(path_parts))
    for counter in range(maximum):
        if eye_parts[counter] != path_parts[counter]:
            break
    else:
        counter = maximum
    if relative or len(eye_parts) < 2*counter:
        return '/'.join((['..'] * (len(eye_parts) - counter)
                         + path_parts[counter:]))
    if path[0] != '/':
        return os.path.join(os.getcwd(), path)
    return path

def canonical_parts(path, viewpoint=None):

    def split_and_append(parts, name):
        for part in name.split('/'):
            if part == '..':
                parts.pop()
            elif part != '.' and (part or not parts):
                parts.append(part)
        return parts

    if path[0] == '~':
        path = os.path.expanduser(path)
    elif path[0] != '/':
        if viewpoint is None:
            viewpoint = os.getcwd()
        path = os.path.join(viewpoint, path)
    parts = split_and_append([], path)
    counter = 0
    while counter < len(parts):
        name = '/'.join(parts[:1+counter])
        if name and os.path.islink(name):
            link = os.readlink(name)
            if link[0] == '/':
                link_parts = split_and_append([], link)
            else:
                link_parts = split_and_append(parts[:counter], link)
            parts = link_parts + parts[1+counter:]
            counter = 0
        else:
            counter += 1
    return parts
