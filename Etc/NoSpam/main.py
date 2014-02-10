#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 1998, 99, 00, 01, 02, 03 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 1998.

"""\
This tool scans one or many messages for possible SPAM, and if a message
is found to be SPAM-like, adds `X-Junk:' headers to explain what was found.

.------------------------------.
| Usage for message analysis.  |
`------------------------------'

Usage: nospam [OPTION]... [INPUT]...

Operation mode:
  -h        Print this help and do nothing else.
  -C FILE   Use FILE as configuration file.
  -l        Avoid diagnosing non-local addresses (for imported mailboxes).

Input format:
  -b   Study all messages within given Babyl INPUTs (visible headers only).
  -m   Study all messages within mailbox format INPUTs.

Debugging:
  -k     Keep work files holding unpacked hierarchy.
  -d     Diagnose messages without copying them, repeat for more verbosity.
  -dd    Like -d, also print Received and X-Mailer data, and spamicity.
  -ddd   Like -dd, also trace language guessing.

Without -b nor -m, each INPUT contains a single message.  If there
no INPUT, process a single message from standard input.  Without -d
or -g, full messages, with possible header lines added, are copied
to standard output.  Analysis is driven by a directive file: if -C
does not specify it, this is `~/.nospamrc'.

.--------------------------.
| Usage for map handling.  |
`--------------------------'

Usage: nospam OPTION MAP [TYPE:FILE]...

Map handling:
  -E   Create an empty dbm-hashed MAP.
  -U   Update an already existing dbm-hashed MAP.

TYPE:FILE says that FILE contains an association between keys and
values.  TYPE indicates how FILE should be read.  If TYPE is `alias',
FILE lines beginning with a field containing no whitespace and followed
by a colon provide that field as a key and `OK' for its value.  If
TYPE is `file', empty lines or lines beginning with `#' are ignored,
remaining lines should hold either either a single run of TABs or spaces
as a separator, the first part being the key, and the second part being
the value, normally one of `OK', `RELAY', `KILL', `REJECT' or `ACCEPT'.
If TYPE is `hash', FILE is a dbm-hashed map.

.------------------------------.
| Format of a directive file.  |
`------------------------------'

In a directive file, empty lines or lines beginning with `#' are
ignored.  Other lines contain fields separated by whitespace, the first
such field is the name of the directive, others are its arguments.
Lines may be continued by ending them with a backslash.

Wherever a map (TYPE:FILE) is used as a directive argument, and the
wanted value of a key-value pair is `ACCEPT', the message is not
considered as SPAM, regardless of other SPAM clues the program may
get.  The `OK' value is not as strong, as it does not inhibit other
SPAM tests.  The `REJECT' and `KILL' values get the message to be
considered as SPAM, but the intent of `KILL' is to provide a diagnostic
recognisable by tools like `procmail', so the message is not even
delivered.  The `RELAY' value has no effect.

The map arguments to either `locals' or `domains' directive are
processed a bit specially, as map keys may be domains (preceded by an
`@' sign), users, or full email addresses, yielding lookups to multiple
interpretations.  A mapped domain always implies all its subdomains, but
if both the domain and one of its subdomains are listed, the subdomain
wins.  A full email address wins over the mere user or the mere domain.
A user is not considered if there is any `here' directive and the domain
to check is not part of a `here' domain.  If no decision is reached from
the above, the map is finally checked for each domain fragment in the
lookup request.

The `here' directive lists the domains for the host running this
program.  Whenever this directive is used at least once, any email
address in message headers referring to any domain listed in an `here'
directive should also name acceptable user.  Acceptable users are to be
listed through any of the `locals' directives.

The `check` directive requires one or many arguments, `usual' means
all tests, including `spambayes, but not `bogofilter'. 'body' rejects
messages with an empty body. `charset' rejects messages using too
foreign charsets (the list is currently built-in). 'date', 'from',
'message_id', `precedence', 'received', 'subject', 'to_cc' check that
the corresponding headers are not missing, and good looking (for some
meaning of "good looking"!). `viruses' seeks for a few installed virus
scanners and calls hose which are found.

The `bogofilter' and `spambayes' directives both compute the Graham
spamicity factor, one using Bogofilter, the other using Spambayes.  Both
directives accept two optional arguments.  The first is the factor that
should be exceeded for the message to be rejected.  The second is the
factor that should be exceeded for the message to be killed.  Defaults
are 0.75 and 1.00 for `bogofilter' and 0.90 and 1.00 for `spambayes',
yet that 0.90 may itself be overridden through Spambayes configuration
mechanisms.

The `mailer' directive uses its map arguments to check the contents of
the `X-Mailer:' header.

The `locals' directive uses its map arguments to provide a list of
email addresses considered acceptable as local, it should in particular
contains most mailing lists the user is subscribed to.  Unless the `-l'
option is used, a message ought to have either a local origin or at
least one local destination.  If at least one `here' directive is used,
the `locals' map arguments should also provide a list of all acceptable
local users.

The `domains' directive uses its map arguments to check the `From:'
header.  This is used to filter out domains known for spamming.

The `mimetypes' directive lists which MIME content types are acceptable
in attachments.  If this directive is not used, content types are not
checked.

The `extensions' directive lists which file extensions are acceptable
for MIME attachments.  If this directive is not used, extensions are not
checked.

The `words' directive uses its map arguments to provide a list of words
to check in the `Subject:' header.

The `locutions' directive uses its map arguments to provide a list of
textual fragments to check within the `Subject:' header and the whole
body of the message.  Such fragments are meant to be often found in
SPAM mail, but they are checked literally: spaces and newlines are not
equivalent.

The `languages' directive accepts a list of languages to reject.
For arguments being `English', `French', 'German' or `Spanish', the
`Subject:' header and message body are studied in hope to recognise the
language used.  For argument being `Others', the MIME charset is checked
for a known value.

The `blacklists' directive accepts a list of domains in use by the MAPS
project, a `.mail-abuse.org' suffix is automatically implied if there
is no dot.  Submitted for verification are the (possibly many) machines
corresponding to the From domain.  The message is considered SPAM is
some machine is listed in some MAPS map.  Here is a table of possible
domains, and an URL to get more information.

    blackholes   http://www.mail-abuse.org/rbl
    dialups      http://www.mail-abuse.org/dul
    relays       http://www.mail-abuse.org/rss

For more information, visit:

    http://www.iki.fi/era/rbl/rbl.html
"""

# PREREQUISITES:
# - possibly create file `~/.nospamrc' if not relying on the default.
# - possibly modify `~/.procmailrc' according to taste.
# - make sure Postfix uses `procmail' to deliver mail.

# GLOBAL PROCMAIL:
# - intercept `X-Junk:' marked files, redirect towards moderator.
# - have a means to let go messages, once granted by moderator.

# TODO:
# - study the sequence of `Received:' headers.
# - ponder how to counter-attack by complaining.
# - recognise unattended Base64.
# - switch to ConfigParser.
 
# Main program.


import os, sys
from . import tools

PACKAGE = 'NoSpam'
VERSION = '0.23'

class Main:
    def __init__(self):
        # Options.
        self.nospamrc = None
        self.empty = None
        self.update = None
        self.debug = 0
        self.format = 'single'
        self.keep = False
        self.silence_locals = False
        # Decoding `.nospamrc`.
        self.heres = []
        self.instructions = []
        # Statistics.
        self.count_junked = None
        self.total_seen = 0
        self.total_junked = 0
        self.total_killed = 0

    def main(self, *arguments):
        import getopt
        options, arguments = getopt.getopt(arguments, 'C:E:U:bdhklm')
        for option, value in options:
            if option == '-C':
                self.nospamrc = value
            elif option == '-E':
                self.empty = value
            elif option == '-U':
                self.update = value
            elif option == '-b':
                self.format = 'babyl'
            elif option == '-d':
                self.debug += 1
            elif option == '-h':
                sys.stdout.write(__doc__)
                return
            elif option == '-k':
                self.keep = True
            elif option == '-l':
                self.silence_locals = True
            elif option == '-m':
                self.format = 'mailbox'
        if self.empty or self.update:
            import dbm.bsd
            if self.empty:
                map = dbm.bsd.open(self.empty, 'n')
            else:
                map = dbm.bsd.open(self.update, 'c')
            for argument in arguments:
                for key in tools.map_keys(argument):
                    map[key] = tools.map_get(argument, key)
        else:
            write = sys.stderr.write
            if self.nospamrc is None:
                name = os.path.expanduser('~/.nospamrc')
                if os.path.exists(name):
                    self.nospamrc = name
                else:
                    write("* Missing configuration file")
            self.read_nospamrc(self.nospamrc)
            if arguments:
                for argument in arguments:
                    self.check_folder(file(argument), argument)
                if self.debug and len(arguments) > 1:
                    write('\nJunked %d/%d total messages'
                                     % (self.total_junked, self.total_seen))
                    if self.total_killed:
                        write(' (%d killed)' % self.total_killed)
                    write('\n')
            else:
                self.check_folder(sys.stdin, '<stdin>')

    def read_nospamrc(self, name):

        def logical_lines(name):
            line = ''
            for next in file(name):
                next = next.rstrip()
                if next and next[0] != '#':
                    if next[-1] == '\\':
                        line += next[:-1]
                    else:
                        yield line + next
                        line = ''
            if line:
                yield line

        for line in logical_lines(name):
            fields = line.split()
            opcode, arguments = fields[0], fields[1:]
            if opcode == 'here':
                self.heres += arguments
            else:
                self.instructions.append((opcode, arguments))

    def check_folder(self, folder, name):
        if self.debug:
            write = sys.stdout.write
            write('\n%s\n' % name)
        self.count_junked = 0
        self.count_killed = 0

        def message_builder(handle):
            from email import message_from_file, Errors
            try:
                message = message_from_file(handle)
            except Errors.MessageParseError:
                # Do not return None, this would stop the mailbox iterator.
                message = ''
            return message

        if self.format == 'single':
            Checker(message_builder(folder), 1)
            counter = 1
        else:
            import mailbox
            if self.format == 'mailbox':
                box = mailbox.UnixMailbox(folder, message_builder)
            elif self.format == 'babyl':
                box = mailbox.BabylMailbox(folder, message_builder)
            counter = 0
            for message in box:
                counter += 1
                Checker(message, counter)
            if self.debug:
                write('Junked %d/%d messages' % (self.count_junked, counter))
                if self.count_killed:
                    write(' (%d killed)' % self.count_killed)
                write('\n')
        self.total_seen += counter
        self.total_junked += self.count_junked
        self.total_killed += self.count_killed

run = Main()
main = run.main

class Checker:
    class Map_Exception(Exception): pass
    class ACCEPT_in_Map(Map_Exception): pass
    class REJECT_in_Map(Map_Exception): pass
    class KILL_in_Map(Map_Exception): pass

    def __init__(self, message, counter):
        self.report_diagnostics = []
        self.accept_diagnostics = []
        self.reject_diagnostics = []
        self.kill_diagnostics = []
        try:
            if message:
                from . import checks
                checks.Check(message, run, self)
            else:
                self.reject("Invalid message structure.")
        except Checker.Map_Exception:
            pass
        write = sys.stdout.write
        if run.debug:
            diagnostics = (
                ["ACCEPT: " + diagnostic
                 for diagnostic in self.accept_diagnostics]
                + ["KILL: " + diagnostic
                   for diagnostic in self.kill_diagnostics]
                + self.reject_diagnostics + self.report_diagnostics)
            if diagnostics:
                text = '%3d.' % counter
                for diagnostic in diagnostics:
                    write('  %s %s\n' % (text, diagnostic))
                    text = ' ' * len(text)
                if not self.accept_diagnostics:
                    if self.reject_diagnostics or self.kill_diagnostics:
                        run.count_junked += 1
                        if self.kill_diagnostics:
                            run.count_killed += 1
        elif run.format == 'single' or not self.kill_diagnostics:
            text = message.as_string(True)
            position = text.find('\n\n')
            if position < 0:
                position = len(text)
            write(text[:position+1])
            if not self.accept_diagnostics:
                if self.reject_diagnostics or self.kill_diagnostics:
                    import socket
                    host = socket.gethostname()
                    write('X-Junk: %s %s using %s:%s\n'
                          % (PACKAGE, VERSION, host, run.nospamrc))
                    for diagnostic in self.reject_diagnostics:
                        write('X-Junk: > %s\n' % diagnostic)
                    for diagnostic in self.kill_diagnostics:
                        write('X-Junk: > KILL: %s\n' % diagnostic)
            write(text[position+1:])

    def report(self, text):
        self.report_diagnostics.append(text)

    def get_value(self, map_name, key, diagnostic):
        value = tools.map_get(map_name, key)
        if value == 'ACCEPT':
            diagnostic = "`%s' by `%s'." % (key, map_name)
            if diagnostic not in self.accept_diagnostics:
                self.accept_diagnostics.append(diagnostic)
            if not run.debug:
                raise Checker.ACCEPT_in_Map
        if value == 'REJECT':
            self.reject(diagnostic)
        if value == 'KILL':
            self.kill(diagnostic)
        return value

    def reject(self, diagnostic):
        if diagnostic not in self.reject_diagnostics:
            self.reject_diagnostics.append(diagnostic)
        # Commented so a later KILL will be detected.
        #if not run.debug:
        #    raise Checker.REJECT_in_Map

    def kill(self, diagnostic):
        if diagnostic not in self.kill_diagnostics:
            self.kill_diagnostics.append(diagnostic)
        if not run.debug:
            raise Checker.KILL_in_Map

if __name__ == '__main__':
    main(*sys.argv[1:])
