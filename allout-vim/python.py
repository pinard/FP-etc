#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003.

"""\
Allout support for Vim.
"""

from __future__ import generators
import sys, vim

def register_key_bindings(normal_leader, insert_leader):
    for key, modes, name in (
            ('j',    'ni', 'next_visible_heading'),
            ('k',    'n',  'previous_visible_heading'),
            ('u',    'n',  'up_current_level'),
            ('l',    'n',  'forward_current_level'),
            ('h',    'n',  'backward_current_level'),
            ('$',    'n',  'end_of_current_entry'),
            ('^',    'n',  'beginning_of_current_entry'),
            ('c',    'n',  'hide_current_subtree'),
            ('i',    'n',  'show_children'),
            ('o',    'n',  'show_current_subtree'),
            ('O',    'n',  'show_all'),
            ('0',    'n',  'show_current_entry'),
            ('_',    'n',  'open_sibtopic'),
            ('+',    'n',  'open_subtopic'),
            ('-',    'n',  'open_supertopic'),
            ('=',    'n',  'normalize_margin'),
            ('>',    'nv', 'shift_in'),
            ('<',    'nv', 'shift_out'),
            ('<CR>', 'n',  'rebullet_topic'),
            ('#',    'n',  'number_siblings'),
            ('~',    'n',  'revoke_numbering'),
            ('v',    'n',  'visual_topic'),
            ('D',    'n',  'kill_topic'),
            ):
        for mode in modes:
            python_command = ':python allout.%s(\'%s\')' % (name, mode)
            sid_name = '<SID>%s_%s' % (mode, name)
            plug_name = '<Plug>Allout_%s_%s' % (mode, name)
            mapped = int(vim.eval('hasmapto(\'%s\')' % plug_name))
            if mode == 'i':
                if not mapped:
                    vim.command('%smap <buffer> <unique> %s%s %s'
                                % (mode, insert_leader, key, plug_name))
                vim.command('%snoremap <buffer> %s <C-O>%s<CR>'
                            % (mode, sid_name, python_command))
            else:
                if not mapped:
                    vim.command('%smap <buffer> <unique> %s%s %s'
                                % (mode, normal_leader, key, plug_name))
                vim.command('%snoremap <buffer> %s %s<CR>'
                            % (mode, sid_name, python_command))
            vim.command('%snoremap <buffer> <unique> <script> %s %s'
                         % (mode, plug_name, sid_name))

# A Vim cursor has a 1-based ROW and a 0-based COL.  Beware than in its
# mode line, Vim displays both ROW and COL as 1-based.

# Navigation.

def next_visible_heading(mode):
    for row, level in all_following_lines(mode + 's'):
        if level is not None:
            vim.current.window.cursor = row, level + 1
            return
    no_such_line()

def previous_visible_heading(mode):
    for row, level in all_preceding_lines(mode + 's'):
        if level is not None:
            vim.current.window.cursor = row, level + 1
            return
    no_such_line()

def up_current_level(mode):
    heading_row, heading_level = heading_line(mode + 's')
    for row, level in all_preceding_lines(mode + 's', heading_row):
        if level is not None and level < heading_level:
            vim.current.window.cursor = row, level + 1
            return
    no_such_line()

def forward_current_level(mode):
    heading_row, heading_level = heading_line(mode + 's')
    for row, level in all_following_lines(mode + 's'):
        if level is not None:
            if level == heading_level:
                vim.current.window.cursor = row, level + 1
                return
            if level < heading_level:
                break
    no_such_line()

def backward_current_level(mode):
    heading_row, heading_level = heading_line(mode + 's')
    for row, level in all_preceding_lines(mode + 's', heading_row):
        if level is not None:
            if level == heading_level:
                vim.current.window.cursor = row, level + 1
                return
            if level < heading_level:
                break
    no_such_line()

def end_of_current_entry(mode):
    row = None
    for row in all_text_lines(mode + 's'):
        pass
    if row is not None:
        vim.current.window.cursor = row, 0
        vim.command('normal $')

def beginning_of_current_entry(mode):
    for row in all_text_lines(mode + 's'):
        vim.current.window.cursor = row, 0
        vim.command('normal ^')
        break

# Exposure control.

def hide_current_subtree(mode):
    row, level = row_and_level()
    if level is None:
        vim.command('normal zc')
    else:
        try:
            row = all_text_lines(mode + 's').next()
        except StopIteration:
            pass
        else:
            cursor = vim.current.window.cursor
            vim.current.window.cursor = row, 0
            vim.command('normal zc')
            vim.current.window.cursor = cursor

def show_children(mode):
    heading_row, heading_level = heading_line(mode)
    cursor = vim.current.window.cursor
    for row, level in all_level_lines(mode):
        if level is None:
            if not is_invisible(row):
                vim.current.window.cursor = row, 0
                vim.command('normal zc')
        elif level == heading_level + 1:
            if is_invisible(row):
                vim.current.window.cursor = row, 0
                vim.command('normal zv')
    vim.current.window.cursor = cursor

def show_current_subtree(mode):
    cursor = vim.current.window.cursor
    for row, level in all_level_lines(mode):
        if is_invisible(row):
            vim.current.window.cursor = row, 0
            vim.command('normal zv')
            break
    vim.current.window.cursor = cursor

def show_all(mode):
    cursor = vim.current.window.cursor
    for row, level in all_level_lines(mode):
        if is_invisible(row):
            vim.current.window.cursor = row, 0
            vim.command('normal zv')
    vim.current.window.cursor = cursor

def show_current_entry(mode):
    for row in all_text_lines(mode):
        if is_invisible(row):
            vim.current.window.cursor = row, 0
            vim.command('normal zv')
    row, level = heading_line(mode, row)
    vim.current.window.cursor = row, level + 1

# Topic heading production.

def open_sibtopic(mode):
    row, level = heading_line(mode)
    level, bullet, number, line = split_line(row)
    for row in all_text_lines(mode):
        pass
    if number is not None:
        number += 1
    vim.current.buffer[row+1:row+1] = ['', '']
    build_line(row + 2, level, bullet, number, '')
    vim.current.window.cursor = row + 2, level + 1

def open_subtopic(mode):
    row, level = heading_line(mode)
    for row in all_text_lines(mode):
        pass
    vim.current.buffer[row+1:row+1] = ['', '']
    build_line(row + 2, level + 1, '.', None, '')
    vim.current.window.cursor = row + 2, level + 2

def open_supertopic(mode):
    heading_row, heading_level = heading_line(mode)
    for row, level in all_preceding_lines(mode, heading_row):
        if level is not None and level < heading_level:
            level, bullet, number, line = split_line(row)
            break
    else:
        no_such_line()
        return
    row = heading_row
    for row in all_text_lines(mode):
        pass
    if number is not None:
        number += 1
    vim.current.buffer[row+1:row+1] = ['', '']
    build_line(row + 2, level, '.', None, '')
    vim.current.window.cursor = row + 2, level + 1

# Topic level and prefix adjustment.

def normalize_margin(mode):
    before = None
    for row in all_text_lines(mode):
        line = line_at(row)
        margin = len(line) - len(line.lstrip())
        if before is None or margin < before:
            before = margin
    if before is not None:
        row, level = heading_line(mode + 's')
        if level == 0:
            after = 0
        else:
            after = level + 1
        delta = after - before
        for row in all_text_lines(mode):
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, number, line, delta)

def shift_in(mode):
    debug()
    for row, level in all_level_lines(mode):
        level, bullet, number, line = split_line(row)
        build_line(row, level, bullet, number, line, 1)

def shift_out(mode):
    for row, level in all_level_lines(mode):
        level, bullet, number, line = split_line(row)
        build_line(row, level, bullet, number, line, -1)

def rebullet_topic(mode):
    row, level = heading_line(mode + 's')
    level, bullet, number, line = split_line(row)
    build_line(row, level, bullet, number, line)

def number_siblings(mode):
    heading_row, heading_level = heading_line(mode)
    ordinal = 0
    for row, level in all_level_lines(mode):
        if level == heading_level + 1:
            ordinal += 1
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, ordinal, line)

def revoke_numbering(mode):
    heading_row, heading_level = heading_line(mode)
    ordinal = 0
    for row, level in all_level_lines(mode):
        if level == heading_level + 1:
            ordinal += 1
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, None, line)

# Topic oriented killing and yanking.

def visual_topic(mode):
    start = None
    for row, level in all_level_lines(mode):
        if start is None:
            start = row
    if start is None:
        no_such_line()
    else:
        vim.command('normal %dGV%dG' % (row, start))

def kill_topic(mode):
    start = None
    for row, level in all_level_lines(mode):
        if start is None:
            start = row
    if start is None:
        no_such_line()
    else:
        vim.command('normal %dGd%dG' % (row, start))

# Service functions.

# MODE is a sequence of flag letters.  Currently, there are one or two
# letters.  The first letter is `n' when commands executed in normal
# mode, `v' when in visual mode, or `i' when in insert mode.  The second
# letter may be `s' to skip over the contents of closed folds.

# By convention, a ROW of None implies the current row.  LEVEL is None
# for a non-header text line, 1 for `*' headers, 2 for `..' headers, 3
# for `. :' headers, etc.  If first line of file is not a heading, an
# hypothetical 0-level heading is sometimes assumed.  When an necessary
# operation cannot be performed because a line does not exist, functions
# raise StopIteration.

def all_level_lines(mode, row=None):
    # In normal mode, generates all (ROW, LEVEL) for headers and non-empty
    # text lines within the whole level holding ROW, including it sub-levels.
    # LEVEL is zero for non-header lines.  In visual mode, generates (ROW,
    # LEVEL) for all non-empty selected lines.
    if 'n' in mode:
        heading_row, heading_level = heading_line(mode, row)
        yield heading_row, heading_level
        for row, level in all_following_lines(mode, heading_row):
            if level is not None and level <= heading_level:
                break
            yield row, level
    elif 'v' in mode:
        assert row is None, row
        for row, level in all_following_lines(mode):
            yield row, level

def all_text_lines(mode, row=None):
    # In normal mode, generates all rows for non-empty text lines after the
    # heading for the level holding ROW (None implies current row).  In visual
    # mode, generates all rows for non-empty non-header lines.
    if 'n' in mode:
        row, level = heading_line(mode, row)
        for row, level in all_following_lines(mode, row):
            if level is not None:
                break
            yield row
    elif 'v' in mode:
        assert row is None, row
        for row, level in all_following_lines(mode):
            if level is None:
                yield row

def heading_line(mode, row=None):
    # Returns (ROW, LEVEL) for the closest heading at or before ROW.
    assert 'n' in mode, mode
    row, level = row_and_level()
    if level is None:
        for row, level in all_preceding_lines(mode, row):
            if level is not None:
                break
        else:
            return 1, 0
    return row, level

def all_following_lines(mode, row=None):
    # In normal mode, generates (ROW, LEVEL) forward for all non-empty lines
    # after ROW.  In visual mode, generates (ROW, LEVEL) for all non-empty
    # selected lines from first to last.
    buffer = vim.current.buffer
    if 'n' in mode:
        if row is None:
            row, col = vim.current.window.cursor
        row = int(vim.eval('nextnonblank(%d)' % (row + 1)))
        last = len(buffer)
    elif 'v' in mode:
        assert row is None, row
        row, col = buffer.mark('<')
        if not line_at(row):
            row = int(vim.eval('nextnonblank(%d)' % (row + 1)))
        last, col = buffer.mark('>')
    if 's' in mode:
        while 0 < row <= last:
            last = int(vim.eval('foldclosedend(%d)' % row))
            if last < 0:
                yield row_and_level(row)
            else:
                row = last
            row = int(vim.eval('nextnonblank(%d)' % (row + 1)))
    else:
        while 0 < row <= last:
            yield row_and_level(row)
            row = int(vim.eval('nextnonblank(%d)' % (row + 1)))

def all_preceding_lines(mode, row=None):
    # In normal mode, generates (ROW, LEVEL) backwards for all non-empty lines
    # before ROW.  In visual mode, generates (ROW, LEVEL) for all non-empty
    # selected lines from last to first.
    buffer = vim.current.buffer
    if 'n' in mode:
        if row is None:
            row, col = vim.current.window.cursor
        row = int(vim.eval('prevnonblank(%d)' % (row - 1)))
        first = 1
    elif 'v' in mode:
        assert row is None, row
        row, col = buffer.mark('>')
        if not line_at(row):
            row = int(vim.eval('prevnonblank(%d)' % (row - 1)))
        first, col = buffer.mark('<')
    if 's' in mode:
        while first <= row:
            first = int(vim.eval('foldclosed(%d)' % row))
            if first < 0:
                yield row_and_level(row)
            else:
                row = first
            row = int(vim.eval('prevnonblank(%d)' % (row - 1)))
    else:
        while first <= row:
            yield row_and_level(row)
            row = int(vim.eval('prevnonblank(%d)' % (row - 1)))

def row_and_level(row=None):
    # Returns (ROW, LEVEL) for line at ROW.
    if row is None:
        row, col = vim.current.window.cursor
    line = vim.current.buffer[row-1]
    if not line:
        return row, None
    if line[0] == '*':
        return row, 1
    if line[0] == '.':
        text = line[1:].lstrip()
        if text and text[0] in '-*+@#.:,;':
            return row, len(line) - len(text) + 1
    return row, None

def split_line(row=None):
    # Returns (LEVEL, BULLET, NUMBER, LINE) from the contents of line at ROW.
    # For an header line, LEVEL is the header level, BULLET is the bullet
    # character of the header, and NUMBER is either None or the value of the
    # number following a `#' bullet; LINE is the header contents with the
    # whole header prefix removed, None if empty.  For a non-header line,
    # LEVEL, BULLET and NUMBER are None, LINE is the original line contents.
    line = line_at(row)
    if not line:
        return None, None, None, ''
    level = number = None
    if line[0] == '*':
        level = 1
        bullet = '*'
        line = line[1:].lstrip()
    elif line[0] == '.':
        text = line[1:].lstrip()
        if text:
            bullet = text[0]
            text = text[1:]
            if bullet == '#':
                if text and text[0].isdigit():
                    fields = text.split(None, 1)
                    try:
                        number = int(fields[0])
                    except ValueError:
                        pass
                    else:
                        level = len(line) - len(text)
                        if len(fields) == 1:
                            line = None
                        else:
                            line = fields[1]
            elif bullet in '-*+@.:,;':
                level = len(line) - len(text)
                line = text.lstrip()
    if level is None:
        bullet = None
    return level, bullet, number, line

def build_line(row=None, level=None, bullet='.', number=None, line=None,
               delta=0):
    # Reconstructs line at ROW from LEVEL, BULLET, NUMBER and LINE as obtained
    # from `split_line'.  While doing so, adjust level by adding DELTA to it.
    # DELTA may either be positive or negative.  Header lines may have their
    # bullet changed and/or repositioned.  Non-header lines may have their
    # margin adjusted.  If NUMBER is not None, and if bullet is not `@', that
    # number is used to constructs a `#N' bullet which overrides BULLET.  If
    # NUMBER is None, a `#' value for BULLET is overridden by another one.
    if row is None:
        row, col = vim.current.window.cursor
    buffer = vim.current.buffer
    if level is None:
        if delta < 0:
            margin = len(line) - len(line.lstrip())
            if -delta < margin:
                buffer[row-1] = line[-delta:]
            elif margin > 0:
                buffer[row-1] = line[margin:]
            else:
                buffer[row-1] = line
        else:
            buffer[row-1] = ' ' * delta + line
    elif level + delta <= 0:
        buffer[row-1] = line
    else:
        if level + delta == 1:
            prefix = '*'
        else:
            if bullet != '@':
                if number is not None:
                    bullet = '#' + str(number)
                elif level == 1 or bullet in '.:,;#':
                    bullet = '.:,;'[(level + delta - 2) % 4]
            prefix = '.' + ' ' * (level + delta - 2) + bullet
        if line is None:
            buffer[row-1] = prefix
        else:
            buffer[row-1] = prefix + ' ' + line

def is_invisible(row=None):
    # Tells if the line at ROW is within a currently closed fold.
    if row is None:
        row, col = vim.current.window.cursor
    return int(vim.eval('foldclosed(%d)' % row)) >= 0

def line_at(row=None):
    # Returns the text of line at ROW.
    if row is None:
        row, col = vim.current.window.cursor
    return vim.current.buffer[row-1]

def no_such_line():
    error("No such line.")

def error(message):
    vim.command('echohl WarningMsg | echo "%s" | echohl None'
                % message.rstrip().replace('"', '\\"'))

def debug():
    print repr(vim.eval('mode()')), 
    print repr(vim.eval('line("\'<")')),
    print repr(vim.eval('line("\'>")'))
