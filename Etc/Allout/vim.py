#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2003.

u"""\
Allout support for Vim.
"""

__metaclass__ = type
from Etc.Unicode import apply, deunicode, file, open, os, reunicode, sys
from Etc.UniVim import vim

def install_with_vim():
    register_local_keys(u'allout',
                        ((u'<LocalLeader>j', u'n', u'next_visible_topic'),
                         (u'<LocalLeader>J', u'n', u'last_visible_topic'),
                         (u'<LocalLeader>k', u'n', u'previous_visible_topic'),
                         (u'<LocalLeader>K', u'n', u'first_visible_topic'),
                         (u'<LocalLeader>l', u'n', u'next_sibling'),
                         (u'<LocalLeader>L', u'n', u'last_sibling'),
                         (u'<LocalLeader>h', u'n', u'previous_sibling'),
                         (u'<LocalLeader>H', u'n', u'first_sibling'),
                         (u'<LocalLeader>u', u'n', u'up_level'),
                         (u'<LocalLeader>1', u'n', u'down_to_1st_child'),
                         (u'<LocalLeader>2', u'n', u'down_to_2nd_child'),
                         (u'<LocalLeader>3', u'n', u'down_to_3rd_child'),
                         (u'<LocalLeader>4', u'n', u'down_to_4th_child'),
                         (u'<LocalLeader>5', u'n', u'down_to_5th_child'),
                         (u'<LocalLeader>6', u'n', u'down_to_6th_child'),
                         (u'<LocalLeader>7', u'n', u'down_to_7th_child'),
                         (u'<LocalLeader>8', u'n', u'down_to_8th_child'),
                         (u'<LocalLeader>9', u'n', u'down_to_9th_child'),
                         (u'<LocalLeader>^', u'n', u'beginning_of_text'),
                         (u'<LocalLeader>$', u'n', u'end_of_text'),
                         (u'<LocalLeader>v', u'n', u'visual_text'),
                         (u'<LocalLeader>V', u'n', u'visual_level'),
                         (u'<LocalLeader>c', u'n', u'hide_text'),
                         (u'<LocalLeader>C', u'n', u'hide_level'),
                         (u'<LocalLeader>o', u'n', u'show_text'),
                         (u'<LocalLeader>O', u'n', u'show_level'),
                         (u'<LocalLeader>i', u'n', u'show_children'),
                         (u'<LocalLeader>=', u'n', u'create_sibling'),
                         (u'<LocalLeader>+', u'n', u'create_subtopic'),
                         (u'<LocalLeader>-', u'n', u'create_supertopic'),
                         (u'<LocalLeader>d', u'n', u'delete_text'),
                         (u'<LocalLeader>D', u'n', u'delete_level'),
                         (u'<LocalLeader><CR>', u'nv', u'rebullet_topic'),
                         (u'<LocalLeader>#', u'nv', u'number_siblings'),
                         (u'<LocalLeader>~', u'nv', u'revoke_numbering'),
                         (u'<LocalLeader><Bar>', u'nv', u'adjust_margin'),
                         (u'<LocalLeader>0', u'nv', u'remove_margin'),
                         (u'<LocalLeader>>', u'nv', u'shift_in'),
                         (u'<LocalLeader><', u'nv', u'shift_out'),
                         (u'<LocalLeader>_', u'n', u'space_topic')))

def register_local_keys(plugin, triplets):
    for keys, modes, name in triplets:
        for mode in modes:
            python_command = u':python %s.%s(\'%s\')' % (plugin, name, mode)
            sid_name = u'<SID>%s_%s' % (mode, name)
            plug_name = u'<Plug>%s_%s_%s' % (plugin.capitalize(), mode, name)
            vim.command(u'%smap <buffer> %s %s'
                        % (mode, keys, plug_name))
            vim.command(u'%snoremap <buffer> <script> %s %s'
                        % (mode, plug_name, sid_name))
            if mode == u'i':
                vim.command(u'%snoremap <buffer> <silent> %s <C-O>%s<CR>'
                            % (mode, sid_name, python_command))
            else:
                vim.command(u'%snoremap <buffer> <silent> %s %s<CR>'
                            % (mode, sid_name, python_command))
 
## Mapped functions.

# Navigation.

def next_visible_topic(mode):
    for row, level in all_following_lines(mode + u's'):
        if level is not None:
            move_cursor(row, level)
            return
    no_such_line()

def last_visible_topic(mode):
    last_row = None
    for row, level in all_following_lines(mode + u's'):
        if level is not None:
            last_row = row
            last_level = level
    if last_row is None:
        no_such_line()
    else:
        move_cursor(last_row, last_level)

def previous_visible_topic(mode):
    for row, level in all_preceding_lines(mode + u's'):
        if level is not None:
            move_cursor(row, level)
            return
    no_such_line()

def first_visible_topic(mode):
    first_row = None
    for row, level in all_preceding_lines(mode + u's'):
        if level is not None:
            first_row = row
            first_level = level
    if first_row is None:
        no_such_line()
    else:
        move_cursor(first_row, first_level)

def next_sibling(mode):
    topic_row, topic_level = topic_line()
    for row, level in all_following_lines(mode + u's'):
        if level is not None:
            if level == topic_level:
                move_cursor(row, level)
                return
            if level < topic_level:
                break
    no_such_line()

def last_sibling(mode):
    topic_row, topic_level = topic_line()
    last_row = None
    for row, level in all_following_lines(mode + u's'):
        if level is not None:
            if level == topic_level:
                last_row = row
                last_level = level
            elif level < topic_level:
                break
    if last_row is None:
        no_such_line()
    else:
        move_cursor(last_row, last_level)

def previous_sibling(mode):
    topic_row, topic_level = topic_line()
    for row, level in all_preceding_lines(mode + u's', topic_row):
        if level is not None:
            if level == topic_level:
                move_cursor(row, level)
                return
            if level < topic_level:
                break
    no_such_line()

def first_sibling(mode):
    topic_row, topic_level = topic_line()
    for row, level in all_preceding_lines(mode + u's', topic_row):
        if level is not None:
            if level == topic_level:
                first_row = row
                first_level = level
            elif level < topic_level:
                break
    if first_row is None:
        no_such_line()
    else:
        move_cursor(first_row, first_level)

def up_level(mode):
    topic_row, topic_level = topic_line()
    for row, level in all_preceding_lines(mode, topic_row):
        if level is not None and level < topic_level:
            move_cursor(row, level)
            return
    no_such_line()

def down_to_1st_child(mode): down_to_nth_child(mode, 1)
def down_to_2nd_child(mode): down_to_nth_child(mode, 2)
def down_to_3rd_child(mode): down_to_nth_child(mode, 3)
def down_to_4th_child(mode): down_to_nth_child(mode, 4)
def down_to_5th_child(mode): down_to_nth_child(mode, 5)
def down_to_6th_child(mode): down_to_nth_child(mode, 6)
def down_to_7th_child(mode): down_to_nth_child(mode, 7)
def down_to_8th_child(mode): down_to_nth_child(mode, 8)
def down_to_9th_child(mode): down_to_nth_child(mode, 9)

def down_to_nth_child(mode, which):
    # Service for the nine above functions only.
    topic_row, topic_level = topic_line()
    for row, level in all_level_lines(mode):
        if level is not None and level == topic_level + 1:
            which -= 1
            if which == 0:
                move_cursor(row, level)
                return
    no_such_line()

def beginning_of_text(mode):
    for row in all_text_lines(mode + u's'):
        vim.current.window.cursor = row, 0
        vim.command(u'normal ^')
        break

def end_of_text(mode):
    row = None
    for row in all_text_lines(mode + u's'):
        pass
    if row is not None:
        vim.current.window.cursor = row, 0
        vim.command(u'normal $')

def visual_text(mode):
    act_on_region(mode, u'V', all_text_lines)

def visual_level(mode):
    act_on_region(mode, u'V', all_level_lines)

# Exposure control.

def hide_text(mode):
    row, level = row_and_level()
    if level is None:
        vim.command(u'normal zc')
    else:
        try:
            row = all_text_lines(mode + u's').next()
        except StopIteration:
            pass
        else:
            command_at(row, u'normal zc')

def hide_level(mode):
    first = True
    for row, level in all_level_lines(mode):
        if first:
            if is_invisible(row):
                command_at(row, u'normal zv')
            first = False
        else:
            if not is_invisible(row):
                command_at(row, u'normal zc')

def show_text(mode):
    for row in all_text_lines(mode):
        if is_invisible(row):
            command_at(row, u'normal zv')

def show_level(mode):
    for row, level in all_level_lines(mode):
        if is_invisible(row):
            command_at(row, u'normal zv')

def show_children(mode):
    topic_row, topic_level = topic_line()
    for row, level in all_level_lines(mode):
        if level is None:
            if not is_invisible(row):
                command_at(row, u'normal zc')
        elif level == topic_level + 1:
            if is_invisible(row):
                command_at(row, u'normal zv')

# Topics.

def create_sibling(mode):
    row, level = topic_line()
    level, bullet, number, line = split_line(row)
    row = row_of_created_empty(mode, row)
    if number is not None:
        number += 1
    build_line(row, level, bullet, number, u'')
    move_cursor(row, level)
    vim.command(u'startinsert')

def create_subtopic(mode):
    row, level = topic_line()
    row = row_of_created_empty(mode, row)
    build_line(row, level + 1, u'.', None, u'')
    move_cursor(row, level + 1)
    vim.command(u'startinsert')

def create_supertopic(mode):
    topic_row, topic_level = topic_line()
    for row, level in all_preceding_lines(mode, topic_row):
        if level is not None and level < topic_level:
            level, bullet, number, line = split_line(row)
            break
    else:
        no_such_line()
        return
    row = row_of_created_empty(mode, row)
    if number is not None:
        number += 1
    build_line(row, level, u'.', None, u'')
    move_cursor(row, level)
    vim.command(u'startinsert')

def row_of_created_empty(mode, row):
    # Service for the three above functions only.
    last = None
    for last in all_text_lines(mode):
        pass
    if last is None:
        row, level = topic_line()
    else:
        row = last
    vim.current.buffer[row:row] = [u'']
    return row + 1

def delete_text(mode):
    act_on_region(mode, u'd', all_text_lines)

def delete_level(mode):
    act_on_region(mode, u'd', all_level_lines)

def rebullet_topic(mode):

    def rebullet():
        if level > 1 and bullet in u'*+-':
            return u'.:,;'[(level - 2) % 4]
        return bullet

    if u'n' in mode:
        row, level = topic_line()
        level, bullet, number, line = split_line(row)
        build_line(row, level, rebullet(), number, line)
    elif u'v' in mode:
        for row, level in all_level_lines(mode):
            if level is not None:
                level, bullet, number, line = split_line(row)
                build_line(row, level, rebullet(), number, line)

def number_siblings(mode):
    topic_row, topic_level = topic_line()
    ordinal = 0
    for row, level in all_level_lines(mode):
        if level == topic_level + 1:
            ordinal += 1
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, ordinal, line)

def revoke_numbering(mode):
    topic_row, topic_level = topic_line()
    ordinal = 0
    for row, level in all_level_lines(mode):
        if level == topic_level + 1:
            ordinal += 1
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, None, line)

# Levels and whitespace.

def adjust_margin(mode):
    before = None
    buffer = vim.current.buffer
    for row in all_text_lines(mode):
        line = buffer[row-1]
        margin = len(line) - len(line.lstrip())
        if before is None or margin < before:
            before = margin
    if before is not None:
        row, level = topic_line()
        if level == 0:
            after = 0
        else:
            after = level + 1
        delta = after - before
        if delta != 0:
            for row in all_text_lines(mode):
                level, bullet, number, line = split_line(row)
                build_line(row, level, bullet, number, line, delta)

def remove_margin(mode):
    before = None
    buffer = vim.current.buffer
    for row in all_text_lines(mode):
        line = buffer[row-1]
        margin = len(line) - len(line.lstrip())
        if before is None or margin < before:
            before = margin
    if before is not None and before > 0:
        delta = -before
        for row in all_text_lines(mode):
            level, bullet, number, line = split_line(row)
            build_line(row, level, bullet, number, line, delta)

def shift_in(mode):
    for row, level in all_level_lines(mode):
        level, bullet, number, line = split_line(row)
        build_line(row, level, bullet, number, line, 1)

def shift_out(mode):
    for row, level in all_level_lines(mode):
        level, bullet, number, line = split_line(row)
        build_line(row, level, bullet, number, line, -1)

def space_topic(mode):
    row, level = topic_line()
    if row == 1:
        no_such_line()
    else:
        vim.current.buffer[row-1:row-1] = [u'']
 
## Service functions.

# A Vim cursor has a 1-based ROW and a 0-based COL.  Beware than in its
# mode line, Vim displays both ROW and COL as 1-based.

# MODE is a sequence of flag letters.  Currently, there are one or two
# letters.  The first letter is `n' when commands executed in normal
# mode, `v' when in visual mode, or `i' when in insert mode.  The second
# letter may be `s' to skip over the contents of closed folds.

# By convention, a ROW of None implies the current row.  LEVEL is None
# for a non-topic text line, 1 for `*' topics, 2 for `..' topics, 3
# for `. :' topics, etc.  If first line of file is not a topic, an
# hypothetical 0-level topic is sometimes assumed.  When a necessary
# operation cannot be performed because a line does not exist, functions
# raise StopIteration.

def act_on_region(mode, command, generator):
    # Execute Vim COMMAND over the region defined by the first and last lines
    # produced by GENERATOR.
    start = None
    for row, level in generator(mode):
        if start is None:
            start = row
    if start is None:
        no_such_line()
    else:
        vim.command(u'normal %dG%s%dG' % (row, command, start))

def all_level_lines(mode, row=None):
    # In normal mode, generates all (ROW, LEVEL) for topics and non-empty
    # text lines within the whole level holding ROW, including it sub-levels.
    # LEVEL is zero for non-topic lines.  In visual mode, generates (ROW,
    # LEVEL) for all non-empty selected lines.
    if u'n' in mode:
        topic_row, topic_level = topic_line(row)
        yield topic_row, topic_level
        for row, level in all_following_lines(mode, topic_row):
            if level is not None and level <= topic_level:
                break
            yield row, level
    elif u'v' in mode:
        assert row is None, row
        for row, level in all_following_lines(mode):
            yield row, level

def all_text_lines(mode, row=None):
    # In normal mode, generates all rows for non-empty text lines after the
    # topic for the level holding ROW (None implies current row).  In visual
    # mode, generates all rows for non-empty non-topic lines.
    if u'n' in mode:
        row, level = topic_line(row)
        for row, level in all_following_lines(mode, row):
            if level is not None:
                break
            yield row
    elif u'v' in mode:
        assert row is None, row
        for row, level in all_following_lines(mode):
            if level is None:
                yield row

def topic_line(row=None):
    # Returns (ROW, LEVEL) for the closest topic line at or before ROW.
    row, level = row_and_level(row)
    if level is None:
        for row, level in all_preceding_lines(u'n', row):
            if level is not None:
                break
        else:
            assert False
    return row, level

def all_following_lines(mode, row=None):
    # In normal mode, generates (ROW, LEVEL) forward for all non-empty lines
    # after ROW.  In visual mode, generates (ROW, LEVEL) for all non-empty
    # selected lines from first to last.
    buffer = vim.current.buffer
    if u'n' in mode:
        if row is None:
            row, col = vim.current.window.cursor
        row = int(vim.eval(u'nextnonblank(%d)' % (row + 1)))
        last = len(buffer)
    elif u'v' in mode:
        assert row is None, row
        row, col = buffer.mark(u'<')
        if not buffer[row-1]:
            row = int(vim.eval(u'nextnonblank(%d)' % (row + 1)))
        last, col = buffer.mark(u'>')
    if u's' in mode:
        while 0 < row <= last:
            skip = int(vim.eval(u'foldclosedend(%d)' % row))
            if skip < 0:
                yield row_and_level(row)
            else:
                row = skip
            row = int(vim.eval(u'nextnonblank(%d)' % (row + 1)))
    else:
        while 0 < row <= last:
            yield row_and_level(row)
            row = int(vim.eval(u'nextnonblank(%d)' % (row + 1)))

def all_preceding_lines(mode, row=None):
    # In normal mode, generates (ROW, LEVEL) backwards for all non-empty lines
    # before ROW; a first line of the file is never considered empty for this
    # purpose, as it is then the root topic.  In visual mode, generates (ROW,
    # LEVEL) for all non-empty selected lines from last to first.
    buffer = vim.current.buffer
    if u'n' in mode:
        if row is None:
            row, col = vim.current.window.cursor
        row = int(vim.eval(u'prevnonblank(%d)' % (row - 1)))
        first = 1
    elif u'v' in mode:
        assert row is None, row
        row, col = buffer.mark(u'>')
        if not buffer[row-1]:
            row = int(vim.eval(u'prevnonblank(%d)' % (row - 1)))
        first, col = buffer.mark(u'<')
    if u's' in mode:
        while first <= row:
            skip = int(vim.eval(u'foldclosed(%d)' % row))
            if skip < 0:
                yield row_and_level(row)
            else:
                row = skip
            row = int(vim.eval(u'prevnonblank(%d)' % (row - 1)))
    else:
        while first <= row:
            yield row_and_level(row)
            row = int(vim.eval(u'prevnonblank(%d)' % (row - 1)))
    if u'n' in mode and len(buffer) > 0 and not buffer[0]:
        if not (u's' in mode and is_invisible(1)):
            yield 1, 0

def row_and_level(row=None):
    # Returns (ROW, LEVEL) for line at ROW.
    if row is None:
        row, col = vim.current.window.cursor
    line = vim.current.buffer[row-1]
    if line:
        if line[0] == u'*':
            return row, 1
        if line[0] == u'.':
            text = line[1:].lstrip()
            if text and text[0] in u'-*+@#.:,;':
                return row, len(line) - len(text) + 1
    if row == 1:
        return 1, 0
    return row, None

def command_at(row, command):
    # Temporarily move cursor on ROW and execute Vim COMMAND there.
    cursor = vim.current.window.cursor
    vim.current.window.cursor = row, 0
    vim.command(command)
    vim.current.window.cursor = cursor

def move_cursor(row, level):
    # Move cursor on topic at ROW, already known for being at LEVEL.
    vim.current.window.cursor = row, level + 1

def split_line(row=None):
    # Returns (LEVEL, BULLET, NUMBER, LINE) from the contents of line at ROW.
    # For a topic line, LEVEL is the topic level, BULLET is the bullet
    # character of the topic (None at root level), NUMBER is either None or
    # the value of the number following a `#' bullet, and LINE is the topic
    # contents with the whole topic prefix removed (None if empty).  For a
    # non-topic line, LEVEL, BULLET and NUMBER are None, LINE is the original
    # line contents.
    if row is None:
        row, col = vim.current.window.cursor
    line = vim.current.buffer[row-1]
    level = number = None
    if line:
        if line[0] == u'*':
            level = 1
            bullet = u'*'
            line = line[1:].lstrip()
        elif line[0] == u'.':
            text = line[1:].lstrip()
            if text:
                bullet = text[0]
                text = text[1:]
                if bullet == u'#':
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
                elif bullet in u'-*+@.:,;':
                    level = len(line) - len(text)
                    line = text.lstrip()
    if level is None:
        bullet = None
        if row == 1:
            level = 0
            if not line:
                line = None
    return level, bullet, number, line

def build_line(row=None, level=None, bullet=u'.', number=None, line=None,
               delta=0):
    # Reconstructs line at ROW from LEVEL, BULLET, NUMBER and LINE as obtained
    # from `split_line'.  While doing so, adjust level by adding DELTA to it.
    # DELTA may either be positive or negative.  Header lines may have their
    # bullet changed and/or repositioned.  Non-topic lines may have their
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
            buffer[row-1] = u' ' * delta + line
    elif level + delta <= 0:
        buffer[row-1] = line or u''
    else:
        if level + delta == 1:
            prefix = u'*'
        else:
            if bullet != u'@':
                if number is not None:
                    bullet = u'#' + str(number)
                elif level == 1 or bullet in u'.:,;#':
                    bullet = u'.:,;'[(level + delta - 2) % 4]
            prefix = u'.' + u' ' * (level + delta - 2) + bullet
        if line is None:
            buffer[row-1] = prefix
        else:
            buffer[row-1] = prefix + u' ' + line

def is_invisible(row=None):
    # Tells if the line at ROW is within a currently closed fold.
    if row is None:
        row, col = vim.current.window.cursor
    return int(vim.eval(u'foldclosed(%d)' % row)) >= 0

def no_such_line():
    # Reports "No such line" as a Vim warning.
    error(u"No such line.")

def error(message):
    # Reports MESSAGE as a Vim warning.
    vim.command(u'echohl WarningMsg | echo "%s" | echohl None'
                % message.rstrip().replace(u'"', u'\\"'))

install_with_vim()
vim.command(u'autocmd FileType allout python allout.install_with_vim()')
