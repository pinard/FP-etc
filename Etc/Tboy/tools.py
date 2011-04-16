# -*- coding: utf-8 -*-
# Copyright © 2009 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2009.

__metaclass__ = type
import codecs, locale, os, sys, re
from lxml import etree

TOMBOY_DIR = os.path.expanduser('~/.local/share/tomboy')
DOCBOOK_DOCTYPE = (
        '<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.1.2//EN"'
        ' "http://www.oasis-open.org/docbook/xml/4.1.2/docbookx.dtd">'
        '\n')
HTML_DOCTYPE = (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">'
        #' HTML 4.01 Strict//EN" "http://www.w3.org/TR/html4/strict.dtd">'
        '\n')
ENCODING = 'UTF-8'
NON_BREAKABLE_SPACE = u'\u00a0'

def clean_file_name(name):
    # TODO: Les blancs devraient être acceptés par site.mk/site-Makefile.
    return re.sub('[ :/\\\\?\']{1,}', ' ', name).replace(' ', '_')

def is_ignorable_title(title):
    if title.startswith(u"Modèle de bloc-notes "):
        return True
    if title.endswith(u" Notebook Template"):
        return True
    return title in (u"Nouveau modèle de note",
                     u"Démarrer ici",
                     u"Utilisation des liens dans Tomboy",
                     u"New Note Template",
                     u"Start Here",
                     u"Using Links in Tomboy")

def is_linkable(outer, inner):
    # May the outer note link to the inner note?
    if not inner.run.site.is_kept(inner):
        return False
    priority = {':b': 1, ':p': 2, ':t': 0}
    return (priority.get(outer.title[-2:], 0)
            >= priority.get(inner.title[-2:], 0))

def pretty_title(text):
    suffix = {':b': u'⁻', ':p': u'⁺', ':t': ''}.get(text[-2:])
    if suffix is None:
        return text
    return text[:-2] + suffix

def each_regexp(pattern, buffer, name):
    for match in re.finditer(pattern, buffer):
        start = match.start()
        end = match.end()
        yield buffer[start:end], Location(name, start, end)

def each_xml_tag(tag, buffer, name):
    start_tag = '<' + tag + '>'
    end_tag = '</' + tag + '>'
    end = 0
    while True:
        start = buffer.find(start_tag, end)
        if start < 0:
            break
        start += 2 + len(tag)
        end = buffer.find(end_tag, start)
        if end < 0:
            break
        yield (buffer[start:end].replace('&amp;', '&'),
               Location(name, start, end))
        end += 3 + len(tag)

def xsl_transformer(name, cache={}):
    xslt = cache.get(name)
    if xslt is None:
        filename = os.path.join(os.path.dirname(sys.argv[0]),
                                '../share/tboy', name)
        xslt = cache[name] = etree.XSLT(etree.parse(filename))
    return xslt

def xsl_boolean(value):
    if value:
        return "true()"
    return "false()"

def xsl_string(value):
    if value:
        return '"%s"' % value
    return '""'

class Sweeper:
    todo_file = os.path.expanduser('~/fp/WorkFlowy.dump')
    note_count = 0
    character_count = 0
    from_tomboy_count = 0
    from_todo_count = 0
    url_count = 0

    def __init__(self, run, notes):
        self.run = run
        self.arrows = {}
        self.errors = []
        for note in notes:
            self.digest(codecs.open(note.input_name, 'r', ENCODING).read(),
                        note.input_name)
        self.marked = set()

    def digest(self, buffer, name):
        self.note_count += 1
        self.character_count += len(buffer)
        for title, location in each_xml_tag('title', buffer, name):
            break
        else:
            self.run.report_error(name, "No title")
            return
        if title not in self.arrows:
            self.arrows[title] = []
        for fragment, location in each_regexp(' \t', buffer, name):
            self.errors.append((title, u"Space then tab", location))
        for fragment, location in each_xml_tag('link:broken', buffer, name):
            self.errors.append((title, u"Broken link", location))
        for internal, location in each_xml_tag('link:internal', buffer, name):
            self.from_tomboy_count += 1
            for fragment, _ in each_xml_tag('monospace', internal, None):
                internal = fragment
                break
            self.arrows[title].append((internal, location))
        for external, location in each_xml_tag('link:url', buffer, name):
            self.url_count += 1

    def mark(self, ancestor):
        self.marked.add(ancestor)
        for child, location in self.arrows[ancestor]:
            if child in self.arrows:
                if not child in self.marked:
                    self.mark(child)
            else:
                self.errors.append((ancestor, u"Dangling link", location))

    def find_path(self, start, goal):
        return self.find_path_recursive(start, goal, [])

    def find_path_recursive(self, start, goal, seen):
        seen = seen + [start]
        if start == goal:
            return seen
        if start in self.arrows:
            for child, location in self.arrows[start]:
                if child not in seen:
                    path = self.find_path_recursive(child, goal, seen)
                    if path is not None:
                        return path

    def report_errors(self):
        todo_buffer = None
        for title in set(self.arrows) - self.marked:
            if not is_ignorable_title(title):
                if todo_buffer is None:
                    if os.path.exists(self.todo_file):
                        todo_buffer = (open(self.todo_file).read()
                                       .decode('UTF-8'))
                    else:
                        todo_buffer = ''
                if title not in todo_buffer:
                    self.errors.append((title, u"Unreachable", None))
        if os.path.exists(self.todo_file):
            pattern = re.compile(
                ('\\b(%s)$'
                 % '|'.join([re.escape(title) for title in self.arrows])),
                re.UNICODE)
            for line in codecs.open(self.todo_file, encoding=ENCODING):
                line2 = line.strip()
                if line2.startswith('- '):
                    line2 = line2[2:]
                for match in re.finditer('[^ ]:[bnpt]\\b', line2):
                    if pattern.search(line2, endpos=match.end()):
                        self.from_todo_count += 1
                    else:
                        self.run.report_error(
                            'WorkFlowy', u"Unknown (%s)" % line2[:match.end()])
        for title, diagnostic, location in sorted(self.errors):
            if location is not None:
                diagnostic += ' (' + location.context() + ')'
            self.run.report_error(title, diagnostic)

    def display_stats(self):
        write = sys.stdout.write
        write("%5d scanned Tomboy notes\n"
              % self.note_count)
        write("%5d K Unicode chars, XML included\n"
              % (self.character_count // 1000))
        if self.from_tomboy_count:
            write("%5d internal links within Tomboy\n"
                  % self.from_tomboy_count)
        if self.from_todo_count:
            write("%5d links incoming from WorkFlowy\n"
                  % self.from_todo_count)
        if self.url_count:
            write("%5d external URLs within Tomboy\n"
                  % self.url_count)

class Location:

    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

    def context(self):
        size = 50
        buffer = codecs.open(self.name, 'r', ENCODING).read()
        if self.start > size:
            prefix = u'…' + buffer[self.start-size:self.start]
        else:
            prefix = buffer[:self.start]
        if self.end < len(buffer) - size:
            suffix = buffer[self.end:self.end+size] + u'…'
        else:
            suffix = buffer[self.end:]
        context = prefix + u'▶' + buffer[self.start:self.end] + u'◀' + suffix
        return context.replace('\n', '\\n')

class Note:
    registry = {}

    def __init__(self, run, input_name):
        self.run = run
        self.input_name = input_name
        note = self.get_raw_document().getroot()
        assert note.tag == 'note', note
        self.title = note.get('title')
        self.run.entertain("Perused " + self.title)

        # Once in daemon mode, the same note may be re-digested many times.
        #assert self.title not in Note.registry

        Note.registry[self.title] = self

        self.date = note.get('date')
        self.template = bool(note.get('template'))
        if self.template:
            return
        self.notebook = note.get('notebook')
        if self.notebook == 'Entretien':
            if self.title == 'FP etc.:t':
                self.notebook = 'FP etc.'
            elif self.title == 'Paxutils:t':
                self.notebook = 'Paxutils'
            elif self.title in ('dkuug:t', 'Recode and thread-safety:t'):
                self.notebook = 'Recode'
            elif self.title in ('python-twyt:t', 'TweeTabs as a project:t',
                                'TweeTabs Reference:t', 'TweeTabs Tutorial:t',
                                'TweeTabs:t'):
                self.notebook = 'TweeTabs'
            elif self.title == 'xxml:t':
                self.notebook = 'xxml'
        if self.notebook is None:
            self.run.report_error(self.title, "Unknown notebook")

    def __cmp__(self, other):
        return locale.strcoll(self.title, other.title)

    def get_fixed_document(self):
        # Only when in XSLT mode.
        self.run.entertain("Reading " + self.title)
        document = self.get_raw_document()
        Fixup().dispatch(document.getroot())
        if self.run.debug:
            print document
        return document

    def get_raw_document(self):
        xslt = xsl_transformer('ingest.xsl')
        return xslt(etree.parse(str(self.input_name)))
