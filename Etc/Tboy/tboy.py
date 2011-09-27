#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2009 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2009-03.

u"""\
Facilitateur pour Tomboy.

Usage: tboy [OPTION]... [NOTE]...

Options générales:
  -v   Être un peu plus volubile
  -n   Mode galop d'essai, les fichiers ne sont pas récrits

Options pour une seule note:
  -b TITRE    Afficher la note ayant ce titre
  -c TITRE    Créer une note avec ce titre, à partir de stdin
  -e TITRE    Extraire le chemin de liens jusqu'à ce titre
  -f TITRE    Trouver le nom du fichier ayant ce titre
  -o OUTPUT   Produire le fichier OUTPUT

Options pour toutes les notes:
  -a              Donner le titre des notes, un par ligne
  -z RÉPERTOIRE   Sauver les notes dans ce répertoire
  -y              Auto-comparaison des notes et de leurs '(ancien)'
  -s              Statistiques (et santé) pour les notes fournies
  -g GABARIT      Chercher dans les notes pour ce gabarit

Options pour un site Web de notes:
  -w   Convertir un sous-ensemble de mes notes en HTML
  -d   Mode daemon, transforme les notes modifiées, au vol
  -r   Reformatter le HTML ou le XML produit
  -x   Préférer XSLT pour le traitement (expérimental)
  -X   Afficher l'arbre XML digéré (avec l'un de -dhpw)

Si -o est utilisée, NOTE doit donner le titre d'une seule note, et OUTPUT
doit alors se terminer par .html, .mt, .pdf, '.rl', .rst, .wiki ou .xml.
Si OUTPUT se termine par .pdf, le .xml correspondant est aussi produit.
L'extension .mt indique le format Movable Type (étape vers Blogger).
Si aucun argument NOTE n'est donné, alors TOMBOY_DIR/*.note est présumé.
"""

__metaclass__ = type
import codecs, locale, os, re, sys
import convert, site, tools

class Main:
    debug = False
    dryrun = False
    error_seen = False
    reformat = False
    tomboy = None
    verbose = False
    xslt = False

    class Fatal(Exception):
        pass

    def main(self, *arguments):
        if not arguments:
            sys.stdout.write(__doc__)
            return

        all = False
        auto_old = False
        create = None
        daemon = False
        display = None
        extract = None
        find = None
        grep = None
        output = None
        save = None
        stats = False
        web = False

        import getopt
        options, arguments = getopt.getopt(arguments,
                                           'ab:c:de:f:g:no:rsvwXxyz:')
        for option, value in options:
            if option == '-a':
                all = True
            elif option == '-b':
                display = value
            elif option == '-c':
                create = value
            elif option == '-d':
                daemon = True
            elif option == '-e':
                extract = value
            elif option == '-f':
                find = value
            elif option == '-g':
                grep = value
            elif option == '-n':
                self.dryrun = True
            elif option == '-o':
                output = value
            elif option == '-r':
                self.reformat = True
            elif option == '-s':
                stats = True
            elif option == '-v':
                self.verbose = True
            elif option == '-w':
                web = True
            elif option == '-X':
                self.debug = True
            elif option == '-x':
                self.xslt = True
            elif option == '-y':
                auto_old = True
            elif option == '-z':
                save = value
        self.arguments = list(arguments)
        if output:
            title = self.arguments.pop(0)
            assert not self.arguments, self.arguments

        locale.setlocale(locale.LC_COLLATE, 'fr_CA.UTF-8')

        try:
            if daemon or extract or output or stats or web:
                import socket
                host = socket.gethostname()
                if host not in site.Site.registry:
                    raise self.Fatal("Unknown site %s" % host)
                self.site = site.Site.registry[host](self)
            if output:
                if output.endswith('.html'):
                    file(output, 'w').write(
                            self.convert(title, convert.Html_converter))
                elif output.endswith('.mt'):
                    file(output, 'w').write(
                            self.convert(title, convert.MT_converter))
                elif output.endswith('.pdf'):
                    xml = output[:-4] + '.xml'
                    file(xml, 'w').write(
                            self.convert(title, convert.Docbook_converter))
                    self.system('dblatex -T simple "' + xml + '"')
                elif output.endswith('.rl'):
                    file(output, 'w').write(
                            self.convert(title, convert.Redmine_converter))
                elif output.endswith('.rst'):
                    file(output, 'w').write(
                            self.convert(title, convert.Rest_converter))
                elif output.endswith('.wiki'):
                    file(output, 'w').write(
                            self.convert(title, convert.Wiki_converter))
                elif output.endswith('.xml'):
                    file(output, 'w').write(
                            self.convert(title, convert.Docbook_converter))
                else:
                    raise self.Fatal("Option -o not using a valid extension")
            if stats:
                if self.diagnose_notes():
                    raise self.Fatal("Errors while sweeping notes")
            if all:
                self.all_titles()
            if create:
                self.create_note(create)
            if display:
                self.display_note(display)
            if find:
                self.find_file(find)
            if grep:
                self.grep_notes(grep)
            if save:
                self.save_notes(save)
            if extract:
                self.extract_path(extract)
            if daemon or web:
                self.site.update_all()
            if auto_old:
                self.auto_compare_old()
            if daemon:
                self.report_action("Waiting", "for note modifications")
                self.site.run_daemon()
        except KeyboardInterrupt:
            pass
        except self.Fatal, exception:
            sys.exit(str(exception))
        if self.error_seen:
            sys.exit(1)

        #titres = sorted(tomboy.GetNoteTitle(note)
        #                for note in tomboy.ListAllNotes())
        #for titre in titres:
        #    print titre
        # Display the contents of the note called Test
        #print tomboy.GetNoteContents(tomboy.FindNote("Personnel"))
        # Add a tag to the note called Test
        #tomboy.AddTagToNote(tomboy.FindNote("Test"), "sampletag")
        # Display the titles of all notes with the tag 'sampletag'
        #for note in tomboy.GetAllNotesWithTag("sampletag"):
        #  print tomboy.GetNoteTitle(note)
        # Print the XML data for the note called Test
        #print tomboy.GetNoteCompleteXml(tomboy.FindNote("Test"))

    def all_titles(self):
        titles = []
        for note in self.each_note():
            titles.append(note.title)
        for title in sorted(titles):
            sys.stdout.write(title + '\n')

    def auto_compare_old(self):
        no_suffix = {}
        ancien_suffix = {}
        old_suffix = {}
        for note in self.each_note():
            if note.title.endswith(' (ancien)'):
                ancien_suffix[note.title[:-9]] = note.input_name
            elif note.title.endswith(' (old)'):
                old_suffix[note.title[:6]] = note.input_name
            else:
                no_suffix[note.title] = note.input_name
        for title in set(ancien_suffix) & set(old_suffix):
            print "Harder:", title, "(ancien/old)"
            del ancien_suffix[title]
            del old_suffix[title]
        for title in set(ancien_suffix) - set(no_suffix):
            print "Spurious:", title, "(ancien)"
            del ancien_suffix[title]
        for title in set(old_suffix) - set(no_suffix):
            print "Spurious:", title, "(old)"
            del old_suffix[title]
        old_suffix.update(ancien_suffix)
        for counter, (title, name1) in enumerate(sorted(old_suffix.items())):
            name2 = no_suffix[title]
            print
            print '=' * 79
            print counter + 1, title
            print '=' * 79
            print
            #print os.popen('gvim -od %s %s' % (name1, name2)).read()
            #print os.popen('diff -u %s %s' % (name1, name2)).read()
            # Utiliser ediff au mieux en filtrant la sortie avec "less -r"
            print os.popen('ediff %s %s' % (name1, name2)).read()
            if counter == 15:
                break

    def create_note(self, title):
        self.preset_tomboy()
        note = self.tomboy.CreateNamedNote(title)
        self.tomboy.SetNoteContents(
                note,
                title + '\n\n' + 'Coucou?\n\n' + sys.stdin.read())
        self.tomboy.AddTagToNote(note, u"commandline")
        self.tomboy.DisplayNote(note)

    def convert(self, title, factory):
        converter = factory()
        for note in self.each_note():
            if note.title == title:
                return converter.convert(note)
        raise self.Fatal("Not found: " + title)

    def display_note(self, title):
        self.preset_tomboy()
        self.tomboy.DisplayNote(self.tomboy.FindNote(title))

    def extract_path(self, goal):
        sweeper = self.build_sweeper()
        path = sweeper.find_path(self.site.axiom, goal)
        if path is None:
            sys.stdout.write("(No path found)\n")
        else:
            for title in path:
                sys.stdout.write(title + '\n')

    def find_file(self, title):
        for note in self.each_note():
            if note.title == title:
                sys.stdout.write(note.input_name + '\n')

    def grep_notes(self, pattern):
        write = sys.stdout.write
        results = []
        for note in self.each_note():
            buffer = codecs.open(note.input_name, 'r', tools.ENCODING).read()
            match = re.search(pattern, buffer)
            if match is not None:
                results.append((note.title, Location(note.input_name,
                                                     match.start(),
                                                     match.end())))
        for title, location in sorted(results):
            write('\n%s: %s\n' % (title, location.context()))

    def save_notes(self, directory):
        self.preset_tomboy()
        if not os.path.isdir(directory):
            os.mkdir(directory)
        os.chdir(directory)
        for note in self.tomboy.ListAllNotes():
            title = self.tomboy.GetNoteTitle(note)
            if tools.is_template_title(title):
                continue
            title = title.replace(':', '')
            if self.verbose:
                sys.stdout.write(title + '\n')
            contents = self.tomboy.GetNoteContents(note)
            codecs.open(title + '.txt', 'w', tools.ENCODING).write(contents)

    def diagnose_notes(self):
        sweeper = self.build_sweeper()
        sweeper.report_errors()
        sweeper.display_stats()
        return bool(sweeper.errors)

    def build_sweeper(self):
        sweeper = tools.Sweeper(self, self.each_note())
        sweeper.mark(self.site.axiom)
        return sweeper

    def each_public_note(self):
        for note in self.each_note():
            if not (note.template or tools.is_ignorable_title(note.title)):
                yield note

    def each_note(self):
        if tools.Note.registry:
            for note in tools.Note.registry.itervalues():
                yield note
        else:
            for name in self.note_file_names():
                note = tools.Note(self, name)
                if not note.template:
                    yield note

    def note_file_names(self):
        if self.arguments:
            return self.arguments
        import glob
        return glob.glob('%s/*.note' % tools.TOMBOY_DIR)

        #self.preset_tomboy()
        #for note in self.tomboy.ListAllNotes():
        #    title = self.tomboy.GetNoteTitle(note)
        #    if title.startswith("Modèle de bloc-notes "):
        #        continue
        #    if title.endswith(" Notebook Template"):
        #        continue
        #    yield title

    def preset_tomboy(self):
        if self.tomboy is None:
            import dbus
            self.tomboy = dbus.Interface(
                dbus.SessionBus().get_object(
                    'org.gnome.Tomboy',
                    '/org/gnome/Tomboy/RemoteControl'),
                'org.gnome.Tomboy.RemoteControl')

    def system(self, command):
        self.entertain('# ' + command)
        status = os.system(command)
        if status:
            raise self.Fatal("* Command %r returned %r"
                             % (command, divmod(status, 256)))

    def entertain(self, message):
        if self.verbose:
            sys.stderr.write(message + '\n')

    def report_action(self, action, name):
        text = action + ' ' + name
        if self.dryrun:
            text = '(not) ' + text
        sys.stderr.write(text + '\n')

    def report_error(self, title, diagnostic):
        sys.stderr.write('* %s: %s\n' % (title, diagnostic))
        self.error_seen = True
