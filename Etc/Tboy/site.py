# -*- coding: utf-8 -*-
# Copyright © 2009 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2009.

__metaclass__ = type
import codecs, os
from lxml import etree
import convert, tools

class Site:
    registry = {}
    styleurl = None
    editor = None

    class __metaclass__(type):

        def __new__(cls, name, bases, dictionary):
            self = type.__new__(cls, name, bases, dictionary)
            if 'host' in dictionary:
                Site.registry[dictionary['host']] = self
            return self

    def __init__(self, run):
        import socket
        self.run = run
        self.host = socket.gethostname()
        self.number_by_math = {}
        self.blog_entries = []
        # Fill in the note registry.
        for note in self.run.each_public_note():
            pass

    def url_directory(self, notebook=None):
        if notebook in self.notebook_info:
            return self.notebook_info[notebook]
        return self.notebook_info[None]

    def output_name(self, note):
        url, directory = self.url_directory(note.notebook)
        return directory + '/' + tools.clean_file_name(note.title) + '.html'

    def is_kept(self, note):
        return not tools.is_ignorable_title(note.title)

    def run_daemon(self):
        import pyinotify

        class Watch(pyinotify.ProcessEvent):

            def process_IN_MOVED_TO(self2, event):
                name = os.path.join(event.path, event.name or '')
                if name.endswith('.note'):
                    self2.convert(name)

            def convert(self2, input_name):
                note = tools.Note(self.run, input_name)
                if self.run.site.is_kept(note):
                    output_name = self.output_name(note)
                    self.maybe_replace(converter.convert(note), output_name)
                    self.decorate_web_pages(output_name)

        converter = convert.Html_converter()
        manager = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(manager, Watch())
        manager.add_watch(tools.TOMBOY_DIR, pyinotify.IN_MOVED_TO)
        try:
            while True:
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
        finally:
            notifier.stop()

    def update_all(self):
        converter = convert.Html_converter()

        # Make an inventory of the output directories.
        self.output_names = set()
        for url, directory in self.notebook_info.itervalues():
            if os.path.isdir(directory):
                for base in os.listdir(directory):
                    if base.endswith('.html'):
                        self.output_names.add(
                                directory + '/' + base.decode(tools.ENCODING))
        url, directory = self.url_directory()
        if os.path.isdir(directory):
            for base in os.listdir(directory):
                if base.endswith('.math'):
                    self.output_names.add(directory + '/' + base)
                    math = file(directory + '/' + base).read().rstrip()
                    self.number_by_math[math] = base[:-5]

        # Translate all public notes.
        for note in sorted(self.run.each_public_note()):
            if self.run.site.is_kept(note):
                self.maybe_replace(converter.convert(note),
                                   self.output_name(note))

        # Create a full note index, another one for recent entries.
        self.run.entertain("Generating note index")
        entries = etree.Element('entries')
        for note in tools.Note.registry.itervalues():
            if self.run.site.is_kept(note):
                url, directory = self.url_directory(note.notebook)
                etree.SubElement(entries, 'entry',
                                 title=tools.pretty_title(note.title),
                                 url=(url + '/'
                                      + os.path.basename(
                                          self.output_name(note))),
                                 group=note.notebook,
                                 date=note.date)
        url, directory = self.url_directory()
        self.maybe_replace(
                self.create_through_xslt(entries, 'full-index.xsl'),
                directory + '/index.html')
        if self.host in ('alcyon', 'phenix'):
            self.maybe_replace(
                    self.create_through_xslt(entries, 'recent-index.xsl'),
                    directory + '/recent.html')

        # Create a blog page.
        if self.host in ('alcyon', 'phenix'):
            import blog
            self.maybe_replace(blog.Blog_maker(self.run).apply(converter),
                               directory + '/blog.html')

        # Clean up.
        for name in sorted(self.output_names):
            self.run.report_action("Removing", name)
            if not self.run.dryrun:
                os.remove(name)

    def create_through_xslt(self, xml, stylesheet):
        xslt = tools.xsl_transformer(stylesheet)
        xml = xslt(xml, styleurl=tools.xsl_boolean(self.styleurl))
        buffer = etree.tostring(xml, encoding='UTF-8')
        if self.run.reformat:
            work = tempfile.mktemp('-tboy-for-tidy')
            codecs.open(work, 'w', tools.ENCODING).write(buffer)
            # FIXME: Enlever le /dev/null
            buffer = (os.popen('tidy 2> /dev/null -q -i -utf8 ' + work)
                      .read()
                      .decode(tools.ENCODING))
            if not buffer:
                sys.exit('tidy -q -i -utf8 %s : empty result' % work)
            os.remove(work)
        return buffer

    def maybe_replace(self, buffer, output_name):
        name = output_name.encode(tools.ENCODING)
        if os.path.exists(name):
            if codecs.open(name, 'r', tools.ENCODING).read() != buffer:
                self.run.report_action("Updating", name)
                if self.run.dryrun:
                    work = tempfile.mktemp('-tboy-for-ediff')
                    codecs.open(work, 'w', tools.ENCODING).write(buffer)
                    os.system('ediff %s %s' % (name, work))
                    os.remove(work)
                else:
                    codecs.open(name, 'w', tools.ENCODING).write(buffer)
            self.output_names.discard(output_name)
        else:
            self.mkdir_recursive(os.path.dirname(name))
            self.run.report_action("Creating", name)
            if not self.run.dryrun:
                codecs.open(name, 'w', tools.ENCODING).write(buffer)

    def decorate_web_pages(self, output_name):
        pass

    def mkdir_recursive(self, directory):
        if not os.path.isdir(directory):
            self.mkdir_recursive(os.path.dirname(directory))
            self.run.report_action("Making directory", directory)
            if not self.run.dryrun:
                os.mkdir(directory)

class Site_Phenix(Site):
    host = 'phenix'
    editor = '/tboy-pop.cgi'
    axiom = 'Semainier:p'
    notebook_info = {
            None: (
                'http://pinard.progiciels-bpi.ca/notes',
                os.path.expanduser('~/fp/web/notes')),
            u"Cabot": (
                'http://cabot.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/cabot/web/notes')),
            u"Edily": (
                'http://edily.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/edily/web/notes')),
            u"FP etc.": (
                'http://fp-etc.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/fp-etc/web/notes')),
            u"Paxutils": (
                'http://paxutils.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/paxutils/web/notes')),
            u"Pymacs": (
                'http://pymacs.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/pymacs/web/notes')),
            u"Recode": (
                'http://recode.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/recode/web/notes')),
            u"Recodec": (
                'http://recodec.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/codes/web/notes')),
            u"TweeTabs": (
                'http://tweetabs.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/tweetabs/web/notes')),
            u"Wdiff": (
                'http://wdiff.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/wdiff/web/notes')),
            u"xxml": (
                'http://xxml.progiciels-bpi.ca/notes',
                os.path.expanduser(
                    '~/entretien/xxml/web/notes')),
            }

    def decorate_web_pages(self, output_name):
        directory = os.path.dirname(output_name)
        os.system('make-web -t -C %s' % directory)

class Site_Alcyon(Site_Phenix):
    host = 'alcyon'
    editor = None

    def is_kept(self, note):
        if not Site_Phenix.is_kept(self, note):
            return False
        for inhibit in ':b', ':p':
            if note.title.endswith(inhibit):
                return False
        return True
