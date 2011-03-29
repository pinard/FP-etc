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
    title = title.lower()
    if title.startswith(u"modèle de bloc-notes "):
        return True
    if title.endswith(u" notebook template"):
        return True
    return title in (u"nouveau modèle de note",
                     u"démarrer ici",
                     u"utilisation des liens dans tomboy",
                     u"new note template",
                     u"start here",
                     u"using links in tomboy")

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
        yield buffer[start:end], Location(name, start, end)
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

    def __init__(self, run, notes):
        self.run = run
        self.arrows = {}
        self.realtitle = {}
        self.errors = []
        for note in notes:
            self.digest(codecs.open(note.input_name, 'r', ENCODING).read(),
                        note.input_name)
        self.marked = set()

    def digest(self, buffer, name):
        for fragment, location in each_xml_tag('title', buffer, name):
            break
        else:
            self.run.report_error(name, "No title")
            return
        title = fragment.lower()
        if title not in self.arrows:
            self.realtitle[title] = fragment
            self.arrows[title] = []
        for fragment, location in each_regexp(' \t', buffer, name):
            self.errors.append((title, u"Space then tab", location))
        for fragment, location in each_xml_tag('link:broken', buffer, name):
            self.errors.append((title, u"Broken link", location))
        for fragment, location in each_xml_tag('link:internal', buffer, name):
            internal = fragment.lower()
            for fragment, _ in each_xml_tag('monospace', internal, None):
                internal = fragment
                break
            self.arrows[title].append((internal, location))

    def mark(self, ancestor):
        self.marked.add(ancestor.lower())
        for child, location in self.arrows[ancestor.lower()]:
            if child in self.arrows:
                if not child in self.marked:
                    self.mark(child)
            else:
                self.errors.append((ancestor, u"Dangling link", location))

    def find_path(self, start, goal):
        return self.find_path_recursive(start.lower(), goal.lower(), [])

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
                                       .decode('UTF-8').lower())
                    else:
                        todo_buffer = ''
                if title.lower() not in todo_buffer:
                    self.errors.append((title, u"Unreachable", None))
        for title, diagnostic, location in sorted(self.errors):
            if location is not None:
                diagnostic += ' (' + location.context() + ')'
            self.run.report_error(self.realtitle[title], diagnostic)

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
    canonical = {}

    def __init__(self, run, input_name):
        self.run = run
        self.input_name = input_name
        note = self.get_raw_document().getroot()
        assert note.tag == 'note', note
        self.title = note.get('title')
        self.run.entertain("Perused " + self.title)

        # Once in daemon mode, the same note may be re-digested many times.
        #assert self.title not in Note.registry
        #assert self.title.lower() not in Note.canonical

        Note.registry[self.title] = self
        Note.canonical[self.title.lower()] = self.title

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
