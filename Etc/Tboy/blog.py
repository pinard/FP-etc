# -*- coding: utf-8 -*-

import tools

class Blog_maker:

    def __init__(self, run):
        self.run = run

    def apply(self, converter):
        self.escape = converter.escape
        if self.run.xslt:
            write(self.blog_section("Generating blog page",
                                    self.table_of_contents(entries)))
            entries = etree.Element('entries')
            for counter, (title, date) in enumerate(entries):
                etree.SubElement(entries, 'entry',
                                 title=tools.pretty_title(note.title),
                                 idref=title.replace(' ', '-'),
                                 date=note.stamp)
            return self.create_through_xslt(xml, 'blog-page.xsl')
        else:
            self.run.entertain("Generating the blog entry")
            fragments = []
            write = fragments.append
            write(self.prolog())

            def ordering(a, b):
                titlea, datea = a
                titleb, dateb = b
                return cmp(dateb, datea) or locale.strcoll(titlea, titleb)

            entries = sorted(self.run.site.blog_entries, ordering)
            for title, date in entries:
                buffer = self.convert_from_title(title, converter)
                if buffer:
                    write(self.blog_section(title, buffer))
            write(self.blog_section("Contents",
                                    self.table_of_contents(entries)))
            write(self.epilog())
            return ''.join(fragments)

    def prolog(self):
        fragments = []
        write = fragments.append
        write(tools.HTML_DOCTYPE)
        write(u"""\
<html>
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>Pseudo-blog</title>
 </head>
 <body>
  <h1>Pseudo-blog</h1>

  <b>A transient storing device for personal mumblings
  and miscellaneous thoughts</b>

  <p>
   Why do I call this a <i>pseudo-blog</i>?  In a real blog, entries are
   permanent, and visitors may freely add their own comments.
   While here, entries are transient, likely to be modified, reattached
   elsewhere in my Web site, or plainly deleted.  Comments may be emailed
   <a href="mailto:pinard@iro.umontreal.ca">directly to me</a>.
  </p>

  <p>
   A <a href="#Contents">table of contents</a> appears at the end of
   this page.  The blog entries are themselves selected from <a
   href="/notes/index.html">my published notes</a>, for which there is
   also a table showing the <a href="/notes/recent.html">most recently
   modified entries</a>.  Elsewhere, you may find some <a
   href="/tweets.html">recent Twitter tweets</a>, and a diary of shorter
   entries named <a href="/notes/Journal_arts_t.html">Journal arts</a>,
   in French mainly, relating my humble explorations about images and
   sounds.
  </p>

  <p>
   The blog entry sources, previously held in reStructuredText format,
   have been translated as Tomboy notes.  Little glitches from this
   conversion will be polished out over time.
  </p>
""")
        return ''.join(fragments)

    def epilog(self):
        return """\
 </body>
</html>
"""

    def table_of_contents(self, entries):
        fragments = []
        write = fragments.append
        write("""\
<h1>Contents</h1>
<table align="center">
 <tr><th>Nº</th><th>Date</th><th>Title</th></tr>
""")
        for counter, (title, date) in enumerate(entries):
            write(' <tr>\n'
                  '  <td align="center">%d</td>\n'
                  '  <td>%s</td>\n'
                  '  <td><a href="#%s">%s</a></td>\n'
                  ' </tr>\n'
                  % (len(entries) - counter, date,
                     self.escape(title).replace(' ', '-'),
                     self.escape(tools.pretty_title(title))))
        write("""\
</table>
""")
        return ''.join(fragments)

    def convert_from_title(self, title, converter):
        note = tools.Note.registry.get(title)
        if note is not None:
            return converter.convert(note, blog=True)
        self.run.report_error(title, "Not found")

    def blog_section(self, title, text):
        fragments = []
        write = fragments.append
        write('<hr class=ruler />\n'
              '<a name="%s" />\n' % self.escape(title).replace(' ', '-'))
        write(text)
        return ''.join(fragments)
