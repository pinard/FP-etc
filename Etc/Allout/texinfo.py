#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 1995, 1997, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 1995-01.

u"""\
Lorsque ACTION est `texi', ce programme produit un fichier Texinfo à partir
des indications contenues dans le fichier `allout'.  (Convert a file from
allout (outline) format back to Texinfo format.)  Nous avons alors:

Usage: allout texi [OPTION]... [INPUT]...

  -H        suppress Texinfo file header
  -T        suppress Texinfo file trailer
  -I PATH   search included Texinfo files along PATH

Les conventions d'écriture d'un fichier `allout' en vue d'une transformation
Texinfo ne sont pas encore décrites ici.  Pour l'un des ces jours pluvieux!
"""

__metaclass__ = type
from Etc.Unicode import apply, deunicode, file, open, os, reunicode, sys
import re

Default_Copyright = u"""\
Permission is granted to make and distribute verbatim copies of
this manual provided the copyright notice and this permission notice
are preserved on all copies.

@ignore
Permission is granted to process this file through TeX and print the
results, provided the printed document carries copying permission
notice identical to this one except for the removal of this paragraph
(this paragraph not being relevant to the printed manual).

@end ignore
Permission is granted to copy and distribute modified versions of this
manual under the conditions for verbatim copying, provided that the entire
resulting derived work is distributed under the terms of a permission
notice identical to this one.

Permission is granted to copy and distribute translations of this manual
into another language, under the above conditions for modified versions,
except that this permission notice may be stated in a translation approved
by the Foundation.
"""

directive_map = {
    (u'@section', 1) : u'@chapter',
    (u'@section', 2) : u'@section',
    (u'@section', 3) : u'@subsection',
    (u'@section', 4) : u'@subsubsection',
    (u'@unnumbered', 1) : u'@unnumbered',
    (u'@unnumbered', 2) : u'@unnumberedsec',
    (u'@unnumbered', 3) : u'@unnumberedsubsec',
    (u'@unnumbered', 4) : u'@unnumberedsubsubsec',
    (u'@heading', 1) : u'@majorheading',
    (u'@heading', 2) : u'@heading',
    (u'@heading', 3) : u'@subheading',
    (u'@heading', 4) : u'@subsubheading',
    (u'@appendix', 1) : u'@appendix',
    (u'@appendix', 2) : u'@appendixsec',
    (u'@appendix', 3) : u'@appendixsubsec',
    (u'@appendix', 4) : u'@appendixsubsubsec',
    }

class Main:
    def __init__(self):
        # Options.
        self.includes = []
        self.header = True
        self.trailer = True
        # Variables.
        self.French = False
        self.Titlepage = None
        self.Oneliner = None            # `\n' included
        self.Copyline = None
        self.Filename = None
        self.Header = None
        self.Version = None
        self.Edition = None
        self.Updated = None
        self.Entries = None
        self.Title = None
        self.Subtitle = None
        self.Subtitle2 = None
        self.Author = None
        self.Author2 = None
        self.Description = None
        self.Copyright = None            # `\n' included
        # Flattener.
        import string
        self.flattener = string.maketrans(
            u'àâçéêèëîïôûùüÀÂÇÉÊÈËÎÏÔÛÙÜ«»:`\''.encode(u'Latin-1'),
            ur'aaceeeeiiouuuAACEEEEIIOOUU     ')
        # Index processing.
        self.equivalences = {}
        self.delayed_text = u''

    def main(self, *arguments):
        arguments = self.save_options(arguments)
        if arguments:
            for argument in arguments:
                self.process_file(argument, file(argument))
        else:
            self.process_file(u'<stdin>', sys.stdin)

    def save_options(self, arguments):
        # Decode options.
        import getopt
        options, arguments = getopt.getopt(arguments, u'I:HT')
        for option, value in options:
            if option == u'-I':
                self.includes = value.split(u':')
            elif option == u'-H':
                self.header = False
            elif option == u'-T':
                self.trailer = False
        return arguments

    def process_file(self, name, input):
        self.input_name = name
        structure = self.extract_structure(input)
        self.ensure_values()
        write = sys.stdout.write
        if self.header:
            self.produce_header(write)
        self.process_structure(structure, write, 0)
        if self.trailer:
            self.produce_trailer(write)

    def extract_structure(self, input):
        # Process initial lines.
        line = input.readline()
        if line and line[0] not in u'*.':
            line = line.rstrip()
            for ending in u'-*- outline -*-', u'allout':
                if line.endswith(ending):
                    line = line[:-len(ending)].rstrip()
            self.Oneliner = line + u'\n'
            line = input.readline()
        if line and line[0] not in u'*.':
            match = re.match(u'Copyright (\(C\)|©) (.*)', line)
            if not match:
                sys.stderr.write(
                    u"%(input_name)s might not be in proper format.\n"
                    % self.__dict__)
                sys.exit(1)
            self.Copyline = match.group(2) + u'\n'
            line = input.readline()
        variable = None
        spacing = 0
        while line and line[0] not in u'*.':
            line = line.rstrip()
            match = re.match(u'(\S+):\s+(.*)', line)
            if match:
                if variable:
                    self.set_variable(variable, u''.join(fragments))
                variable = match.group(1)
                fragments = [match.group(2)]
                spacing = 0
            elif line:
                assert variable
                if fragments:
                    spacing += 1
                if spacing:
                    fragments.append(u'\n' * spacing)
                    spacing = 0
                if variable == u'Entries' and line[0] == u'-':
                    line = u'*' + line[1:]
                fragments.append(line)
            else:
                spacing += 1
            line = input.readline()
        if variable:
            self.set_variable(variable, u''.join(fragments))
        # Return the allout part as a structure.
        def generator(line, input):
            yield line
            for line in input:
                yield line
        import allout
        return allout.read(generator(line, input))

    def ensure_values(self):
        # Ensure values to some variables.
        if not self.Filename:
            self.Filename = os.path.splitext(self.input_name)[0] + u'.info'
        if not self.Header:
            if self.Title:
                self.Header = self.Title
            else:
                self.Header = self.input_name
        if not self.Title:
            self.Title = self.Header
        if self.header and not self.Copyright:
            if os.path.exists(u'copyrall'):
                self.Copyright = file(u'copyrall').read()
            elif os.path.exists(u'../copyrall'):
                self.Copyright = file(u'../copyrall').read()
            else:
                self.Copyright = Default_Copyright

    def set_variable(self, variable, value):
        if variable[0].isupper() and hasattr(self, variable):
            setattr(self, variable, value)
        else:
            sys.stderr.write(u"%s: Unknown variable `%s'\n"
                             % (self.input_name, variable))

    def produce_header(self, write):
        # Produce the long document header.
        if self.French and self.French.lower() not in (u'0', u'false',
                                                       u'no', u'non'):
            write(u'\\def\\putwordTableofContents{Table des mati\\`eres}\n'
                  u'\\input texinfoec @c -*- texinfo -*-\n')
        else:
            write(u'\\input texinfo\n')
        write(u'@c %%**start of header\n'
              u'@setfilename %(Filename)s\n'
              u'@settitle %(Header)s\n'
              u'@finalout\n'
              u'@c %%**end of header\n'
              % self.__dict__)
        if self.Version or self.Edition or self.Updated:
            write(u'\n')
            if self.Version:
                write(u'@set VERSION %(Version)s\n' % self.__dict__)
            if self.Edition:
                write(u'@set EDITION %(Edition)s\n' % self.__dict__)
            if self.Updated:
                write(u'@set UPDATED %(Updated)s\n' % self.__dict__)
        elif os.path.exists(u'version.texi'):
            write(u'\n')
            if self.includes:
                self.include(u'version.texi')
            else:
                write(u'@include version.texi\n')
        write(u'\n'
              u'@ifinfo\n'
              u'@set Francois Franc,ois\n'
              u'@end ifinfo\n'
              u'@tex\n'
              u'@set Francois Fran\\noexpand\\ptexc cois\n'
              u'@end tex\n')
        if self.Entries:
            write(u'\n'
                  u'@ifinfo\n'
                  u'@format\n'
                  u'START-INFO-DIR-ENTRY\n'
                  u'%(Entries)s'
                  u'END-INFO-DIR-ENTRY\n'
                  u'@end format\n'
                  u'@end ifinfo\n'
                  % self.__dict__)
        write(u'\n'
              u'@ifinfo\n'
              u'%(Oneliner)s'
              u'\n'
              u'Copyright © %(Copyline)s\n'
              u'\n'
              u'%(Copyright)s'
              u'@end ifinfo\n'
              u'\n'
              u'@titlepage\n'
              % self.__dict__)
        if self.Titlepage:
            write(u'%(Titlepage)s' % self.__dict__)
        else:
            write(u'@title %(Title)s\n' % self.__dict__)
            if self.Subtitle:
                write(u'@subtitle %(Subtitle)s\n' % self.__dict__)
            if self.Subtitle2:
                write(u'@subtitle %(Subtitle2)s\n' % self.__dict__)
            if self.Author:
                write(u'@author %(Author)s\n' % self.__dict__)
            if self.Author2:
                write(u'@author %(Author2)s\n' % self.__dict__)
        write(u'\n'
              u'@page\n'
              u'@vskip 0pt plus 1filll\n'
              #'@insertcopying\n'
              u'Copyright @copyright{} %(Copyline)s\n'
              u'\n'
              u'%(Copyright)s\n'
              u'@end titlepage\n'
              u'\n'
              u'@ifhtml\n'
              u'@set top-menu\n'
              u'@end ifhtml\n'
              u'@ifinfo\n'
              u'@set top-menu\n'
              u'@end ifinfo\n'
              u'\n'
              u'@ifset top-menu\n'
              u'@node Top\n'
              u'@top %(Header)s\n'
              % self.__dict__)
        if self.Description:
            write(u'\n%(Description)s\n' % self.__dict__)
        write(u'\n'
              u'@menu\n'
              u'@end menu\n'
              u'\n'
              u'@end ifset\n')

    def produce_trailer(self, write):
        write(u'\n'
              u'@contents\n'
              u'@bye\n'
              u'\n'
              # Split the following line so Emacs will not recognize it,
              # while editing this script.
              u'@c Local ' u'variables:\n'
              u'@c texinfo-column-for-description: 32\n'
              u'@c End:\n')

    def process_structure(self, structure, write, level):
        # Transform the allout structure.
        if isinstance(structure, str):
            self.output_text(structure, write)
            return
        if u' ' in structure[0]:
            first, rest = structure[0].split(None, 1)
        else:
            first = structure[0]
            if first.endswith(u'.all'):
                texi_name = first[:-4] + u'.texi'
                if self.includes:
                    self.include(texi_name)
                    return
                write(u'@include %s\n' % texi_name)
                return
            rest = u''
        if first.startswith(u'@'):
            if first in (u'@section', u'@unnumbered', u'@heading', u'@appendix'):
                try:
                    directive = directive_map[first, level+1]
                except KeyError:
                    directive = u'@c %s-%d' % (first[1:], level+1)
                if u',' in rest:
                    second, third = rest.split(u',', 1)
                else:
                    second = third = rest
                if second != u'-':
                    second = second.replace(u'@@', u' ')
                    second = re.sub(ur'@[^{]+{([^}]*)}', ur'\1', second)
                    second = second.translate(self.flattener)
                    second = re.sub(u'  +', u' ', second)
                    write(u'@node %s\n' % second)
                self.output_text(u'%s %s' % (directive, third), write)
                for sub in structure[1:]:
                    self.process_structure(sub, write, level+1)
                return
            if first in (u'@display', u'@example', u'@format', u'@lisp', u'@menu',
                         u'@quotation', u'@smalldisplay', u'@smallexample',
                         u'@smallformat', u'@smalllisp'):
                assert not rest, rest
                write(u'%s\n' % first)
                for sub in structure[1:]:
                    self.process_structure(sub, write, level)
                write(u'@end %s\n' % first[1:])
                return
            if first in (u'@enumerate', u'@itemize', u'@table'):
                if rest:
                    write(u'%s %s\n' % (first, rest))
                else:
                    write(u'%s\n' % first)
                for sub in structure[1:]:
                    self.process_structure_item(sub, write, level)
                write(u'@end %s\n' % first[1:])
                return
        if structure[0]:
            self.output_text(structure[0], write)
        for sub in structure[1:]:
            self.process_structure(sub, write, level)

    def process_structure_item(self, structure, write, level):
        # Transform an allout structure while introducing an @item.
        if structure[0]:
            self.output_text(u'@item %s' % structure[0], write)
        else:
            write(u'@item\n')
        for sub in structure[1:]:
            self.process_structure(sub, write, level)

    def include(self, name, write):
        for directory in self.includes:
            if os.path.exists(u'%s/%s' % (directory, name)):
                name = u'%s/%s' % (directory, name)
                break
        sys.stderr.write(u"Including %s..." % name)
        inside = False
        for line in file(name):
            if inside:
                if line in (u'@contents\n', u'@bye\n'):
                    break
                write(line)
            elif line.startswith(u'@node '):
                if line != u'@node Top\n' and not line.startswith(u'@node top,'):
                    inside = True
                    write(line)
        sys.stderr.write(u" done\n")

    def output_text(self, text, write,
                    searcher = re.compile(u'@<([^>]*)>([^ ]*)').search):

        def output_protecting_colons(text):
            # Force a space before textual colons.
            text = re.sub(ur'([^ ]):$', ur'\1@w{ :}', text)
            text = re.sub(ur'([^ ]): ', ur'\1@w{ :} ', text)
            write(u'%s\n' % text)

        # Merge text after anything delayed.
        if self.delayed_text:
            text = self.delayed_text + u' ' + text
            self.delayed_text = u''
        # If line fully empty, only then produce an empty line.
        if not text:
            write(u'\n')
            return
        # Recognise index entries and produce them.
        match = searcher(text)
        while match:
            fragment = text[:match.start()].rstrip() + match.group(2)
            if fragment:
                output_protecting_colons(fragment)
            fragments = [fragment.strip()
                         for fragment in match.group(1).split(u'::')]
            if len(fragments) > 1:
                # Declare an equivalence between index entries.
                entries = []
                for fragment in fragments:
                    fragment = fragment.strip()
                    if u':' in fragment:
                        index, entry = fragment.split(u':', 1)
                    else:
                        index, entry = u'c', fragment
                    assert (index, entry) not in self.equivalences, (
                        self.equivalences[index, entry])
                    entries.append((index, entry))
                for index, entry in entries:
                    self.equivalences[index, entry] = entries
            else:
                # Process an actual index entry.
                for fragment in match.group(1).split(u';'):
                    fragment = fragment.strip()
                    if u':' in fragment:
                        index, entry = fragment.split(u':', 1)
                    else:
                        index, entry = u'c', fragment
                    try:
                        entries = self.equivalences[index, entry]
                    except KeyError:
                        entries = [(index, entry)]
                    for index, entry in entries:
                        write(u'@%sindex %s\n' % (index, entry))
            text = text[match.end():].lstrip()
            match = searcher(text)
        if text:
            match = re.search(u'@<', text)
            if match:
                # Incomplete index entry, delay it until next line.
                self.delayed_text = text[match.start():]
                text = text[:match.start()]
            output_protecting_colons(text)

main = Main().main

if __name__ == u'__main__':
    main(*sys.argv[1:])
