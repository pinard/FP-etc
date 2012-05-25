# -*- coding: utf-8 -*-
# Copyright © 2009 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2009.

# Only when in XSLT mode (very experimental, not ready).

__metaclass__ = type

### Document preparation

to_delete = object()
inlineable = set(['bold', 'comment', 'datetime', 'highlight', 'italic',
                  'link', 'monospace', 'small'])

class Traversal:

    def __init__(self):
        self.processors = {}
        for key in dir(type(self)):
            if key.startswith('pre_'):
                post = False
                tag = key[4:].replace('_', '-')
            elif key.startswith('post_'):
                post = True
                tag = key[5:].replace('_', '-')
            else:
                continue
            if tag not in self.processors:
                self.processors[tag] = [None, None]
            self.processors[tag][post] = getattr(self, key)

    def dispatch(self, element):
        pre, post = self.processors.get(element.tag, (None, None))
        if pre is not None:
            value = pre(element)
            if value is not None:
                return value
        deletes = []
        for counter, child in enumerate(element):
            value = self.dispatch(child)
            if value is not None:
                if value is to_delete:
                    deletes.append(counter)
                else:
                    element[counter] = value
        if deletes:
            for counter in reversed(deletes):
                del element[counter]
        if post is not None:
            value = post(element)
            if value is not None:
                return value

class Fixup(Traversal):

    # Tag-dispatched fixups

    def pre_internal(self, element):
        text = element.text
        if text is None:
            # TODO: Se produisait avec ``xmartin``
            print('** internal = None')
            return
        text_sans = pretty_title(text)
        note = Note.registry.get(text)
        if note is None:
            self.run.report_error(
                    self.title, "Refers to missing \"%s\"" % text)
            element.text = text_sans
            return
        if not self.run.site.is_kept(note):
            self.run.report_error(
                    self.title, "Refers to restricted \"%s\"" % text)
            element.text = text_sans
            return
        url, directory = self.run.url_directory(note.notebook)
        link = etree.Element('link', url=(
            url + '/' + clean_file_name(text) + '.html'))
        link.text = text_sans
        return link

    def pre_list(self, element):
        self.fixup_notext(element)

    def pre_list_item(self, element):
        if len(element):
            if element[-1].tail:
                element[-1].tail = element[-1].tail.rstrip()
        else:
            if element.text:
                element.text = element.text.rstrip()

    def post_list_item(self, element):
        self.fixup_hide_links(element)

    def pre_note(self, element):

        def fixup_title_line():
            ## FIXME:
            #if isinstance(text, Link_node):
            #    text = text[0]
            #print >>sys.stderr, '***', repr(text)
            match = re.match('\n*(.*)\n*', element.text)
            assert element.get('title') == match.group(1), (
                    element.get('title'), match.group(1))
            element.text = element.text[match.end():]

        def fixup_date_line():
            match = re.match(
                    '\n*([12][901][0-9][0-9]-[0-2][0-9](-[0-3][0-9])?)\n*',
                    element.text)
            if match:
                element.set('date-caption', match.group(1))
                element.text = element.text[match.end():]

        def fixup_sections():
            # A section is either major or minor.  In a Tomboy note, a
            # section is introduced by a header, a major one being a single
            # line of all large characters, a minor one being a single line
            # of all bold characters.  In a section element, there is a
            # boolean major field.  On output, section numbers looks like
            # N for a major section and N.M for a minor section.

            # The table of contents, if any.
            self.toc = None

            # Beginning of line indicator.  A section header is only recognized
            # when at the beginning of a line.
            bol = True

            # Accumulates, in this order: any stuff before the first
            # section, then a table of contents element if any section,
            # then zero or more minor section elements, then zero or more
            # major section elements.  (Any minor section, once a major
            # header has been seen, gets included in some major section.)
            branches = []

            # Where current accumulation goes, either branches or a section
            # element.
            current = branches

            # The major section node, if any, in the process of being built.
            major_node = None

            # Categorization for next element.  None means that the element
            # is not a section header, so it should merely be accumulated.
            # Otherwise, tells as a boolean whether if the header is major
            # or not.
            category = None

            for counter, branch in enumerate(element):
                # Set category for the next element.
                category = None
                if (bol and branch.tag in ('large', 'bold')
                        and branch.text
                        and '\n' not in branch.text.strip()):
                    if ends_with_newline(branch):
                        eol = True
                    elif branch.tail:
                        eol = branch.tail.startswith('\n')
                    elif counter == len(element) - 1:
                        eol = True
                    else:
                        eol = starts_with_newline(element[counter+1])
                    if eol:
                        category = branch.tag = 'large'
                # Take action on element.
                if category is None:
                    current.append(branch)
                    if isinstance(branch, Node):
                        bol = ends_with_newline(branch)
                    else:
                        bol = branch.endswith('\n')
                else:
                    if current is branches:
                        self.toc = Toc_node(not branches)
                        branches.append(self.toc)
                    section = Section_node(text, category)
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
            element[:] = branches

            # A single section is not worth a table of contents.
            if len(self.toc) < 2:
                self.toc.inhibited = True
                return

            # The special "Journal *" nodes does not have a TOC.
            if element.title.startswith("Journal "):
                self.toc.inhibited = True
                return

            # When no major at all, promote all minor nodes to major.
            if major_node is None:
                for section in self.toc:
                    section.major = True

        def starts_with_newline(element):
            if element.tag not in inlineable:
                return True
            if element.text:
                return element.text.startswith('\n')
            if not element:
                return False
            return starts_with_newline(element[0])

        def ends_with_newline(element):
            if element.tag not in inlineable:
                return True
            if len(element):
                if element[-1].tail:
                    return element[-1].tail.endswith('\n')
                return ends_with_newline(element[-1])
            if element.text:
                return element.text.endswith('\n')
            return False

        fixup_title_line()
        fixup_date_line()
        fixup_sections()

    def post_note(self, element):
        self.fixup_hide_links(element)
        self.fixup_numbers(element)

    ## Fixup functions

    def fixup_notext(self, element):
        # Used for nodes which do not convey text by themselves.  All text
        # should be XML indenting whitespace, and it gets removed.
        assert not element.text or not element.text.strip(), element.text
        element.text = None
        for branch in element:
            assert not branch.tail or not branch.tail.strip(), branch.tail
            branch.tail = None

    def fixup_hide_links(self, element):
        # Used for elements producing paragraphs of text.  Try to hide each
        # link (or URL) reference under some previous text.

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
                self[counter] = Image_node(link.url)
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

    def fixup_numbers(self, element):

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

