#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Virus scanners.
"""

# Inspired by AMaViS 0.2.1, see http://amavis.org/.  AMaViS itself is:
# - written by Mogens Kjaer, Carlsberg Laboratory, <mk@crc.dk>,
# - modified by Juergen Quade, Softing GmbH, <quade@amavis.org>,
# - modified and maintained by Christian Bricart <shiva@aachalon.de>,
# - modified by Chris L. Mason <cmason@unixzone.com>,
# - modified and maintained by Rainer Link, SuSE GmbH <link@suse.de>.
# Copyright (C) 1996..2000 the people mentioned above.  Also GPL'ed.

import os, types
from . import tools

def all(instances=[]):
    if not instances:
        for object in globals().values():
            if (type(object) is type
                and issubclass(object, Scanner)
                and object is not Scanner
                ):
                instances.append(object())
    return instances

class Scanner:
    Program_Not_Found = 'Program not found'
    name = 'Generic'
    program = 'Unknown'

    def check(self):
        try:
            return self.get_path()
        except Scanner.Program_Not_Found:
            pass

    def get_path(self):
        path = tools.get_program_path(self.program)
        if path is None:
            raise Scanner.Program_Not_Found(self.program)
        return path

    def scan(self, directory, checker):
        raise self.Program_Not_Found

    def report_viruses(self, names, checker):
        if names:
            if len(names) == 1:
                prefix = "Virus `%s'" % names[0]
            else:
                prefix = "Viruses `%s'" % '\', `'.join(names)
            checker.reject("%s found by `%s'." % (prefix, self.name))
        else:
            checker.reject("Virus found by `%s'." % self.name)

    def report_internal_error(self, checker):
        checker.reject("Internal error in `%s' scanner." % self.name)

class AntiVir(Scanner):
    name = 'H+BEDV AntiVir'
    program = 'antivir'

    def scan(self, directory, checker):
        path = tools.get_program_path('antivir')
        if path is None:
            assert False
            return
        import tempfile
        logfile = tempfile.mktemp()
        try:
            status = tools.run_program(
                ('%s --allfiles -q -s -z -ra -rf%s %s >/dev/null 2>> %s'
                 % (path, logfile, directory, logfile)),
                checker.report)
            file_line = ''
            viruses = []
            for line in file(logfile):
                if line.startswith(' VIRUS:'):
                    viruses.append(line.split()[-1][1:-1])
        finally:
            try:
                os.remove(logfile)
            except os.error:
                pass
        if viruses or status == 1:
            self.report_viruses(viruses, checker)
        elif status > 1:
            self.report_internal_error(checker)
