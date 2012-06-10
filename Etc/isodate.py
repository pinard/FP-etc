#!/usr/bin/env python3
# Copyright © 1996-2000, 2003, 2004 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 1996-06.

"""\
Convert dates from some American formats to ISO format.
"""

import re


class Rule:

    which_month = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    which_zone = {
        'PST': '-08:00', 'PDT': '-07:00', 'MST': '-07:00', 'MDT': '-06:00',
        'CST': '-06:00', 'CDT': '-05:00', 'EST': '-05:00', 'EDT': '-04:00',
        'AST': '-04:00', 'NST': '-03:30', 'UT':  '+00:00', 'GMT': '+00:00',
        'BST': '+01:00', 'MET': '+01:00', 'EET': '+02:00', 'JST': '+09:00',
        'GMT+1': '+01:00', 'GMT+2': '+02:00', 'GMT+3': '+03:00',
        'GMT+4': '+04:00', 'GMT+5': '+05:00', 'GMT+6': '+06:00',
        'GMT+7': '+07:00', 'GMT+8': '+08:00', 'GMT+9': '+09:00',
        'GMT+10': '+10:00', 'GMT+11': '+11:00', 'GMT+12': '+12:00',
        'GMT+13': '+13:00',
        'GMT-1': '-01:00', 'GMT-2': '-02:00', 'GMT-3': '-03:00',
        'GMT-4': '-04:00', 'GMT-5': '-05:00', 'GMT-6': '-06:00',
        'GMT-7': '-07:00', 'GMT-8': '-08:00', 'GMT-9': '-09:00',
        'GMT-10': '-10:00', 'GMT-11': '-11:00', 'GMT-12': '-12:00'}

    week_day = 'Sun|Mon|Tue|Wed|Thu|Fri|Sat'
    month_day = '[ 0-3][0-9]'
    month = '|'.join(which_month)
    year = '[890][0-9]|19[789][0-9]|20[0-9][0-9]'
    day_time = '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]|[0-2][0-9]:[0-5][0-9]'

    def which_year(self, text):
        year = int(text)
        if year >= 1900:
            return year
        if year >= 70:
            return 1900 + year
        return 2000 + year


# Frequent cases.

class Rule_Slashed(Rule):
    def __init__(self):
        self.search = re.compile(
            '([01]?[0-9])\/([0-3]?[0-9])\/([890][0-9])').search

    def replace(self, match):
        return '%d-%02d-%02d' % (self.which_year(match.group(3)),
                                 int(match.group(1)),
                                 int(match.group(2)))


class Rule_Email(Rule):
    def __init__(self):
        self.search = (re.compile(
                '((%s), )?(%s) (%s) (%s)'
                % (self.week_day, self.month_day, self.month, self.year))
            .search)

    def replace(self, match):
        return '%d-%02d-%02d' % (self.which_year(match.group(5)),
                                 self.which_month[match.group(4)],
                                 int(match.group(3)))


class Rule_Other_1(Rule):
    def __init__(self):
        self.search = (re.compile(
                '(%s) (%s) (%s) (%s)'
                % (self.month, self.month_day, self.day_time, self.year))
            .search)

    def replace(self, match):
        return '%d-%02d-%02d %s' % (self.which_year(match.group(4)),
                                    self.which_month[match.group(1)],
                                    int(match.group(2)),
                                    match.group(3))


class Rule_Other_2(Rule):
    def __init__(self):
        self.search = (re.compile(
                '(%s) (%s) (%s)'
                % (self.month, self.month_day, self.day_time))
            .search)

    def replace(self, match):
        return '%02d-%02d %s' % (self.which_month[match.group(1)],
                                 int(match.group(2)),
                                 match.group(3))


class Rule_Zone_1(Rule):
    def __init__(self):
        self.search = re.compile(
            '(%s) (UT|GMT[-+][0-9][0-9]?|[A-Z][A-Z]T)' % self.day_time).search

    def replace(self, match):
        return '%s %s' % (match.group(1), self.which_zone(match.group(2)))


class Rule_Zone_2(Rule):
    def __init__(self):
        self.search = re.compile(
            '(%s) ([+-][01][0-9])([03]0)' % self.day_time).search

    def replace(self, match):
        return '%s %s:%s' % match.group(1, 2, 3)


# POSIX horrors, as in `ls' and `pax'.  Just drop the time.

class Rule_Posix_1(Rule):
    def __init__(self):
        import time
        self.current_year = time.localtime(time.time())[0]
        self.search = (re.compile(
                '(%s) (%s) (%s)'
                % (self.month, self.month_day, self.day_time))
            .search)

    def replace(self, match):
        return '%d-%02d-%02d ' % (self.current_year,
                                  self.which_month[match.group(1)],
                                  int(match.group(2)))


class Rule_Posix_2(Rule):
    def __init__(self):
        self.search = (re.compile(
                '(%s) (%s)  (%s)'
                % (self.month, self.month_day, self.year))
            .search)

    def replace(self, mahch):
        return '%d-%02d-%02d ' % (int(match.group(3)),
                                  self.which_month[match.group(1)],
                                  int(match.group(2)))


# Do it all.

class Application:

    def transform(self, text):
        for rule in self.rules:
            fragments = []
            match = rule.search(text)
            while match:
                fragments.append(text[:match.start()])
                fragments.append(rule.replace(match))
                text = text[match.end():]
                match = rule.search(text)
            fragments.append(text)
            text = ''.join(fragments)
        return text


class Normalize(Application):
    def __init__(self):
        self.rules = (Rule_Slashed(), Rule_Email(),
                      Rule_Other_1(), Rule_Other_2(),
                      Rule_Zone_1(), Rule_Zone_2())


class Unposix(Application):
    def __init__(self):
        self.rules = Rule_Posix_1(), Rule_Posix_2()


# External API.
normalize = Normalize().transform
unposix = Unposix().transform
