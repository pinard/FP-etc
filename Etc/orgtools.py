#!/usr/bin/env python
# -*- coding: utf-8 -*-

__metaclass__ = type
import sys

def print_table(table, write=sys.stdout.write):
    """\
Print TABLE according to Org format conventions, using WRITE.
Table is a list of "lines", each line eith None for a separator line,
or a list of "values" to display from left to right.  Each value is
either None which is printed as blank, an actual value which may not
be a list, or a list of values to display vertically one under another.
"""

    # Plan the width of each column.
    widths = []
    for line in table:
        if line is not None:
            for counter, values in enumerate(line):
                while len(widths) <= counter:
                    widths.append(0)
                if isinstance(values, list):
                    for value in values:
                        widths[counter] = max(
                                widths[counter], len(str(value)))
                else:
                    widths[counter] = max(
                            widths[counter], len(str(values)))

    # Produce the table itself.
    for line in table:
        if line is None:
            write('|')
            for counter, width in enumerate(widths):
                write('-' * (width + 2))
                write(counter == len(widths) - 1 and '|' or '+')
            write('\n')
        else:
            more = True
            index = 0
            while more:
                more = False
                write('|')
                for values, width in zip(line, widths):
                    if values is None:
                        text = ''
                    elif isinstance(values, list):
                        if index < len(values):
                            text = str(values[index])
                            if index + 1 < len(values):
                                more = True
                        else:
                            text = ''
                    elif index == 0:
                        text = str(values)
                    else:
                        text = ''
                    write(' %*s |' % (-width, text))
                write('\n')
                index += 1
