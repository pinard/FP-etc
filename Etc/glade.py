#!/usr/bin/env python3
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003-02.

"""\
Facilitateur pour l'usage de `libglade'.
"""


class Glade:

    def __init__(self, project, names, connections):
        import libglade
        import os
        fichier_xml = project + '.glade'
        if not os.path.exists(fichier_xml):
            fichier_xml = '/usr/local/share/glade/' + fichier_xml
        self.ui = libglade.GladeXML(fichier_xml)
        for name in names:
            setattr(self, name, self.ui.get_widget(name))
        for connection in connections:
            self.ui.signal_connect(connection, getattr(self, connection))

    def mainloop(self):
        import gtk
        gtk.mainloop()

    def mainquit(self, widget):
        import gtk
        gtk.mainquit()

    def refresh(self):
        import gtk
        while gtk.events_pending():
            gtk.mainiteration()
