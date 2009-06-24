# Web generation services for distribution files.
# -*- coding: utf-8 -*-
# Copyright © 2000, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2000.

u"""\
Web page generation tool for many of my own software projects.
"""

import os, re, sys, time
import cPickle as pickle

class error(Exception): pass

#def generate(top, name, index, mode):
#    if name is not None:
#        # Jail NAME below the top directory.
#        fragments = name.split('/')
#        while fragments and not fragments[0]:
#            del fragments[0]
#        while '..' in fragments:
#            fragments.remove('..')
#        name = '/'.join(fragments)
#        # Be strict about when the `archives' mode is usable.
#        if mode == 'archives':
#            mode = None
#        if 'archives' in fragments:
#            mode = 'archives'
#        # Be strict about when the `folders' mode is usable.
#        if mode == 'folders':
#           mode = None
#        if 'courriel' in fragments:
#            mode = 'folders'
#        elif fragments and fragments[-1] == 'COURRIEL':
#            mode = 'folders'
#    # Dispatch to the appropriate formatting class.
#    if name is None:
#        if mode == 'archives':
#            html = Html_Archives(top)
#        elif mode == 'folders':
#            html = Html_Folders(top)
#        else:
#            html = Html_File_List(top)
#    elif os.path.isdir(os.path.join(top, name)):
#        html = Html_File_List(top, name)
#    elif os.path.isfile(os.path.join(top, name)):
#        if mode == 'folders':
#            if index is None:
#                html = Html_Summary(top, name)
#            else:
#                html = Html_Message(top, name, index)
#        else:
#            base = os.path.basename(name)
#            if base == 'NEWS':
#                html = Html_Verbatim(top, name,
#                        u"NEWS - History of user-visible changes")
#            #elif base == 'README':
#            #    html = Html_Allout(top, name,
#            #            "README - Introductory notes")
#            elif base == 'THANKS':
#                html = Html_Thanks(top, name,
#                        u"THANKS - People who have contributed")
#            elif base == 'TODO':
#                html = Html_Verbatim(top, name,
#                        u"TODO - Things still to be done")
#            else:
#                extension = os.path.splitext(base)[1]
#                if extension == '.all':
#                    html = Html_Allout(top, name)
#                elif extension == '.html':
#                    html = Html_Html(top, name)
#                else:
#                    html = Html_File(top, name, mode)
#    else:
#        html = Html_Buffer(top, name)
#    return (html.html_title(), html.html_body(), html.html_buttons())

# Base classes.

class Html:
    title = None
    meta = None
    body = None
    up = None
    left = None
    right = None

    def __init__(self, top, name):
        self.top = top
        self.name = name
        if name:
            up = os.path.dirname(self.name)
            if up != name:
                self.up = up

    def __str__(self):
        return self.html_prefixe() + self.html_body() + self.html_suffixe()

    def html_title(self):
        if self.title:
            return enhanced(self.title)
        return ''

    def html_meta(self):
        return self.meta or ''

    def html_body(self):
        return self.body or ''

    def html_prefixe(self):
        fragments = []
        write = fragments.append
        title = self.html_title()
        write('<html>\n'
              ' <head>\n'
              '  <meta http-equiv="Content-type"'
              ' content="text/html; charset=UTF-8" />\n'
              '  <title>%s</title>\n'
              '  <link href="/gabarit.css" rel="stylesheet"'
              ' type="text/css" />\n'
              '  <script src="/gabarit.js" type="text/javascript" />\n'
              ' </head>\n'
              ' <body>\n'
              % title)
        write(self.html_buttons(title))
        write(self.html_ruler())
        return ''.join(fragments)

    def html_suffixe(self):
        fragments = []
        write = fragments.append
        write(self.html_ruler())
        write(self.html_buttons(None))
        write(' </body>\n'
              '</html>\n')
        return ''.join(fragments)

    def html_buttons(self, title):
        fragments = []
        write = fragments.append
        write('  <table class=navigation>\n'
              '   <tr>\n')
        write('    <td class=left>\n')
        if self.left is not None:
            write('  <a href="/%s">'
                  '<img id="previous" alt="Previous" src="/flèche-gauche-1.png"'
                  ' onmouseover="previousOver()" onmouseout="previousOut()" />'
                  '</a>\n'
                  % self.left)
        else:
            write('  <img src="/flèche-gauche-0.png" />\n')
        if self.up is not None:
            write('  <a href="/%s">'
                  '<img id="up" alt="Up" src="/flèche-haut-1.png"'
                  ' onmouseover="upOver()" onmouseout="upOut()" />'
                  '</a>\n'
                  % self.up)
        else:
            write('  <img src="/flèche-haut-0.png" />\n')
        write('    </td>\n')
        write('    <td class=title>')
        if title is not None:
            write(enhanced(title))
        write('</td>\n')
        write('    <td class=right>\n')
        if self.right is not None:
            write('  <a href="/%s">'
                  '<img id="next" alt="Next" src="/flèche-droite-1.png"'
                  ' onmouseover="nextOver()" onmouseout="nextOut()" />'
                  '</a>\n'
                  % self.right)
        else:
            write('  <img src="/flèche-droite-0.png" />\n')
        write('    </td>\n')
        write('   </tr>\n'
              '  </table>\n')
        write('\n')
        return ''.join(fragments)

    @staticmethod
    def html_ruler():
        return '  <hr class=ruler />\n'

    def file_data(self, names):
        data = []
        for name in names:
            full_name = os.path.join(self.top, name)
            try:
                name = unicode(name)
            except UnicodeError:
                name = unicode(name, 'ISO-8859-1')
            date = ('%d-%.2d-%.2d'
                    % time.localtime(os.path.getmtime(full_name))[:3])
            size = os.path.getsize(full_name)
            data.append((name, date, size))
        return data

class Html_lines_read(Html):

    def __init__(self, top, name, title=None, buffer=None):
        Html.__init__(self, top, name)
        if buffer is None:
            try:
                self.lines = unicode_readlines(os.path.join(top, name))
            except IOError, exception:
                raise error("Page not found (%s)" % exception.strerror)
        else:
            self.lines = buffer.splitlines(True)
        self.title = title

    def allout_title(self):
        if self.lines:
            if self.lines[0].startswith('* '):
                title = self.lines[0][2:].strip()
                title = re.sub('-\\*- .* -\\*-', '', title, 1)
                title = re.sub('[ \t]allout', '', title, 1)
                return title.strip()
        return self.title

# Make HTML showing an error message.

class Html_Error(Html):
    title = u"Error report"

    def __init__(self, top, name, diagnostic):
        Html.__init__(self, top, name)
        self.diagnostic = diagnostic

    def html_body(self):
        return error_body(self.diagnostic)

# Make HTML from in-memory contents.

class Html_Buffer(Html_lines_read):

    def __init__(self, top, buffer, title=None):
        Html_lines_read.__init__(self, top, None, title=title, buffer=buffer)

# Make HTML listing all existing archives.

class Html_Archives(Html):

    def __init__(self, top, name='archives'):
        Html.__init__(self, top, name)

    def html_title(self):
        return u"Archives"

    def html_body(self):
        names = []
        latest = stable = usoft = None
        items = []
        for name in os.listdir(os.path.join(self.top, self.name)):
            for extension in '.tgz', '.tar.gz', '.tar.bz2', '.zip':
                if name.endswith(extension):
                    base = name[:-len(extension)]
                    match = re.match('.*?([0-9]+)\\.([0-9]+)([a-z])$', base)
                    if match:
                        items.append(((-int(match.group(1)),
                                       -int(match.group(2)),
                                       -(ord(match.group(3)) - ord('a') + 1)),
                                      name))
                        break
                    match = re.match('.*?([0-9]+)\\.([0-9]+)\\.([0-9]+)$', base)
                    if match:
                        items.append(((-int(match.group(1)),
                                       -int(match.group(2)),
                                       -int(match.group(3))),
                                      name))
                        break
                    match = re.match('.*?([0-9]+)\\.([0-9]+)$', base)
                    if match:
                        items.append(((-int(match.group(1)),
                                       -int(match.group(2)),
                                       0),
                                      name))
                        break
                    match = re.match('.*?([0-9]+)$', base)
                    if match:
                        items.append(((-int(match.group(1)),
                                       0,
                                       0),
                                      name))
                        break
                    items.append(((0, 0, 0), name))
                    break
            else:
                if not name.endswith('~'):
                    names.append(name)
                    if name.endswith('.exe'):
                        usoft = name
        names.sort()
        items.sort()
        names = [name for version, name in items] + names
        for (major, minor, micro), name in items:
            if latest is None:
                latest = name
            if micro == 0:
                stable = name
                break
        # REVOIR!
        return self.file_data(names), latest, stable, usoft

# Make HTML listing existing folders.

class Html_Folders(Html):

    def __init__(self, top):
        Html.__init__(self, top, None)

    def html_title(self):
        return u"Email folders"

    def html_body(self):
        stack = ['.']
        results = []
        previous = None
        while stack:
            directory = stack.pop()
            all = 'courriel' in directory.split('/')
            bases = os.listdir(os.path.join(self.top, directory))
            bases.sort()
            directories = []
            names = []
            for base in bases:
                if base.endswith('~'):
                    continue
                name = os.path.join(directory, base)
                if os.path.isdir(os.path.join(self.top, name)):
                    directories.append(name)
                    continue
                if ((all or base.find('COURRIEL') >= 0)
                    and os.path.isfile(os.path.join(self.top, name))):
                    if directory != previous:
                        previous = directory
                    names.append(os.path.normpath(name))
            directories.reverse()
            stack += directories
            if names:
                results.append(self.file_data(names))
        return results

# Make HTML summarizing a single Babyl or Mailbox folder.

class Html_Summary(Html):

    def __init__(self, top, name):
        Html.__init__(self, top, name)
        from Etc import folder
        self.messages = folder.folder(os.path.join(top, name), strip201=True)

    def html_title(self):
        return u"%s (index)" % self.name

    def html_body(self):
        try:
            from email.utils import parseaddr
        except ImportError:
            from email.Utils import parseaddr
        fragments = []
        write = fragments.append
        write('  <table class=index align=center>\n'
              '   <tr>\n'
              u'    <th class=no>Nº</th>\n'
              '    <th class=from>From</th>\n'
              '    <th class=subject>Subject</th>\n'
              '   </tr>\n')
        index = 0
        for index in range(len(self.messages)):
            message = self.messages.message_headers(index)
            user, email = parseaddr(message.get('From'))
            if user:
                user = decoded_header(user)
            else:
                user = email
            subject = message.get('Subject')
            if subject:
                subject = decoded_header(subject)
            if not subject:
                subject = "(None)"
            write('   <tr>\n'
                  '    <td class=no>%d</td>\n'
                  '    <td class=from><a href="mailto:%s">%s</a></td>\n'
                  '    <td class=subject><a href="/%s/%d">%s</a></td>\n'
                  '   </tr>\n'
                  % (index + 1, email,
                     enhanced(user[:20]), enhanced(self.name),
                     index + 1, enhanced(subject)))
            index += 1
        write('  </table>\n')
        return ''.join(fragments)

    def html_buttons(self, title):
        self.up = os.path.dirname(self.name)
        if len(self.messages) > 0:
            self.right = self.name + '/1'
        return Html.html_buttons(self, title)

# Make HTML out of a selected message from within a folder.

class Html_Message(Html):

    def __init__(self, top, name, index, buffer_cache=None):
        Html.__init__(self, top, name)
        self.index = index
        self.buffer_cache = buffer_cache
        from Etc import folder
        messages = folder.folder(os.path.join(top, name), strip201=True)
        if not 0 <= index < len(messages):
            raise error(u"No such message!")
        self.count = len(messages)
        self.headers = messages.message_headers(index)
        self.body = messages.message_body(index)

    def html_title(self):
        return u"%s (%d/%d)" % (self.name, self.index + 1, self.count)

    def html_body(self):
        try:
            from email.utils import parseaddr
        except ImportError:
            from email.Utils import parseaddr

        class RenderError(error): pass

        def render_recursive(
                message, noraise=True,
                headers=['Date', 'From', 'Subject', 'To', 'Cc']):
            if headers:
                if headers is True:
                    pairs = message.items()
                else:
                    pairs = []
                    for field in headers:
                        value = message.get(field)
                        if value:
                            pairs.append((field, value))
            else:
                pairs = None
            fragments = []
            write = fragments.append
            if pairs:
                write('  <table class=email>\n')
                for field, value in pairs:
                    if field in ('From', 'To'):
                        user, email = parseaddr(value)
                        if user:
                            value = decoded_header(user)
                            if email:
                                value += ' <%s>' % email
                        else:
                            value = email
                    elif field == 'Date':
                        try:
                            from email.utils import parsedate_tz
                        except ImportError:
                            from email.Utils import parsedate_tz
                        date = parsedate_tz(value)
                        if date is not None:
                            date = list(date[:5])
                            if date[0] < 70:
                                date[0] += 2000
                            elif date[0] < 100:
                                date[0] += 1900
                            value = '%.4d-%.2d-%.2d %.2d:%.2d' % tuple(date)
                    else:
                        value = decoded_header(value)
                    write('   <tr>\n'
                          '    <td class=field>%s: </td>\n'
                          '    <td class=value>%s</td>\n'
                          '   </tr>\n'
                          % (enhanced(field), enhanced(value)))
                write('  </table>\n')
            try:
                access_type = message.get_param('access-type')
                if access_type == 'x-mutt-deleted':
                    raise RenderError(u"Deleted in Mutt.")
                content_type = message.get_content_type()
                content_maintype = message.get_content_maintype()
                if message.is_multipart():
                    payloads = []
                    counter = 0
                    while True:
                        try:
                            payloads.append(message.get_payload(counter))
                        except IndexError:
                            break
                        counter += 1
                    if content_type == 'multipart/alternative':
                        text = None
                        for payload in payloads:
                            try:
                                text = render_recursive(payload, noraise=False)
                            except RenderError:
                                break
                        if text is None:
                            raise RenderError(
                                "Aucune entité retenue dans: %s" % content_type)
                        write(text)
                    elif content_type == 'message/delivery-status':
                        write('<hr class=ruler />\n')
                        for payload in payloads:
                            write(render_recursive(payload, headers=True))
                    elif content_type == 'message/rfc822':
                        write('<hr class=ruler />\n')
                        for payload in payloads:
                            write(render_recursive(payload))
                    elif content_maintype == 'multipart':
                        for payload in payloads:
                            write(render_recursive(payload))
                    else:
                        raise RenderError(
                            u"Multi-entité inconnue: %s" % content_type)
                else:
                    if (content_type in ('application/msword',
                                         'application/pdf')
                            and self.buffer_cache is not None):
                        index = self.buffer_cache.save(
                                payload_of(message, raw=True),
                                content_type, 3600)
                        write('  <a class=attachment href="/+%s">%s</a>\n'
                              % (index,
                                 message.get_param('name', content_type)))
                    elif content_type == 'application/octet-stream':
                        write('<pre>\n%s</pre>\n'
                              % enhanced(payload_of(message)))
                    elif content_type == 'application/pgp-signature':
                        pass
                    elif (content_maintype == 'image'
                            and self.buffer_cache is not None):
                        index = self.buffer_cache.save(
                            payload_of(message, raw=True),
                            content_type)
                        write('  <img src="/+%s" />\n' % index)
                    elif content_type == 'message/delivery-status':
                        write('<pre>\n%s</pre>\n'
                              % enhanced(payload_of(message)))
                    elif content_type == 'message/rfc822':
                        write('<pre>\n%s</pre>\n'
                              % enhanced(payload_of(message)))
                    elif content_type == 'text/enriched':
                        write(from_text_enriched(payload_of(message)))
                    elif content_type == 'text/html':
                        write(from_text_html(payload_of(message)))
                    elif content_type == 'text/plain':
                        write(from_text_plain(payload_of(message)))
                    elif content_type == 'text/x-patch':
                        write('<pre>\n%s</pre>\n'
                              % enhanced(payload_of(message)))
                    else:
                        raise RenderError(u"Entité inconnue: %s"
                                          % content_type)
            except RenderError, exception:
                if not noraise:
                    raise
                write(error_body(str(exception)))
            return ''.join(fragments)

        from email import message_from_string
        return render_recursive(
                message_from_string(str(self.headers) + self.body))

    def html_buttons(self, title):
        if self.index > 0:
            self.left = self.name + '/%d' % self.index
        self.up = self.name
        if self.index < self.count - 1:
            self.right = self.name + '/%d' % (self.index + 2)
        return Html.html_buttons(self, title)

# Make HTML listing the directory hierarchy.

class Html_File_List(Html):

    def __init__(self, top, name='', dots=False):
        Html.__init__(self, top, name)
        self.name = name
        self.dots = dots

    def html_title(self):
        if self.name:
            return self.name + '/'
        return '/'

    def html_body(self):
        fragments = []
        write = fragments.append
        counter = 0
        write('  <table class=directory align=center>\n'
              '   <tr>\n'
              u'    <th class=no>Nº</th>\n'
              '    <th class=folder>Folder</th>\n'
              '    <th class=date>Date</th>\n'
              '    <th class=size>Size</th>\n'
              '   </tr>\n')
        directory = self.name or '.'
        directories = []
        names = []
        for base in sorted(os.listdir(os.path.join(self.top, directory))):
            if not self.dots and base.startswith('.'):
                continue
            if base.endswith('~'):
                continue
            if base.endswith('.swp'):
                continue
            name = os.path.normpath(os.path.join(directory, base))
            if os.path.isdir(os.path.join(self.top, name)):
                if (base in ('.git', '.svn', 'RCS', 'CVS',
                             'archives', 'build', 'web')
                        or base.startswith('build-')
                        or base.startswith(u'Prépare-')):
                    continue
                directories.append(name + '/')
            elif os.path.isfile(os.path.join(self.top, name)):
                names.append(name)
        names = directories + names
        if names:
            for name, date, size in self.file_data(names):
                if name.endswith('/'):
                    base = os.path.basename(name[:-1]) + '/'
                else:
                    base = os.path.basename(name)
                counter += 1
                write('   <tr>\n'
                      '    <td class=no>%d</td>\n'
                      '    <td class=folder><a href="/%s">%s</a></td>\n'
                      '    <td class=date>%s</td>\n'
                      '    <td class=size>%d</td>\n'
                      '   </tr>\n'
                      % (counter, name, base, date, size))
        write('  </table>\n')
        return ''.join(fragments)

# Make HTML out of a selected file.

class Html_File(Html):

    def __init__(self, top, name, mode=None):
        Html.__init__(self, top, name)
        self.mode = mode

    def html_title(self):
        return self.name

    def html_body(self):
        try:
            if self.mode == 'monochrome':
                return self.html_body_through_enscript()
            if self.mode == 'coloured':
                return self.html_body_through_vim()
            return self.html_body_through_none()
        except IOError, exception:
            raise error("Page not found (%s)" % exception.strerror)

    def html_body_through_none(self):
        fragments = []
        write = fragments.append
        write('<pre>\n')
        for line in unicode_readlines(os.path.join(self.top, self.name)):
            write(line.replace('&', '&amp;').replace('<', '&lt;'))
        write('</pre>\n')
        return ''.join(fragments)

    def html_body_through_enscript(self):
        fragments = []
        write = fragments.append
        command = ('enscript 2>/dev/null -p- -G -E --language=html %s'
                   % os.path.join(self.top, self.name))
        before = True
        for line in unicode_readlines(os.popen(command)):
            if before:
                if line != '<PRE>\n':
                    continue
                before = False
            write(line)
            if line == '</PRE>\n':
                break
        return ''.join(fragments)

    def html_body_through_vim(self):
        fragments = []
        write = fragments.append
        import tempfile
        work = tempfile.mktemp()
        # `-u NONE' ne fonctionne pas.
        command = ('/usr/bin/vim -fNn -u /dev/null >/dev/null 2>/dev/null'
                   ' -c \'set background=light\' -c \'syntax on\''
                   ' -c TOhtml -c \'wq! %s\' -c q %s'
                   % (work, os.path.join(self.top, self.name)))
        os.system(command)
        before = True
        for line in unicode_readlines(work):
            if before:
                if line != '<pre>\n':
                    continue
                before = False
            write(line)
            if line == '</pre>\n':
                break
        os.remove(work)
        return ''.join(fragments)

    def html_buttons(self, title):
        fragments = []
        write = fragments.append
        write('<form action=\"%s\">\n'
              u"Redisplay this file \n"
              % self.name)
        value = u"flat"
        if self.mode is not None and self.mode != value:
            write(' <input type=submit name="mode" value="%s">'
                  u" (not highlighted),\n" % value)
        value = u"monochrome"
        if self.mode != value:
            write(' <input type=submit name="mode" value="%s">'
                  u" (through Enscript),\n" % value)
        value = u"coloured"
        if self.mode != value:
            write(' <input type=submit name="mode" value="%s">'
                  u" (through Vim),\n" % value)
        write(u" or go back to the"
              u" <a href=\"/\">list of project files</a>.\n"
              '</form>\n')
        if title:
            write('  <h1>%s</h1>\n' % title)
        return ''.join(fragments)

# Make HTML out a file, taken almost verbatim.

class Html_Verbatim(Html_lines_read):

    def html_title(self):
        if self.lines:
            return self.allout_title() or self.lines[0].strip()
        return self.title

    def html_body(self):
        fragments = []
        write = fragments.append
        write('<pre>\n')
        for line in self.lines:
            write(enhanced(line))
        write('</pre>\n')
        return ''.join(fragments)

# Make HTML out of an `allout' outline file.

class Html_Allout(Html_lines_read):

    def html_title(self):
        return self.allout_title()

    def html_body(self):
        if not self.lines:
            return ''
        fragments = []
        write = fragments.append
        self.element = None
        self.level = -1
        self.margin = '  '
        for line in self.lines[1:]:
            if line[0] == '*':
                # Title is unexpected!
                break
            match = re.match('\\.( *)[-*+:;.,@] (.+)', line)
            if match:
                self.maybe_stop('p', write)
                self.maybe_stop('pre', write)
                self.header(len(match.group(1)), match.group(2), write)
                continue
            if line == '\n':
                self.maybe_stop('p', write)
                write(line)
                continue
            if line.find('\t') >= 0:
                self.maybe_start('pre', write)
                if line[:1] == '\t':
                    line = line[1:]
                write(enhanced(line, clean=True))
                continue
            if line[:len(self.margin)] == self.margin:
                line = line[len(self.margin):]
            if line.endswith('----\n'):
                continue
            if line.find('   ') >= 0:
                self.maybe_start('pre', write)
            else:
                self.maybe_start('p', write)
            write(enhanced(line, clean=True))
        self.maybe_stop('p', write)
        self.maybe_stop('pre', write)
        while self.level >= 0:
            self.level -= 1
            self.margin = ' ' * (self.level+3)
            write('%s</ol>\n' % self.margin)
        return ''.join(fragments)

    def header(self, goal, title, write):
        while self.level < goal:
            write('%s<ol class=level%d>\n' % (self.margin, self.level + 1))
            self.level += 1
            self.margin = ' ' * (self.level+3)
        while self.level > goal:
            self.level -= 1
            self.margin = ' ' * (self.level+3)
            write('%s</ol>' % self.margin)
        write('%s<li><h%d>%s</h%d>'
              % (self.margin, self.level+2,
                 enhanced(title, clean=True), self.level+2))

    def maybe_start(self, tag, write):
        if tag != self.element:
            if self.element:
                write('</%s>\n' % self.element)
            write('%s<%s>\n' % (self.margin, tag))
            self.element = tag

    def maybe_stop(self, tag, write):
        if tag == self.element:
            write('</%s>\n' % self.element)
            self.element = None

# Make HTML out of a file already holding HTML.

class Html_Html(Html_lines_read):

    def html_title(self):
        if self.title:
            return self.title
        title = None
        for line in self.lines:
            position = line.find('<title>')
            if position >= 0:
                title = line[position+7:]
                line = ''
            position = line.find('<TITLE>')
            if position >= 0:
                title = line[position+7:]
                line = ''
            if title is not None:
                title += line
                position = title.find('</title>')
                if position >= 0:
                    title = title[:position]
                    break
                position = title.find('</TITLE>')
                if position >= 0:
                    title = title[:position]
                    break
            elif body_start_tag_in_line(line):
                break
        if title:
            return title.strip()
        return ''

    def html_meta(self):
        meta = ''
        for line in self.lines:
            position = line.find('<meta')
            if position >= 0:
                meta = line[position:]
                line = ''
            position = line.find('<META')
            if position >= 0:
                meta = line[position:]
                line = ''
            if meta:
                meta += line
                position = meta.find('>', 5)
                if position >= 0:
                    meta = meta[:position+1]
                    break
            elif body_start_tag_in_line(line):
                break
        return meta

    def html_body(self):
        fragments = []
        write = fragments.append
        lines = []
        before = True
        for line in self.lines:
            if before:
                if body_start_tag_in_line(line):
                    before = False
            else:
                if body_end_tag_in_line(line):
                    break
                write(line)
        return ''.join(fragments)

def body_start_tag_in_line(line):
    return ('<body>' in line or '<BODY>' in line
            or '<body ' in line or '<BODY ' in line)

def body_end_tag_in_line(line):
    return '</body>' in line or '</BODY>' in line

# Make HTML out of a `THANKS' file.

class Html_Thanks(Html_lines_read):

    def html_body(self):

        def produce_row():
            if name is None:
                write(u'  <p> </p>\n'
                      '  <table align=center border=2>\n'
                      '   <tr>\n'
                      '    <th>Contributor</th>\n'
                      '    <th>Email address</th>\n'
                      '   </tr>\n')
                return
            write('   <tr>\n')
            if url:
                write('    <td><a href="%s">%s</a></td>\n'
                      '    <td>%s</td>\n' % (url, name, mailto or ''))
            else:
                write('    <td>%s</td>\n' % name)
                if mailto:
                    write('    <td><a href="mailto:%s">%s</a></td>\n'
                          % (mailto, mailto))
                else:
                    write('    <td></td>\n')
            write('   </tr>\n')

        fragments = []
        write = fragments.append
        prefix = True
        within_p = False
        name = mailto = url = None
        for line in self.lines:
            # Transform the introductory paragraphs.
            if prefix:
                if line == '\n':
                    if within_p:
                        write('  </p>\n')
                        within_p = False
                    continue
                if '\t' in line or line.find('   ') >= 0:
                    if within_p:
                        write('  </p>\n')
                    prefix = False
                else:
                    if not within_p:
                        write('  <p>\n')
                        within_p = True
                    write('   %s' % enhanced(line, clean=True))
                    continue
            # Make a table with the remainder of the file.
            if line == '\n' or line.startswith(' '):
                continue
            fields = line.rstrip().split('\t')
            if fields[0]:
                produce_row()
                name = fields[0]
                del fields[0]
                mailto = url = None
            while fields and not fields[0]:
                del fields[0]
            if not fields:
                continue
            text = ' '.join(fields)
            if text.startswith('http:'):
                url = text
            else:
                mailto = text
        if name is not None:
            produce_row()
            write('  </table>\n')
        return ''.join(fragments)

# Reformatters towards HTML for some Content-Types.

enriched_map = {
        'bold': ('<b>', '</b>'),
        'italic': ('<i>', '</i>'),
        'fixed': ('<tt>', '</tt>'),
        'smaller': ('<small>', '</small>'),
        'bigger': ('<big>', '</big>'),
        'underline': ('<u>', '</u>'),
        'center': ('<div align=center>', '</div>'),
        'flushright': ('<div class=flushright>', '</div>'),
        'flushleft': ('<div class=flushleft>', '</div>'),
        'flushboth': ('<div class=flushboth>', '</div>'),
        'nofill': ('<pre>', '</pre>'),
        'indent': ('<div class=indent>', '</div>'),
        'indentright': ('<div class=indentright>', '</div>'),
        'excerpt': ('<div class=excerpt>', '</div>'),
        }

def from_text_enriched(buffer):
    fragments = []
    write = fragments.append
    import re
    pattern = re.compile(
            '<(?P<closing>/)?(?P<tag>[-A-Za-z0-9]+)>'
            '(?:<param>(?P<param>[^<]*)</param>)?'
            '|(?P<charent>&[A-Za-z0-9]+;)'
            '|(?P<newline>[\r\n]+)(?P<margin>[ \t]*)'
            '|<<')
    position = 0
    while True:
        match = pattern.search(buffer, position)
        if match is None:
            if position < len(buffer):
                write(enhanced(buffer[position:]))
            return ''.join(fragments)
        start, end = match.span()
        if start > position:
            write(enhanced(buffer[position:start]))
        position = end
        text = match.group('tag')
        if text is not None:
            tag = text.lower()
            closing = match.group('closing') is not None
            pair = enriched_map.get(tag)
            if pair is not None:
                write(pair[closing])
                continue
            if tag == 'color':
                if closing:
                    write('</font>')
                else:
                    param = match.group('param')
                    split = param.split(',')
                    if len(split) == 3:
                        param = '#' + split[0][:2] + split[1][:2] + split[2][:2]
                    else:
                        param = None
                    if param is None:
                        write('<font>')
                    else:
                        write('<font color="%s">' % param)
                continue
            if tag == 'fontfamily':
                if closing:
                    write('</font>')
                else:
                    param = match.group(5)
                    if param is None:
                        write('<font>')
                    else:
                        write('<font face="%s">' % param)
                continue
            if tag == 'paraindent':
                # REVOIR: param == 'out'
                continue
        text = match.group('charent')
        if text is not None:
            write(text)
            continue
        text = match.group('newline')
        if text is not None:
            text = text.replace('\r', '')
            if len(text) == 1:
                write('\n')
            else:
                write('<br>\n' * (len(text) - 1))
            text = match.group('margin')
            if text:
                write(text.expandtabs().replace(' ', u'\xa0'))
            continue
        text = match.group()
        if match.group() == '<<':
            write('<')
            continue
        write(enhanced(match.group()))

def from_text_html(buffer):
    return buffer

def from_text_plain(buffer):
    margin_map = {'': 0}
    used_levels = set()
    max_levels = 30

    def level_of(margin):
        if margin not in margin_map:
            level = (len(margin) + len(margin.replace(' ', ''))) % max_levels
            if len(used_levels) < max_levels:
                while level in used_levels:
                    level = (level + 1) % max_levels
                used_levels.add(level)
            margin_map[margin] = level
        return margin_map[margin]

    def handle_block(lines):
        DEBUG = False
        # Two blocks may be filled together only if not separated by white
        # lines and if they share a common left margin.
        if DEBUG:
            print '--->'
            for counter, line in enumerate(lines):
                print '%d.' % counter, repr(line)
            print '--------------------------------------------------'
        current_margin = None
        current_level = 0
        verbatim = False
        white = False
        for counter, line in enumerate(lines):
            text = (line.replace('>', ' ')
                     .replace('|', ' ')
                     .replace('%', ' ')
                     .replace(':', ' ')
                     .lstrip())
            if is_verbatim(text):
                verbatim = True
            if not text:
                if current_margin is not None:
                    if verbatim:
                        write('<pre class=level%d>\n' % current_level)
                        write_verbatim_block(lines[start:counter])
                        write('</pre>\n')
                    elif recursive is None:
                        write('<pre class=level%d>\n' % current_level)
                        write_filled_block(lines[start:counter])
                        write('</pre>\n')
                    else:
                        handle_block(lines[start:counter])
                    current_margin = None
                    current_level = 0
                    verbatim = False
                    white = True
                continue
            margin = line[:len(line) - len(text)]
            if current_margin is None:
                if white:
                    write_whiteline()
                    white = False
                current_margin = margin
                current_level = level_of(margin)
                start = counter
                recursive = None
                continue
            if margin == current_margin:
                continue
            if margin.startswith(current_margin):
                if recursive is None and not verbatim:
                    recursive = counter
                continue
            if verbatim:
                write('<pre class=level%d>\n' % current_level)
                write_verbatim_block(lines[start:counter])
                write('</pre>\n')
            elif recursive is None:
                write('<pre class=level%d>\n' % current_level)
                write_filled_block(lines[start:counter])
                write('</pre>\n')
            else:
                handle_block(lines[start:counter])
            current_margin = margin
            current_level = level_of(margin)
            start = counter
            recursive = None
            continue
        if current_margin is not None and start < len(lines):
            if verbatim:
                write('<pre class=level%d>\n' % current_level)
                write_verbatim_block(lines[start:])
                write('</pre>\n')
            elif recursive is None:
                write('<pre class=level%d>\n' % current_level)
                write_filled_block(lines[start:])
                write('</pre>\n')
            else:
                write('<pre class=level%d>\n' % current_level)
                write_filled_block(lines[start:recursive])
                write('</pre>\n')
                handle_block(lines[recursive:])
        if DEBUG:
            print '---<'

    def is_verbatim(text):
        # Given TEXT, with left margin already removed, should we go in
        # VERBATIM mode?  In this mode, the current block, and all those
        # which follow up to a white line, are not refilled.
        if text.endswith('{'):
            # A line terminated with a brace.
            return True
        if '  ' in re.sub('[.!?][\'")\]}]?  ', ' ', text):
            # More than two consecutive spaces, but not a full stop.
            return True
        for word in text.split():
            if not re.search('[a-zA-Z0-9]', word):
                # A word without letter nor number.
                return True
            #if re.search('[a-zA-Z0-9_][._][a-zA-Z_]', word):
            #    # A period or underline within an identifier.
            #    return True
        return False

    def write_filled_block(lines):
        # We should not refill a block which:
        # - has a single line,
        # - starts with a short line,
        # - has, besides the last one, two short consecutive short lines.
        if len(lines) == 1:
            write_verbatim_block(lines)
            return
        was_short = True
        for line in lines[:-1]:
            short = len(line) < 30
            if was_short and short:
                write_verbatim_block(lines)
                return
            was_short = short
        import tempfile
        work = tempfile.mktemp()
        file(work, 'w').writelines(lines)
        for line in os.popen('par <%s' % work):
            write(enhanced(line))
        os.remove(work)

    def write_verbatim_block(lines):
        # Any overlong line is always refilled.
        for line in lines:
            if len(line) <= 80:
                write(enhanced(line))
            else:
                import tempfile
                work = tempfile.mktemp()
                file(work, 'w').write(line)
                for line in unicode_readlines(os.popen('par <%s' % work)):
                    write(enhanced(line))
                os.remove(work)

    def write_whiteline():
       write('\n')

    input = unicode_force(buffer).splitlines(True)
    input.append('')
    counter = 0
    fragments = []
    write = fragments.append
    # Copy message body.
    lines = []
    while counter < len(input) and input[counter] not in ('-- \n', '--\n'):
        line = input[counter]
        if line.startswith('>from'):
            line = input[counter][1:]
        lines.append(line.replace(u'\x92', '\''))
        counter += 1
    if lines:
        write_whiteline()
        handle_block(lines)
    # Copy signature.
    if counter < len(lines):
        write_whiteline()
        write('<pre class=signature>\n')
        write_verbatim_block(input[counter:])
        write('</pre>\n')
    return ''.join(fragments)

# Cache of temporary files for generated HTML references.

class Entry:
    ordinal = 0
    directory = '/tmp/CID-showfile'
    index_file = os.path.join(directory, 'index')

    def __init__(self, buffer, content_type, duration):
        Entry.ordinal += 1
        self.index = '%.4d' % Entry.ordinal
        self.file_name = os.path.join(self.directory, self.index)
        file(self.file_name, 'wb').write(buffer)
        self.content_type = content_type
        self.expiry = time.time() + duration

    def __cmp__(self, other):
        return cmp(other.expiry, self.expiry)

class Cache:

    def __init__(self):
        if not os.path.isdir(Entry.directory):
            os.mkdir(Entry.directory)
        self.index = {}
        if os.path.exists(Entry.index_file):
            self.entries = pickle.load(file(Entry.index_file, 'rb'))
            deletes = []
            for counter, entry in enumerate(self.entries):
                if os.path.exists(entry.file_name):
                    self.index[entry.index] = entry
                else:
                    deletes.append(counter)
            for counter in reversed(deletes):
                del self.entries[counter]
            self.delete_expired()
            for entry in self.entries:
                if entry.index > Entry.ordinal:
                    Entry.ordinal = entry.index
        else:
            self.entries = []

    def save(self, buffer, content_type, duration=300):
        entry = Entry(buffer, content_type, duration)
        self.entries.append(entry)
        self.entries.sort()
        self.index[entry.index] = entry
        self.delete_expired()
        pickle.dump(self.entries, file(Entry.index_file, 'wb'), -1)
        return entry.index

    def get(self, index):
        entry = self.index.get(index)
        self.delete_expired()
        return entry

    def delete_expired(self):
        now = time.time()
        while self.entries and self.entries[0].expiry < now:
            entry = self.entries.pop(0)
            os.remove(entry.file_name)
            del self.index[entry.index]

# Services.

def decoded_header(text):
    try:
        from email.header import decode_header
    except ImportError:
        from email.Header import decode_header
    try:
        result = ''
        for fragment, charset in decode_header(text):
            if result:
                result += ' '
            if charset is None:
                result += unicode(fragment)
            else:
                result += unicode(fragment, charset)
        return result
    except UnicodeDecodeError:
        return unicode(text, 'ISO-8859-1')

def enhanced(text, clean=False):
    if clean:
        replace_url = '<a href="\\1">\\3</a>'
        replace_emph = '<i>\\1</i>'
        replace_strong = '<b>\\1</b>'
        replace_code = '<tt><b>\\1</b></tt>'
    else:
        replace_url = '<a href="\\1">\\1</a>'
        replace_emph = '_<i>\\1</i>_'
        replace_strong = '*<b>\\1</b>*'
        replace_code = '`<tt><b>\\1</b></tt>\''

    def replacement(match):
        text = match.group()
        if len(text) == 1:
            if text == '&':
                return '&amp;'
            if text == '<':
                return '&lt;'
            if text == '>':
                return '&gt;'
        return match.expand(replace_url)

    text = re.sub(
           '[&<>]|((https?://)([-_.~/a-zA-Z0-9?&=]+[~/a-zA-Z0-9]))',
            replacement, text)
    text = text.replace('\f', ' ')
    text = re.sub(
            '((mailto:|ftp://)([-_.@~/a-zA-Z0-9?&=]+[~/a-zA-Z0-9]))',
            replace_url, text)
    text = re.sub(
            ('(^|[^-_%+./a-zA-Z0-9:])'
             '([-_%+./a-zA-Z0-9]+@[-a-zA-Z0-9]+\\.[-.a-zA-Z0-9]*[a-zA-Z0-9])'),
            '\\1<a href="mailto:\\2">\\2</a>', text)
    text = re.sub(
            '_([-_@./a-zA-Z0-9]*[/a-zA-Z0-9])_', replace_emph, text)
    text = re.sub(
            '\\*([-_@./a-zA-Z0-9]*[/a-zA-Z0-9])\\*', replace_strong, text)
    text = re.sub(
            '`([-_@./a-zA-Z0-9]*[/a-zA-Z0-9])\'', replace_code, text)
    return text

def error_body(text):
    return '<p class=error>%s</p>\n' % text

def payload_of(message, raw=False):
    text = message.get_payload(decode=True)
    if not raw:
        charset = message.get_param('charset') or 'ASCII'
        try:
            text = unicode(text, charset)
        except UnicodeError:
            text = unicode(text, 'ISO-8859-1')
    return text

def unicode_force(buffer):
    try:
        return buffer.decode('UTF-8')
    except UnicodeError:
        return buffer.decode('ISO-8859-1')

def unicode_read(handle):
    if isinstance(handle, basestring):
        handle = file(handle)
    return unicode_force(handle.read())

def unicode_readlines(handle):
    return unicode_read(handle).splitlines(True)
