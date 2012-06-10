#!/usr/bin/env python3
# Copyright © 2007 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2007.

"""\
Unicode wrapper for "import vim" within Python-enabled Vim.

Usage: from Etc.UniVim import vim
"""

charset = 'UTF-8'


class Wrapper:
    import vim
    buffer_type = type(vim.current.buffer)

    def __init__(self, object):
        self.object = object

    def __getattr__(self, name):
        value = getattr(self.object, name)
        if isinstance(value, (int, tuple)):
            return value
        if isinstance(value, str):
            return value.decode(charset)
        if isinstance(value, self.buffer_type):
            return Buffer(value)
        return Wrapper(value)


class Buffer(Wrapper):

    def __len__(self):
        return len(self.object)

    def __getitem__(self, index):
        return self.object[index].decode(charset)

    def __setitem__(self, index, value):
        self.object[index] = value.encode(charset)

    def __getslice__(self, low, high):
        return [value.decode(charset) for value in self.object[low:high]]

    def __setslice__(self, low, high, sequence):
        self.object[low:high] = [value.encode(charset) for value in sequence]

    def append(self, value):
        if isinstance(value, str):
            self.object.append(value.encode(charset))
        elif isinstance(value, list):
            self.object.append([text.encode(charset) for text in value])
        else:
            self.object.append(value)

    def mark(self, text):
        return self.object.mark(text.encode(charset))

#class Message(Wrapper):
#
#    def write(self, text):
#        self.object.write(text.encode(charset))
#
#    def writelines(self, lines):
#        for line in lines:
#            self.write(line)
#
#class Sys(Wrapper):
#    import sys as object
#    stdout = Message(object.stdout)
#    stderr = Message(object.stderr)
#
#    def __init__(self): pass


class Vim(Wrapper):
    import vim as object

    def __init__(self):
        pass

    def command(self, text):
        self.object.command(text.encode(charset))

    def eval(self, text):
        return self.object.eval(text.encode(charset)).decode(charset)

#sys = Sys()
vim = Vim()
