#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003-05.

u"""\
Traitements Babyl ou mbox fréquents: partie mise en commun.
"""

import os, time, sys
from email import message_from_string
from email.Errors import MessageError

class Error(Exception): pass

def folder(file_name, strip201=False):
    if file_name:
        if not os.path.isfile(file_name):
            raise Error, u"%s: File not found." % file_name
        buffer = file(file_name).read()
    else:
        buffer = sys.stdin.read()
    if strip201:
        count = buffer.count('\201')
        if count > 0:
            buffer = buffer.replace('\201', '')
    if buffer.startswith('BABYL OPTIONS:'):
        folder = Babyl(file_name, buffer)
    elif buffer.startswith('From '):
        folder = Mbox(file_name, buffer)
    else:
        raise Error, u"%s: Unknown format." % (file_name or '<stdin>')
    if strip201:
        folder.count201 = count
        if count > 0:
            folder.modified = True
    return folder

class Folder:
    # If FILE_NAME is not None, that folder file is being read and written.
    # Otherwise, standard input is read, and maybe written to standard output.
    file_name = None
    # If FILE_SIZE is not None, FILE_NAME pre-existed with that initial size.
    file_size = None

    def __init__(self, file_name, buffer=None):
        # If BUFFER is not None, it holds initial folder contents.  Otherwise,
        # the folder is being created.
        if file_name:
            self.file_name = file_name
        if buffer is None:
            if file_name and os.path.exists(file_name):
                self.error(u"May not create folder over an existing file.")
            self.data = []
            self.deleted = []
        else:
            if file_name:
                self.file_size = os.path.getsize(file_name)
            self.create_data(buffer)
            self.deleted = [False] * len(self.data)
        self.modified = False

    def rescan(self):
        if self.file_name is None:
            self.error(u"May not rescan standard input.")
        if self.file_size is None:
            self.error(u"May not rescan a file which did not exist.")
        try:
            size = os.path.getsize(self.file_name)
        except IOError:
            self.error(u"May not rescan a vanished folder.")
        if size < self.file_size:
            self.error(u"May not rescan a shrunk folder.")
        if size > self.file_size:
            input = file(self.file_name)
            input.seek(self.file_size)
            self.file_size = size
            self.extend_data(input.read())
            self.deleted += [False] * (len(self.data) - len(self.deleted))

    def __len__(self):
        return len(self.data)

    def mark_deleted(self, index):
        self.deleted[index] = True
        self.modified = True

    def chars_lines(self, index):
        (data, head_being, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        return body_end - body_begin, data.count('\n', body_begin, body_end)

    def message_headers(self, index):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        try:
            return message_from_string(data[head_begin:head_end])
        except MessageError, diagnostic:
            self.error(diagnostic, index)

    def message_body(self, index):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        return data[body_begin:body_end]

    def close(self, backup=None):
        if self.modified:
            if self.file_size is not None:
                if os.path.getsize(self.file_name) != self.file_size:
                    self.error(u"May not close a file which changed on disk.")
                if backup is None:
                    backup = self.file_name + '~'
                if os.path.exists(backup):
                    os.remove(backup)
                os.rename(self.file_name, backup)
            write = None
            for counter in range(len(self.data)):
                if not self.deleted[counter]:
                    if write is None:
                        if self.file_name is None:
                            write = sys.stdout.write
                        else:
                            write = file(self.file_name, 'w').write
                        if self.folder_prefix is not None:
                            write(self.folder_prefix)
                    self.write_indexed_message(counter, write)

    def error(self, diagnostic, index=None):
        file_name = self.file_name or '<stdin>'
        if index is None:
            raise Error('%s: %s' % (file_name, diagnostic))
        raise Error('%s:%s: %s' % (file_name, index+1, diagnostic))

class Babyl(Folder):
    folder_prefix = '''\
BABYL OPTIONS: -*- rmail -*-
Version: 5
Labels:
Note:   This is the header of an rmail file.
Note:   If you are seeing it in rmail,
Note:    it means the file has no messages in it.
\37\
'''
    article_prefix = '''
0, unseen,,
*** EOOH ***
'''
    eooh_string = '\n*** EOOH ***\n'

    def create_data(self, buffer):
        self.data = buffer.split('\37\f\n')
        if self.data and self.data[-1].endswith('\37'):
            self.data[-1] = self.data[-1][:-1]
        else:
            self.error(u"Folder does not end like a Babyl file.")
        if self.data[0].startswith('BABYL OPTIONS:'):
            self.folder_prefix = self.data.pop(0) + '\37'
        else:
            self.error(u"Folder does not start like a Babyl file.")

    def extend_data(self, buffer):
        data = buffer.split('\37\f\n')
        if data[-1].endswith('\37'):
            data[-1] = data[-1][:-1]
        else:
            self.error(u"Message does not end like a Babyl article.",
                       len(self.data) + len(data) - 1)
        if data[0].startswith('\f\n'):
            data[0] = date[0][2:]
        else:
            self.error(u"Message does not start like a Babyl article.",
                       len(self.data))
        self.data += data

    def append(self, text):
        self.data.append(self.article_prefix + text)
        self.deleted.append(False)
        self.modified = True

    def __getitem__(self, index):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        return ('%s\n%s' % (data[head_begin:head_end],
                            data[body_begin:body_end]))

    def __setitem__(self, index, text):
        if text != self[index]:
            self.data[index] = self.article_prefix + text
            self.modified = True

    def write_indexed_message(self, index, write):
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        write('\f\n')
        write(self.article_prefix)
        write(data[head_begin:head_end])
        write('\n')
        write(data[body_begin:body_end])
        write('\37')

    def find_head_body(self, index):
        # Returns (DATA, HEAD_BEGIN, HEAD_END, BODY_BEGIN, BODY_END), the
        # first being a string, all others being positions in that string.
        data = self.data[index]
        eooh = data.find(self.eooh_string)
        if eooh < 0:
            self.error(u"Missing EOOH within a Babyl article.", index)
        double_newline = data.find('\n\n', eooh)
        if double_newline < 0:
            self.error(u"Unterminated head within Babyl article.", index)
        body_begin = double_newline + 2
        body_end = len(data)
        if data.startswith('0'):
            head_begin = eooh + len(self.eooh_string)
            head_end = double_newline + 1
        elif data.startswith('1'):
            newline = data.find('\n', 0, eooh)
            if newline < 0:
                self.error(u"Invalid Babyl article.", index)
            head_begin = newline + 1
            head_end = eooh
        else:
            self.error(u"Invalid Babyl flag.", index)
        return data, head_begin, head_end, body_begin, body_end

class Mbox(Folder):
    folder_prefix = None

    def __init__(self, *arguments):
        self.envelope = []
        Folder.__init__(self, *arguments)

    def create_data(self, buffer):
        self.data = []
        self.extend_data(buffer)

    def extend_data(self, buffer):
        data = []
        envelope = []
        start = 0
        while start < len(buffer):
            end = buffer.find('\nFrom ', start)
            if end < 0:
                end = len(buffer)
            newline = buffer.find('\n', start, end)
            if newline < 0:
                self.error(u"Unterminated envelope in Mbox folder.",
                           len(self.data) + len(data))
            double_newline = buffer.find('\n\n', newline+1, end)
            if double_newline < 0:
                head = buffer[newline+1:end]
                if not head.endswith('\n'):
                    head += '\n'
                body = ''
            else:
                head = buffer[newline+1:double_newline+1]
                body = buffer[double_newline+2:end]
                if body.endswith('\n\n'):
                    body = body.rstrip() + '\n'
            data.append('%s\n%s' % (head, body.replace('\n>From', '\nFrom')))
            envelope.append(buffer[start+5:newline].strip())
            start = end + 2
        self.data += data
        self.envelope += envelope

    def append(self, text):
        self.data.append(text)
        self.envelope.append('folder.Mbox %s' % time.ctime(time.time()))
        self.deleted.append(False)
        self.modified = True

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, text):
        if text != self[index]:
            self.data[index] = text
            self.modified = True

    def write_indexed_message(self, index, write):
        write('From %s\n' % self.envelope[index])
        (data, head_begin, head_end, body_begin, body_end
         ) = self.find_head_body(index)
        write(data[head_begin:head_end])
        write('\n')
        body = data[body_begin:body_end]
        if body.startswith('From'):
            write('>')
        write(body.replace('\nFrom', '\n>From'))
        if not body.endswith('\n'):
            write('\n')
        write('\n')

    def find_head_body(self, index):
        # Returns (DATA, HEAD_BEGIN, HEAD_END, BODY_BEGIN, BODY_END), the
        # first being a string, all others being positions in that string.
        data = self.data[index]
        double_newline = data.find('\n\n')
        if double_newline < 0:
            return data, 0, len(data), len(data), len(data)
        return data, 0, double_newline + 1, double_newline + 2, len(data)
