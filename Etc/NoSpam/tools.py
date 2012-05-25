#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Miscellaneous service routines.
"""

import os, re, sys

## Finding words in text.

def find_words(text,
               regexp=re.compile("[^-a-z\300-\377]*"
                                 "([-a-z\300-\377]+)"
                                 "[^-a-z\300-\377]*$")):
    words = []
    for word in text.lower().split():
        if len(word) < 25:
            match = regexp.match(word)
            if match is not None:
                words.append(match.group(1))
    return words

## Reading maps.

map_cache = {}

def map_get(map_name, key):
    if key:
        # I would prefer "return read_cached_map(map_name).get(key)", but
        # this is not accepted by `dbhash'.  So let's write it the long way.
        map = read_cached_map(map_name)
        if key in map:
            return map[key]

def map_keys(map_name):
    return list(read_cached_map(map_name).keys())

def read_cached_map(map_name):
    map = map_cache.get(map_name)
    if map is None:
        try:
            method, name = map_name.split(':', 1)
        except ValueError:
            method, name = '', map_name
        if method == 'alias':
            map = map_cache[map_name] = {}
            for line in file(os.path.expanduser(name)):
                if line[0] in '#\n':
                    continue
                fields = line.split(':', 1)
                if (len(fields) == 2
                    and ' ' not in fields[0]
                    and '\t' not in fields[0]
                    ):
                    map[fields[0]] = 'OK'
        elif method == 'file':
            map = map_cache[map_name] = {}
            for line in file(os.path.expanduser(name)):
                if line[0] in '#\n':
                    continue
                fields = [
                    field for field in line.rstrip().split('\t') if field]
                if len(fields) != 2:
                    fields = line.split()
                if (len(fields) != 2
                    or fields[1] not in ('OK',  'ACCEPT', 'REJECT', 'KILL',
                                         'RELAY')
                    ):
                    sys.stderr.write("Dubious `%s' line: %s" % (name, line))
                else:
                    key, value = fields
                    key = fields[0].lower()
                    if key in map:
                        sys.stderr.write(
                            "In `%s', `%s' reset from `%s' to `%s'\n"
                            % (name, key, map[key], fields[1]))
                    map[key] = fields[1]
        elif method == 'hash':
            import dbm.bsd
            map = map_cache[map_name] = dbm.bsd.open(
                os.path.expanduser(name), 'r')
        else:
            assert False, "Unknown method for `%s'" % map_name
    return map

## Executing system commands.

def get_program_path(name,
                     search_path=os.environ['PATH'].split(':'), cache={}):
    if name in cache:
        return cache[name]
    for directory in search_path:
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            cache[name] = path
            return path
    cache[name] = None

def run_program(command, write):
    write('\n%s--->\n' % ('-' * 60))
    write("Running %s\n" % command)
    process = os.popen(command)
    write(process.read())
    status = process.close()
    if status is None:
        status = 0
    else:
        status = status >> 8
    write("Returned %d\n" % status)
    write('%s---<\n' % ('-' * 60))
    return status
