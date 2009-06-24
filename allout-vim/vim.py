#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003.

"""\
Allout support for Vim.
"""

from __future__ import generators
import sys, vim

def register_key_bindings():
    # The Vim commands do not seem to work; I did not figure out why yet.
    # So for now, bindings get (tediously) established from `allout.vim'.
    for key, function in (
            ('j', next_visible_heading),
            ('k', previous_visible_heading),
            ('u', up_current_level),
            ('l', forward_current_level),
            ('h', backward_current_level),
            ('$', end_of_current_entry),
            ('^', beginning_of_current_entry),
            ('c', hide_current_subtree),
            ('i', show_children),
            ('o', show_current_subtree),
            ('O', show_all),
            ('0', show_current_entry),
            ('_', open_sibtopic),
            ('+', open_subtopic),
            ('-', open_supertopic),
            ('=', normalize_margin),
            ('>', shift_in),
            ('<', shift_out),
            ('<CR>', rebullet_topic),
            ('#', number_siblings),
            ('~', revoke_numbering),
            ('v', visual_topic),
            ('D', kill_topic),
            ):
        has_binding = int(vim.eval('hasmapto(\'<Plug>Allout_%s\')' % function))
        #if not has_binding:
        #    vim.command(
        #            'map <buffer> <unique> <LocalLeader>%s <Plug>Allout_%s'
        #            % (key, function))
        #vim.command(
        #        'noremap <buffer> <unique> <script> <Plug>Allout_%s <SID>%s'
        #        % (function, function))
        #vim.command(
        #        'noremap <buffer> <SID>%s :python allout.%s()<CR>'
        #        % (function, function))

# A Vim cursor has a 1-based ROW and a 0-based COL.  Beware than in its
# mode line, Vim displays both ROW and COL as 1-based.

# Navigation.

def next_visible_heading():
    for row, level in all_following_lines(skip=True):
        if level is not None:
            vim.current.window.cursor = row, level + 1
            return
    no_such_line()

def previous_visible_heading():
    for row, level in all_preceding_lines(skip=True):
        if level is not None:
            vim.current.window.cursor = row, level + 1
            return
    no_such_line()

def up_current_level():
    heading_row, heading_level = heading_line(skip=True)
    for row, level in all_preceding_lines(heading_row, skip=True):
        if level is not None and level < heading_level:
            vim.current.window.cursor = row, level + 1
            return
    no_such_line()

def forward_current_level():
    heading_row, heading_level = heading_line(skip=True)
    for row, level in all_following_lines(skip=True):
        if level is not None:
            if level == heading_level:
                vim.current.window.cursor = row, level + 1
                return
            if level < heading_level:
                break
    no_such_line()

def backward_current_level():
    heading_row, heading_level = heading_line(skip=True)
    for row, level in all_preceding_lines(heading_row, skip=True):
        if level is not None:
            if level == heading_level:
                vim.current.window.cursor = row, level + 1
                return
            if level < heading_level:
                break
    no_such_line()

def end_of_current_entry():
    row = None
    for row in all_text_lines(skip=True):
        pass
    if row is not None:
        vim.current.window.cursor = row, 0
        vim.command('normal $')

def beginning_of_current_entry():
    for row in all_text_lines(skip=True):
        vim.current.window.cursor = row, 0
        vim.command('normal ^')
        break

# Exposure control.

def hide_current_subtree():
    row, level = row_and_level()
    if level is None:
        vim.command('normal zc')
    else:
        try:
            row = all_text_lines(skip=True).next()
        except StopIteration:
            pass
        else:
            cursor = vim.current.window.cursor
            vim.current.window.cursor = row, 0
            vim.command('normal zc')
            vim.current.window.cursor = cursor

def show_children():
    heading_row, heading_level = heading_line()
    cursor = vim.current.window.cursor
    for row, level in all_level_lines():
        if level is None:
            if not is_invisible(row):
                vim.current.window.cursor = row, 0
                vim.command('normal zc')
        elif level == heading_level + 1:
            if is_invisible(row):
                vim.current.window.cursor = row, 0
                vim.command('normal zv')
    vim.current.window.cursor = cursor

def show_current_subtree():
    cursor = vim.current.window.cursor
    for row, level in all_level_lines():
        if is_invisible(row):
            vim.current.window.cursor = row, 0
            vim.command('normal zv')
            break
    vim.current.window.cursor = cursor

def show_all():
    cursor = vim.current.window.cursor
    for row, level in all_level_lines():
        if is_invisible(row):
            vim.current.window.cursor = row, 0
            vim.command('normal zv')
    vim.current.window.cursor = cursor

def show_current_entry():
    for row in all_text_lines():
        if is_invisible(row):
            vim.current.window.cursor = row, 0
            vim.command('normal zv')
    row, level = heading_line(row)
    vim.current.window.cursor = row, level + 1

# Topic heading production.

def open_sibtopic():
    row, level = heading_line()
    level, bullet, number, line = split_line(row)
    for row in all_text_lines():
        pass
    if number is not None:
        number += 1
    vim.current.buffer[row+1:row+1] = ['', '']
    build_line(row + 2, level, bullet, number, '')
    vim.current.window.cursor = row + 2, level + 1

def open_subtopic():
    row, level = heading_line()
    for row in all_text_lines():
        pass
    vim.current.buffer[row+1:row+1] = ['', '']
    build_line(row + 2, level + 1, '.', None, '')
    vim.current.window.cursor = row + 2, level + 2

def open_supertopic():
    heading_row, heading_level = heading_line()
    for row, level in all_preceding_lines(heading_row):
        if level is not None and level < heading_level:
            level, bullet, number, line = split_line(row)
            break
    else:
        no_such_line()
        return
    row = heading_row
    for row in all_text_lines():
        pass
    if number is not None:
        number += 1
    vim.current.buffer[row+1:row+1] = ['', '']
    build_line(row + 2, level, '.', None, '')
    vim.current.window.cursor = row + 2, level + 1

# Topic level and prefix adjustment.

def normalize_margin():
    before = None
    for row in all_text_lines():
        line = line_at(row)
        margin = len(line) - len(line.lstrip())
        if before is None or margin < before:
            before = margin
    if before is not None:
        row, level = heading_line(skip=True)
        if level == 0:
            after = 0
        else:
            after = level + 1
        delta = after - before
        for row in all_text_lines():
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, number, line, delta)

def shift_in():
    for row, level in all_level_lines():
        level, bullet, number, line = split_line(row)
        build_line(row, level, bullet, number, line, 1)

def shift_out():
    for row, level in all_level_lines():
        level, bullet, number, line = split_line(row)
        build_line(row, level, bullet, number, line, -1)

def rebullet_topic():
    row, level = heading_line(skip=True)
    level, bullet, number, line = split_line(row)
    build_line(row, level, bullet, number, line)

def number_siblings():
    heading_row, heading_level = heading_line()
    ordinal = 0
    for row, level in all_level_lines():
        if level == heading_level + 1:
            ordinal += 1
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, ordinal, line)

def revoke_numbering():
    heading_row, heading_level = heading_line()
    ordinal = 0
    for row, level in all_level_lines():
        if level == heading_level + 1:
            ordinal += 1
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, None, line)

# Topic oriented killing and yanking.

def visual_topic():
    start = None
    for row, level in all_level_lines():
        if start is None:
            start = row
    if start is None:
        no_such_line()
    else:
        vim.command('normal %dGV%dG' % (row, start))

def kill_topic():
    start = None
    for row, level in all_level_lines():
        if start is None:
            start = row
    if start is None:
        no_such_line()
    else:
        vim.command('normal %dGd%dG' % (row, start))

# Service functions.

# By convention, a ROW of None implies the current row.  LEVEL is None for a
# non-header text line, 1 for `*' headers, 2 for `..' headers, 3 for `. :'
# headers, etc.  If first line of file is not a heading, an hypothetical
# 0-level heading is sometimes assumed.  When SKIP is true, folded lines are
# skipped.  When an necessary operation cannot be performed because a line
# does not exist, functions raise StopIteration.

def all_level_lines(row=None, skip=False):
    # Generates all (ROW, LEVEL) for headers and non-empty text lines
    # within the whole level holding ROW, including it sub-levels.
    # LEVEL is zero for non-header lines.
    heading_row, heading_level = heading_line(row, skip)
    yield heading_row, heading_level
    for row, level in all_following_lines(heading_row, skip):
        if level is not None and level <= heading_level:
            break
        yield row, level

def all_text_lines(row=None, skip=False):
    # Generates all rows for non-empty text lines after the heading for the
    # level holding ROW (None implies current row).
    row, level = heading_line(row, skip)
    for row, level in all_following_lines(row, skip):
        if level is not None:
            break
        yield row

def heading_line(row=None, skip=False):
    # Returns (ROW, LEVEL) for the closest heading at or before ROW.
    row, level = row_and_level()
    if level is None:
        for row, level in all_preceding_lines(row, skip):
            if level is not None:
                break
        else:
            return 1, 0
    return row, level

def all_following_lines(row=None, skip=False):
    # Generates (ROW, LEVEL) forward for all non-empty line after ROW.
    if row is None:
        row, col = vim.current.window.cursor
    row = int(vim.eval('nextnonblank(%d)' % (row + 1)))
    while row:
        if skip:
            last = int(vim.eval('foldclosedend(%d)' % row))
            if last < 0:
                yield row_and_level(row)
            else:
                row = last
        else:
            yield row_and_level(row)
        row = int(vim.eval('nextnonblank(%d)' % (row + 1)))

def all_preceding_lines(row=None, skip=False):
    # Generates (ROW, LEVEL) backwards for all non-empty line before ROW.
    if row is None:
        row, col = vim.current.window.cursor
    row = int(vim.eval('prevnonblank(%d)' % (row - 1)))
    while row:
        if skip:
            first = int(vim.eval('foldclosed(%d)' % row))
            if first < 0:
                yield row_and_level(row)
            else:
                row = first
        else:
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
