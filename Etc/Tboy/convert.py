# -*- coding: utf-8 -*-
# Copyright © 2009 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2009.

__metaclass__ = type
import os, re, sys, time, urllib
from lxml import etree
from xml.sax import saxutils
import tools

### Conversion classes

class Converter:
    literally = False
    last_modified = None

    def document_from_note(self, note):
        note.run.entertain("Reading " + note.title)
        branches = self.digest(note, etree.XML(open(note.input_name).read()))
        assert len(branches) == 1, branches
        document = branches[0]
        document.fixup(self)
        if note.run.debug:
            document.debug_output(sys.stderr.write)
        return document

    def digest(self, note, element):

        def recurse(factory=None):
            branches = []
            if element.text:
                branches.append(element.text)
            for child in element:
                branches += self.digest(note, child)
            if factory is not None:
                branches = [factory(note, branches)]
            if element.tail:
                branches.append(element.tail)
            return branches

        def replace(branch=None, factory=None):
            branches = []
            if branch is not None:
                branches.append(branch)
            if factory is not None:
                branches = [factory(note, branches)]
            if element.tail:
                branches.append(element.tail)
            return branches

        tag = self.clean_tag(element)
        if tag in (
                'last-metadata-change-date', 'create-date',
                'cursor-position', 'width', 'height', 'x', 'y',
                'tags', 'last-change-date', 'open-on-startup'):
            return replace()
        if tag == 'note':
            return recurse(Note_node)
        if tag == 'title':
            assert len(element) == 0
            return recurse(Title_node)
        if tag == 'text':
            attribs = self.clean_attrib(element).items()
            assert attribs == [('space', 'preserve')], attribs
            return recurse()
        if tag == 'note-content':
            return recurse(Note_content_node)
        if tag == 'list':
            return recurse(List_node)
        if tag == 'list-item':
            return recurse(List_item_node)
        if tag == 'url':
            text = element.text
            if (text is not None
                    and re.match('^(ftp|https?://|mailto:)', text)):
                link = Link_node(note)
                link.url = text
                return replace(link)
            return recurse(Italic_node)
        if tag == 'internal':
            text = element.text
            if text is None:
                # TODO: Se produisait avec ``xmartin``
                print '** internal = None'
                return ''
            text_sans = tools.pretty_title(text)
            note2 = tools.Note.registry.get(text)
            if note2 is None:
                note.run.report_error(
                        note.title, "Refers to missing \"%s\"" % text)
                return replace(text_sans)
            if not tools.is_linkable(note, note2):
                note.run.report_error(
                        note.title, "Refers to restricted \"%s\"" % text)
                return replace(text_sans)
            url, directory = note2.run.site.url_directory(note2.notebook)
            link = Link_node(note2, [text_sans])
            link.url = url + '/' + tools.clean_file_name(text) + '.html'
            return replace(link)
        if tag == 'broken':
            return recurse()
        if tag == 'monospace':
            return recurse(Monospace_node)
        if tag == 'large':
            return recurse(Large_node)
        if tag == 'small':
            return recurse(Small_node)
        if tag == 'highlight':
            return recurse(Highlight_node)
        if tag == 'bold':
            return recurse(Bold_node)
        if tag == 'italic':
            return recurse(Italic_node)
        if tag == 'datetime':
            return recurse(Datetime_node)
        # Élément inconnu!
        branches = self.unknown_element(note, element)
        note.run.report_error(note.title, "Unknown " + repr(branches))
        return branches

    def unknown_element(self, note, element):
        branches = [Comment_node(
            note,
            [note.title + ': ' + self.clean_tag(element) + ' inconnu!'])]
        fragments = []
        write = fragments.append
        keys = element.attrib.items()
        write(self.clean_tag(element))
        if keys:
            write(' ' + repr(keys))
        write(' ' + repr(element.text))
        branches.append(Comment_node(note, [''.join(fragments)]))
        for child in element:
            branches += self.digest(note, child)
        if element.tail:
            branches.append(element.tail)
        return branches

    def clean_tag(self, element):
        text = element.tag
        position = text.find('}')
        if position:
            return text[position + 1:]

    def clean_attrib(self, element):
        result = {}
        if element.attrib:
            for key, value in element.attrib.items():
                position = key.find('}')
                if position:
                    result[key[position + 1:]] = value
                else:
                    result[key] = value
        return result

    def escape_link(self, text):
        if ':/' in text:
            left, right = text.split(':/', 1)
            left += ':/'
        else:
            left = ''
            right = text
        if isinstance(right, unicode):
            right = right.encode(tools.ENCODING)
        return left + self.escape(urllib.quote(right, safe="/#?="))

class Docbook_converter(Converter):

    def convert(self, note):
        if note.run.xslt:
            document = note.get_fixed_document()
        else:
            document = self.document_from_note(note)
            if note.run.reformat:
                work = tempfile.mktemp('-tboy-for-xmllint')
                document.docbook_output(
                        codecs.open(work, 'w', tools.ENCODING).write, self)
                buffer = os.popen(
                        'xmllint -encode utf-8 -format ' + work).read()
                os.remove(work)
                return buffer.decode(tools.ENCODING)
            fragments = []
            document.docbook_output(fragments.append, self)
            return ''.join(fragments)

    def escape(self, text):
        if self.literally:
            text = text.replace(' ', tools.NON_BREAKABLE_SPACE)
        return saxutils.escape(text)

    def output(self, node, write):
        node.docbook_output(write, self)

    def start_paragraph(self, write):
        write('<para>')

    def end_paragraph(self, write):
        write('</para>\n')

    def break_line(self, write):
        # FIXME!
        pass

class Html_converter(Converter):

    def convert(self, note):
        movable_type = isinstance(self, MT_converter)
        self.note = note
        if note.run.xslt:

            note.run.entertain("Reading " + note.title)
            document = note.get_fixed_document()
            xslt = xsl_transformer('html.xsl')
            xml = xslt(xml,
                       blog=xsl_boolean(movable_type),
                       styleurl=xsl_string(note.run.site.styleurl))
            buffer = etree.tostring(xml.getroot()) + '\n'
            # Éliminer les déclarations de namespace.  (Tidy les oublie?)
            buffer = re.sub(r'(<[^>\s]*)(\s*xmlns(:[^>=]*)?\s*=\s*"[^>"]*")*',
                            r'\1', buffer)
            if note.run.reformat and not movable_type:
                work = tempfile.mktemp('-tboy-for-tidy')
                file(work, 'w').write(buffer.encode(tools.ENCODING))
                # FIXME: Enlever le /dev/null
                buffer = (os.popen('tidy 2> /dev/null -q -i -utf8 ' + work)
                          .read()
                          .decode(tools.ENCODING))
                if not buffer:
                    sys.exit('tidy -q -i -utf8 %s : empty result' % work)
                os.remove(work)

        else:

            if isinstance(self, MT_converter):
                document = self.document_from_note(note)
            else:
                self.last_modified = note.date
                document = self.document_from_note(note)
                self.last_modified = None
            if note.run.reformat and not movable_type:
                work = tempfile.mktemp('-tboy-for-tidy')
                document.html_output(
                        codecs.open(work, 'w', tools.ENCODING).write, self)
                # FIXME: Enlever le /dev/null
                buffer = (os.popen('tidy 2> /dev/null -q -i -utf8 ' + work)
                          .read()
                          .decode(tools.ENCODING))
                if not buffer:
                    sys.exit('tidy -q -i -utf8 %s : empty result' % work)
                os.remove(work)
            else:
                fragments = []
                document.html_output(fragments.append, self)
                buffer = ''.join(fragments)

        del self.note
        return buffer

    def escape(self, text):

        def write_fragment(fragment):
            position = fragment.find('\t')
            while position >= 0:
                fragment = (
                        fragment[:position]
                        + (8 - position % 8) * tools.NON_BREAKABLE_SPACE
                        + fragment[position + 1:])
                position = fragment.find('\t')
            fragment = saxutils.escape(fragment)
            if self.literally:
                fragment = (fragment.replace(' ', tools.NON_BREAKABLE_SPACE)
                            .replace('\n', '<br />\n'))
            return write(fragment)

        fragments = []
        write = fragments.append
        position = 0
        while True:
            start = text.find('\\[', position)
            if start < 0:
                write_fragment(text[position:])
                break
            end = text.find('\\]', start + 2)
            if end < 0:
                write_fragment(text[position:])
                break
            math = text[start + 2:end].strip()
            if not math:
                write_fragment(text[start:end + 2])
                position = end + 2
                continue
            write_fragment(text[position:start])
            site = self.note.run.site
            url, directory = site.url_directory()
            number = site.number_by_math.get(math)
            if number is None:
                numbers = set(site.number_by_math.values())
                number = 1
                while str(number) in numbers:
                    number += 1
                number = str(number)
                site.number_by_math[math] = number
                filename = '%s/%s.math' % (directory, number)
                file(filename, 'w').write(math + '\n')
            else:
                filename = '%s/%s.math' % (directory, number)
                site.output_names.discard(filename)
            if '{' in math:
                write('<img align="center" src="%s/%s.png">' % (url, number))
            else:
                write('<img src="%s/%s.png">' % (url, number))
            position = end + 2
        return ''.join(fragments)

    def output(self, node, write):
        node.html_output(write, self)

    def start_paragraph(self, write):
        write('<p>')

    def end_paragraph(self, write):
        write('</p>\n')

    def break_line(self, write):
        write('<br />\n')

class MT_converter(Html_converter):

    def convert(self, note):
        self.note = note
        document = self.document_from_note(note)
        fragments = []
        write = fragments.append
        document.html_output(write, self)
        del self.note
        return ''.join(fragments)

    def movable_prefix(self, title, date):
        return ("AUTHOR: François Pinard\n"
                "TITLE: %s\n"
                "BASENAME: %s\n"
                "STATUS: Publish\n"
                "ALLOW COMMENTS: 1\n"
                "CONVERT BREAKS: 0\n"
                "ALLOW PINGS: 1\n"
                "PRIMARY CATEGORY: \n"
                "DATE: %s\n"
                "-----\n"
                "BODY:\n"
                % (title, title, date))

    def movable_suffix(self):
        return ("-----\n"
                "EXTENDED BODY:\n"
                "\n"
                "-----\n"
                "EXCERPT:\n"
                "\n"
                "-----\n"
                "KEYWORDS:\n"
                "\n"
                "\n"
                "\n"
                "--------\n")

class Rest_converter(Converter):
    list_level = 0

    def bold_tag(self, write, converter):
        self.output_nested(write, converter, '**', '**')

    def comment_tag(self, write, converter):
        self.output_nested(write, converter, '.: ', '\n')

    def datetime_tag(self, write, converter):
        self.output_nested(write, converter, '*', '*')

    def highlight_tag(self, write, converter):
        self.output_nested(write, converter, '*', '*')

    def italic_tag(self, write, converter):
        self.output_nested(write, converter, '*', '*')

    def link_tag(self, write, converter):
        write('`')
        if self:
            self.output_branches(write, converter)
        else:
            write(converter.escape(self.url))
        write(' <' + converter.escape_link(self.url) + '>`')

    def monospace_tag(self, write, converter):
        converter.literally = True
        self.output_nested(write, converter, '``', '``')
        converter.literally = False

    def note_content_tag(self, write, converter):
        # Bug?
        title = converter.escape(self.note.title)
        ruler = '=' * len(title)
        write(ruler + '\n'
              + title + '\n'
              + ruler + '\n')
        self.output_paragraphs(write, converter)

    def section_tag(self, write, converter):
        # Bug?
        title = converter.escape(self.title)
        write('\n'
              + title + '\n'
              + '-='[self.major] * len(title) + '\n'
              + '\n')
        self.output_paragraphs(write, converter)

    def toc_tag(self, write, converter):
        if self.inhibited:
            return
        write('\n'
              '..: contents\n'
              '..: sectnum\n')

    def convert(self, note):
        document = self.document_from_note(note)
        fragments = []
        document.rest_output(fragments.append, self)
        return ''.join(fragments)

    def escape(self, text):
        if self.literally:
            text = text.replace(' ', tools.NON_BREAKABLE_SPACE)
        return text

    def output(self, node, write):
        node.rest_output(write, self)

    def start_paragraph(self, write):
        if self.list_level:
            prefix = '\n' + ':' * self.list_level + ' '
        else:
            prefix = '\n'
        write(prefix)

    def end_paragraph(self, write):
        write('\n')

    def break_line(self, write):
        write('<br />\n')

class Wiki_converter(Converter):
    list_level = 0

    def bold_tag(self, write, converter):
        self.output_nested(write, converter, '\'\'\'', '\'\'\'')

    def datetime_tag(self, write, converter):
        self.output_nested(write, converter, '\'\'', '\'\'')

    def italic_tag(self, write, converter):
        self.output_nested(write, converter, '\'\'', '\'\'')

    def link_tag(self, write, converter):
        if self:
            write('[' + converter.escape_link(self.url) + ' ')
            self.output_branches(write, converter)
            write(']')
        else:
            write(converter.escape(self.url))

    def list_item_tag(self, write, converter):
        if self:
            write(':' * (converter.list_level - 1) + '* ')
            self.output_branches(write, converter)
            write('\n')

    def list_tag(self, write, converter):
        converter.list_level += 1
        self.output_branches(write, converter)
        converter.list_level -= 1

    def monospace_tag(self, write, converter):
        converter.literally = True
        self.output_nested(write, converter, '<tt>', '</tt>')
        converter.literally = False

    def note_content_tag(self, write, converter):
        # Bug?
        write('\n== ' + converter.escape(self.note.title) + ' ==\n\n')
        self.output_paragraphs(write, converter)

    def section_tag(self, write, converter):
        equals = ('====', '===')[self.major]
        write('\n' + equals + ' '
              # Bug?
              + converter.escape(self.title)
              + ' ' + equals + '\n\n')
        self.output_paragraphs(write, converter)

    def convert(self, note):
        document = self.document_from_note(note)
        fragments = []
        document.wiki_output(fragments.append, self)
        return ''.join(fragments)

    def escape(self, text):
        if self.literally:
            text = text.replace(' ', tools.NON_BREAKABLE_SPACE)
        return text

    def output(self, node, write):
        node.wiki_output(write, self)

    def start_paragraph(self, write):
        if self.list_level:
            prefix = '\n' + ':' * self.list_level + ' '
        else:
            prefix = '\n'
        write(prefix)

    def end_paragraph(self, write):
        write('\n')

    def break_line(self, write):
        write('<br />\n')

# XML tree rebuilt and simplified for processing.

class Node(list):
    inline_markup = False
    pattern1 = re.compile('(\\A|.*[\\s([{])`(\\Z|\\S.*)', re.DOTALL)
    pattern2 = re.compile('(.*?)(\\S{2,}) $', re.DOTALL)

    def __init__(self, note, branches=()):
        self.note = note
        list.__init__(self, branches)

    def debug_output(self, write, level=0):
        write('%2s ' % level + '  ' * level + self.node_repr() + '\n')
        level += 1
        for branch in self:
            if isinstance(branch, Node):
                branch.debug_output(write, level)
            else:
                write('%2s ' % level + '  ' * level
                      + truncated_repr(branch, 76 - 2 * level)
                      + '\n')

    def node_repr(self):
        return type(self).__name__

    def starts_with_newline(self):
        if not self.inline_markup:
            return True
        if not self:
            return False
        if isinstance(self[0], Node):
            return self[0].starts_with_newline()
        return self[0].startswith('\n')

    def ends_with_newline(self):
        if not self.inline_markup:
            return True
        if not self:
            return False
        if isinstance(self[-1], Node):
            return self[-1].ends_with_newline()
        return self[-1].endswith('\n')

    def fixup(self, converter):
        for branch in self:
            if isinstance(branch, Node):
                branch.fixup(converter)

    def fixup_notext_whitespace(self):
        # Used for nodes which do not convey text by themselves.  All text
        # should be XML indenting whitespace, and it gets removed.
        counter = 0
        while counter < len(self):
            branch = self[counter]
            if isinstance(branch, Node):
                counter += 1
            else:
                assert not branch.strip(), branch
                del self[counter]

    def fixup_hide_links(self):
        # Used for nodes producing paragraphs of text.  Try to hide each link
        # (or URL) reference under some previous text.

        # Scan all branches from first to last, watching for all link nodes
        # immediately preceded by some text.
        counter = 0
        while counter < len(self) - 1:
            text = self[counter]
            counter += 1
            if isinstance(text, Node):
                continue
            link = self[counter]
            if not isinstance(link, Link_node):
                continue
            if link:
                # An internal link already has a description.
                continue
            # At this point, text is a string, link is a link node, and
            # counter is such that self[counter] is the link node.
            if text.endswith('▢ '):
                # The link represents an image to be inserted.
                self[counter-1] = text[:-2]
                self[counter] = Image_node(self.note, link.url)
                continue
            if text.endswith('` '):
                # The link is preceded by exactly one space, then a backquote.
                # Scan back for the corresponding beginning bacquote.
                # If found, the hiding text is between them.
                start = counter
                while start > 0:
                    start -= 1
                    if isinstance(self[start], Node):
                        continue
                    match = self.pattern1.match(self[start])
                    if match:
                        # self[start] contains the beginning backquote.
                        if start == counter - 1:
                            # Both bacquotes are located in the same string.
                            self[start] = match.group(1)
                            link.append(match.group(2)[:-2])
                        else:
                            # The beginning backquote is in self[start], the
                            # end backquote is in self[counter-1].  
                            self[start] = match.group(1)
                            self[counter-1] = self[counter-1][:-2]
                            link.append(match.group(2))
                            link += self[start+1:counter-1]
                            del self[start+1:counter-1]
                            counter = start + 2
                        break
                continue
            match = self.pattern2.match(text)
            if match:
                # The link is preceded by exactly one space, then a blob
                # of ink at least three caracters wide.  Use it to hide
                # the reference.
                self[counter-1] = match.group(1)
                link.append(match.group(2))

    def output_branches(self, write, converter):
        for branch in self:
            if isinstance(branch, Node):
                converter.output(branch, write)
            else:
                write(converter.escape(branch))

    def output_nested(self, write, converter, start, end):
        fragments = []
        self.output_branches(fragments.append, converter)
        buffer = ''.join(fragments)
        if buffer:
            write(start)
            write(buffer)
            write(end)

    def output_paragraphs(self, write, converter):

        def write_line(line):
            match = re.match(' +', line)
            if match:
                converter.literally = True
                write(converter.escape(match.group()))
                converter.literally = False
                write(converter.escape(line[match.end():]))
            else:
                write(converter.escape(line))

        within_paragraph = False
        for branch in self:
            if isinstance(branch, Node):
                if branch.inline_markup:
                    if not within_paragraph:
                        converter.start_paragraph(write)
                        within_paragraph = True
                else:
                    if within_paragraph:
                        converter.end_paragraph(write)
                        within_paragraph = False
                converter.output(branch, write)
            else:
                position = 0
                for match in re.finditer('\n\n+', branch):
                    line = branch[position:match.start()]
                    if line:
                        if not within_paragraph:
                            converter.start_paragraph(write)
                            within_paragraph = True
                        write_line(line)
                    if len(match.group()) > 1:
                        if within_paragraph:
                            converter.end_paragraph(write)
                            within_paragraph = False
                    else:
                        if within_paragraph:
                            converter.break_line(write)
                    position = match.end()
                line = branch[position:]
                if line:
                    if not within_paragraph:
                        converter.start_paragraph(write)
                        within_paragraph = True
                    write_line(line)
        if within_paragraph:
            converter.end_paragraph(write)

def truncated_repr(object, length):
    text = repr(object)
    if len(text) > length:
        left = length * 2 / 3
        right = length - left
        text = text[:left-3] + u' … ' + text[-right:]
    return text

class Bold_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        self.output_nested(
                write, converter, '<emphasis role="bold">', '</emphasis>')

    def html_output(self, write, converter):
        self.output_nested(write, converter, '<b>', '</b>')

    def rest_output(self, write, converter):
        self.output_nested(write, converter, '**', '**')

    def wiki_output(self, write, converter):
        self.output_nested(write, converter, '\'\'\'', '\'\'\'')

class Comment_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        self.output_nested(write, converter, '<!-- ', ' -->')

    html_output = docbook_output

    def rest_output(self, write, converter):
        self.output_nested(write, converter, '.: ', '\n')

    wiki_output = docbook_output

class Datetime_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        # TODO: Should be smaller as well.
        self.output_nested(write, converter, '<emphasis>', '</emphasis>')

    def html_output(self, write, converter):
        start = '<span style="font-size:71%"><i>'
        end = '</i></span>'
        self.output_nested(write, converter, start, end)

    def rest_output(self, write, converter):
        self.output_nested(write, converter, '*', '*')

    def wiki_output(self, write, converter):
        self.output_nested(write, converter, '\'\'', '\'\'')

    wiki_output = html_output

class Highlight_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        # TODO: Should rather use a yellow background.
        self.output_nested(write, converter, '<emphasis>', '</emphasis>')

    def html_output(self, write, converter):
        self.output_nested(
                write, converter,
                '<span style="background-color:#FFFF66">', '</span>')

    def rest_output(self, write, converter):
        self.output_nested(write, converter, '*', '*')

    wiki_output = html_output

class Image_node(Node):

    def __init__(self, note, image, link=None, alt=None):
        self.image = image
        self.link = link
        self.alt = alt
        Node.__init__(self, note)

    def docbook_output(self, write, converter):
        pass
    
    def html_output(self, write, converter):
        if self.link:
            write('<a href="%s">' % converter.escape_link(self.link))
        write('<img align="right" src="%s"'
              % converter.escape_link(self.image))
        if self.alt:
            write(' alt="%s"' % converter.escape(self.alt))
        write('>')
        if self.link:
            write('</a>\n')

    def wiki_output(self, write, converter):
        pass

class Italic_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        self.output_nested(write, converter, '<emphasis>', '</emphasis>')

    def html_output(self, write, converter):
        self.output_nested(write, converter, '<i>', '</i>')

    def rest_output(self, write, converter):
        self.output_nested(write, converter, '*', '*')

    def wiki_output(self, write, converter):
        self.output_nested(write, converter, '\'\'', '\'\'')

class Large_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        # TODO; Should really use a larger font.
        self.output_nested(
                write, converter, '<emphasis role="bold">', '</emphasis>')

    def html_output(self, write, converter):
        start = '<span style="font-size:141%">'
        end = '</span>'
        self.output_nested(write, converter, start, end)

    wiki_output = html_output

class Last_modified_node(Node):

    def __init__(self, note, last_modified):
        self.last_modified = last_modified
        Node.__init__(self, note)

    def node_name(self):
        return Node.node_name(self) + ' ' + self.last_modified

    def docbook_output(self, write, converter):
        pass

    def html_output(self, write, converter):
        write('<hr class="ruler" />\n'
              "Last modified: " + self.last_modified + '\n')

    def wiki_output(self, write, converter):
        pass

class Link_node(Node):
    inline_markup = True

    def node_repr(self):
        return Node.node_repr(self) + ' ' + self.url

    def docbook_output(self, write, converter):
        write('<ulink url="' + converter.escape_link(self.url) + '">')
        if self:
            self.output_branches(write, converter)
        else:
            write(converter.escape(self.url))
        write('</ulink>')

    def html_output(self, write, converter):
        write('<a class="reference" href="'
              + converter.escape_link(self.url) + '">')
        if self:
            self.output_branches(write, converter)
        else:
            write(converter.escape(self.url))
        write('</a>')

    def rest_output(self, write, converter):
        write('`')
        if self:
            self.output_branches(write, converter)
        else:
            write(converter.escape(self.url))
        write(' <' + converter.escape_link(self.url) + '>`')

    def wiki_output(self, write, converter):
        if self:
            write('[' + converter.escape_link(self.url) + ' ')
            self.output_branches(write, converter)
            write(']')
        else:
            write(converter.escape(self.url))

class List_item_node(Node):

    def fixup(self, converter):
        if (self and not isinstance(self[-1], Node)
                and self[-1].endswith('\n')):
            self[-1] = self[-1].rstrip()
        Node.fixup(self, converter)
        Node.fixup_hide_links(self)

    def docbook_output(self, write, converter):
        if self:
            self.output_nested(
                    write, converter,
                    '<listitem><para>', '</para></listitem>\n')

    def html_output(self, write, converter):
        if self:
            self.output_nested(write, converter, '<li>', '</li>\n')

    def wiki_output(self, write, converter):
        if self:
            write(':' * (converter.list_level - 1) + '* ')
            self.output_branches(write, converter)
            write('\n')

class List_node(Node):

    def fixup(self, converter):
        self.fixup_notext_whitespace()
        Node.fixup(self, converter)

    def docbook_output(self, write, converter):
        self.output_nested(
                write, converter, '<itemizedlist>\n', '</itemizedlist>\n')

    def html_output(self, write, converter):
        self.output_nested(write, converter, '<ul>\n', '</ul>\n')

    def wiki_output(self, write, converter):
        converter.list_level += 1
        self.output_branches(write, converter)
        converter.list_level -= 1

class Monospace_node(Node):
    inline_markup = True
                
    def docbook_output(self, write, converter):
        for branch in self:
            if isinstance(branch, Node):
                if converter.literally:
                    write('</literal>')
                    converter.literally = False
                branch.docbook_output(write, converter)
            else:
                for line in branch.splitlines(True):
                    if line.endswith('\n'):
                        line = line[:-1]
                        if line:
                            if not converter.literally:
                                write('<literal>')
                                converter.literally = True
                            write(converter.escape(line))
                        if converter.literally:
                            write('</literal>')
                            converter.literally = False
                        write('</para>\n'
                              '<para>')
                    else:
                        if not converter.literally:
                            write('<literal>')
                            converter.literally = True
                        if line.endswith('\n'):
                            line = line[:-1]
                        write(converter.escape(line))
        if converter.literally:
            write('</literal>')
            converter.literally = False
                
    def html_output(self, write, converter):
        write('<tt class="file docutils literal"><span class="pre">')
        converter.literally = True
        for branch in self:
            if isinstance(branch, Node):
                branch.html_output(write, converter)
            else:
                write(converter.escape(branch))
        converter.literally = False
        write('</span></tt>')

    def rest_output(self, write, converter):
        converter.literally = True
        self.output_nested(write, converter, '``', '``')
        converter.literally = False

    def wiki_output(self, write, converter):
        converter.literally = True
        self.output_nested(write, converter, '<tt>', '</tt>')
        converter.literally = False

class Note_content_node(Node):

    def node_repr(self):
        return Node.node_repr(self) + ' ' + self.note.title

    def fixup(self, converter):
        self.fixup_title_line()
        self.fixup_sections()
        Node.fixup(self, converter)
        Node.fixup_hide_links(self)
        self.fixup_numbers()
        self.fixup_last_modified(converter)

    def fixup_title_line(self):
        # Delete the title and surrounding white lines.
        text = self.pop(0)
        # FIXME:
        if isinstance(text, Link_node):
            text = text[0]
        text = text[re.match('\n*.*\n*', text).end():]
        if text:
            self.insert(0, text)
        if not self:
            # DocBook requires at least one paragraph.
            self.append('')

    def fixup_sections(self):
        # A section is either major or minor.  In a Tomboy note, a section is
        # introduced by a header, a major one being a single line of all large
        # characters, a minor one being a single line of all bold characters.
        # In a section node, there is a boolean major field.  On output,
        # section numbers looks like N for a major section and N.M for a
        # minor section.

        # The table of contents node, if any.
        self.toc = None

        # Beginning of line indicator.  A section header is only recognized
        # when at the beginning of a line.
        bol = True

        # Accumulates, in this order: any stuff before the first section. then
        # a table of contents node if any section, then zero or more minor
        # nodes, then zero or more major nodes.  (Any minor section, once a
        # major header has been seen, gets included in some major section.)
        branches = []

        # Where current accumulation goes, either branches or a section node.
        current = branches

        # The major section node, if any, in the process of being built.
        major_node = None

        # Categorization for next element.  None means that the element is
        # not a section header, so it should merely be accumulated.  Otherwise,
        # tells as a boolean whether if the header is major or not.
        category = None

        for counter, branch in enumerate(self):
            # Set category for the next element.  Unless None, text has the
            # incoming section title.
            category = None
            if bol and isinstance(branch, (Large_node, Bold_node)):
                if branch.ends_with_newline():
                    eol = True
                elif counter == len(self) - 1:
                    eol = True
                else:
                    branch2 = self[counter+1]
                    if isinstance(branch2, Node):
                        eol = branch2.starts_with_newline()
                    else:
                        eol = branch2.startswith('\n')
                if eol:
                    # FIXME: Does not cover all possible cases.
                    text = branch[0]
                    if not isinstance(text, Node):
                        text = text.strip()
                        if text and '\n' not in text.strip():
                            category = isinstance(branch, Large_node)
            # Take action on element.
            if category is None:
                current.append(branch)
                if isinstance(branch, Node):
                    bol = branch.ends_with_newline()
                else:
                    bol = branch.endswith('\n')
            else:
                if current is branches:
                    self.toc = Toc_node(self.note, not branches)
                    branches.append(self.toc)
                section = Section_node(self.note, text, category)
                self.toc.append(section)
                if major_node and not category:
                    major_node.append(section)
                else:
                    branches.append(section)
                current = section
                if current.major:
                    major_node = section

        # Put everything in place.
        if current is branches:
            return
        self[:] = branches

        # A single section is not worth a table of contents.
        if len(self.toc) < 2:
            self.toc.inhibited = True
            return

        # The special "Journal *" nodes does not have a TOC.
        if self.note.title.startswith("Journal "):
            self.toc.inhibited = True
            return

        # When no major at all, promote all minor nodes to major.
        if major_node is None:
            for section in self.toc:
                section.major = True

    def fixup_numbers(self):

        def adjust(node, numbers):
            if not node.title.strip():
                node.title = "<title error " + repr(node.title) + '>'
            node.numbers = numbers.replace('.', '-')
            word = node.title.split(None, 1)[0]
            if word.endswith('.'):
                word = word[:-1]
            if not word.isdigit():
                node.title_prefix = numbers + tools.NON_BREAKABLE_SPACE * 3

        if self.toc is None or self.toc.inhibited:
            return

        major_count = 0
        minor_count = 0
        for branch in self:
            if isinstance(branch, Section_node):
                if branch.major:
                    major_count += 1
                    adjust(branch, '%s' % major_count)
                    minor_count = 0
                    for minor in branch:
                        if isinstance(minor, Section_node):
                            assert not minor.major, minor
                            minor_count += 1
                            adjust(minor,
                                   '%s.%s' % (major_count, minor_count))
                else:
                    minor_count += 1
                    adjust(branch, '%s.%s' % (major_count, minor_count))

    def fixup_last_modified(self, converter):
        if converter.last_modified is not None:
            self.append(Last_modified_node(self.note, converter.last_modified))

    def docbook_output(self, write, converter):
        self.output_paragraphs(write, converter)

    def html_output(self, write, converter):
        if not isinstance(converter, MT_converter):
            write('<body>\n')
        pretty = tools.pretty_title(self.note.title.strip())
        if isinstance(converter, MT_converter):
            editor = None
        else:
            editor = self.note.run.site.editor
        if editor is None:
            write('<h1>' + converter.escape(pretty) + '</h1>\n')
        else:
            write('<form method="get" action="%s">\n'
                  '<h1>%s\n'
                  '<input type="submit" value="Edit"/>\n'
                  '<input type="hidden" name="note" value="%s"/>\n'
                  '</h1>\n'
                  '</form>\n'
                  % (editor, converter.escape(pretty),
                     converter.escape(self.note.title)))
        self.output_paragraphs(write, converter)
        if not isinstance(converter, MT_converter):
            write('</body>\n')

    def rest_output(self, write, converter):
        title = converter.escape(self.note.title)
        ruler = '=' * len(title)
        write(ruler + '\n'
              + title + '\n'
              + ruler + '\n')
        self.output_paragraphs(write, converter)

    def wiki_output(self, write, converter):
        write('\n== ' + converter.escape(self.note.title) + ' ==\n\n')
        self.output_paragraphs(write, converter)

class Note_node(Node):

    def fixup(self, converter):
        self.fixup_notext_whitespace()
        Node.fixup(self, converter)

    def docbook_output(self, write, converter):
        self.output_nested(
                write, converter,
                '<?xml version="1.0"?>\n' + tools.DOCBOOK_DOCTYPE
                + '<article>\n',
                '</article>\n')

    def html_output(self, write, converter):
        if isinstance(converter, MT_converter):
            self.output_branches(write, converter)
        else:
            write(tools.HTML_DOCTYPE)
            write('<html>\n')
            self.output_branches(write, converter)
            write('\n</html>\n')

    def rest_output(self, write, converter):
        self.output_branches(write, converter)

    def wiki_output(self, write, converter):
        self.output_branches(write, converter)

class Section_node(Node):
    numbers = None
    title_prefix = ''

    def __init__(self, note, title, major):
        if title == "Reclasser" and note.title[-2:] == ':t':
            note.run.report_error(note.title, "Public Reclasser section")
        self.title = title
        self.major = major
        Node.__init__(self, note)

    def node_repr(self):
        return (Node.node_repr(self) + ' ' + self.title_prefix + self.title)

    def fixup(self, converter):
        Node.fixup(self, converter)
        Node.fixup_hide_links(self)

    def docbook_output(self, write, converter):
        write(('<sect2>', '<sect1>')[self.major] + '\n')
        write('<title>')
        write(converter.escape(tools.pretty_title(self.title)))
        write('</title>\n')
        self.output_paragraphs(write, converter)
        write(('</sect2>', '</sect1>')[self.major] + '\n')

    def html_output(self, write, converter):
        title = converter.escape(self.title_prefix + self.title)
        if self.numbers:
            write(('<h3>', '<h2>')[self.major]
                  + ('<a href="#toc%s" id="sec%s">%s</a>'
                     % (self.numbers, self.numbers, title))
                  + ('</h3>', '</h2>')[self.major] + '\n')
        else:
            write(('<h3>', '<h2>')[self.major]
                   + title
                  + ('</h3>', '</h2>')[self.major] + '\n')
        self.output_paragraphs(write, converter)

    def rest_output(self, write, converter):
        title = converter.escape(self.title)
        write('\n'
              + title + '\n'
              + '-='[self.major] * len(title) + '\n'
              + '\n')
        self.output_paragraphs(write, converter)

    def wiki_output(self, write, converter):
        equals = ('====', '===')[self.major]
        write('\n' + equals + ' '
              + converter.escape(self.title)
              + ' ' + equals + '\n\n')
        self.output_paragraphs(write, converter)

class Small_node(Node):
    inline_markup = True

    def docbook_output(self, write, converter):
        # TODO: Should really use a smaller font.
        self.output_nested(write, converter, '<emphasis>', '</emphasis>')

    def html_output(self, write, converter):
        start = '<span style="font-size:71%">'
        end = '</span>'
        self.output_nested(write, converter, start, end)

    wiki_output = html_output

class Title_node(Node):

    def docbook_output(self, write, converter):
        write('<title>')
        fragments = []
        self.output_branches(fragments.append, converter)
        write(toolspretty_title(''.join(fragments)))
        write('</title>')

    def html_output(self, write, converter):
        if not isinstance(converter, MT_converter):
            write('<head>\n' 
                  '<meta http-equiv="Content-Type"'
                  ' content="text/html; charset=utf-8" />\n')
            styleurl = self.note.run.site.styleurl
            if styleurl is not None:
                write('<link rel="stylesheet" href="'
                      + styleurl + '" type="text/css" />\n')
            write('<title>')
            fragments = []
            self.output_branches(fragments.append, converter)
            write(tools.pretty_title(''.join(fragments)))
            write('</title>\n'
                  '</head>\n')

    def rest_output(self, write, converter):
        pass

    def wiki_output(self, write, converter):
        pass

class Toc_node(Node):
    inhibited = False

    def __init__(self, note, first):
        self.first = first
        Node.__init__(self, note)

    def fixup(self, converter):
        # The table of contents contain only section nodes, extracted
        # from the overall tree.  All nodes here are mere duplicates.
        # As fixup happens elsewhere, no need to repeat it all here.
        pass

    def debug_output(self, write, level=0):
        if self.inhibited:
            return
        indent = '%2s ' % level + '  ' * level
        write(indent + type(self).__name__ + '\n')
        level += 1
        indent = '%2s ' % level + '  ' * level
        for branch in self:
            write(indent + branch.node_repr() + ' …\n')

    def docbook_output(self, write, converter):
        pass

    def html_output(self, write, converter):
        if self.inhibited:
            return
        if not self.first:
            write('<br />\n'
                  '<hr class="ruler" />\n')
        write("Contents\n"
              '<ul>\n')
        major = False
        minor = False
        for section in self:
            if section.major:
                if minor:
                    write('</li>\n'
                          '</ul>\n')
                    minor = False
                if major:
                    write('</li>\n')
                major = True
            else:
                if minor:
                    write('</li>\n')
                else:
                    write('\n'
                          '<ul>\n')
                    minor = True
            write('<li><a href="#sec%s" id="toc%s">%s</a>'
                  % (section.numbers, section.numbers,
                     converter.escape(section.title_prefix + section.title)))
        if minor:
            write('</ul>\n'
                  '</li>\n')
        write('</ul>\n'
              '<hr class="ruler" />\n')

    def rest_output(self, write, converter):
        if self.inhibited:
            return
        write('\n'
              '..: contents\n'
              '..: sectnum\n')

    def wiki_output(self, write, converter):
        pass
