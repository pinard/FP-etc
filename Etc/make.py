#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2000, 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2000.

"""\
Make-like facilities.

For years, I've been growing Makefiles for synchronising my projects
between machines, rebuilding Web sites, and doing various other things;
and resorted to parallel Make builds to save my time, as I do these things
on many remote machines at once.  The output of parallel processes often
got all mangled, to the point of becoming hard to decipher and sort out.
Also, I found limits on what one can cleanly do with Makefiles.  So, for
some while, I have not been satisfied, and decided to try rewriting nearly
all these tools in Python.  It went surprisingly well!  At the hearth,
I wrote this Make-alike module, fairly straightforward and simple to use.

So here, you will find equivalents for Make style rules, goals, dependencies
and actions.  I did not implement implicit rules nor macro capabilities,
as in my opinion, such needs are well supplemented by the power of Python.

    from Local import make
    maker = make.Maker([OPTION]...)

The Maker constructor accepts a few options, all defaulting to False
or 0 initially.  Option `logall' asks for all goal reports to be sent
to stdout, default is to send only goals in error.  Option `verbose'
asynchronously writes partial results on stderr as soon as possible,
yet lines never mangle each other, and titles are added as appropriate to
indicate to which goal lines pertain.  `agent' announces a maximal number
of parallel processes, 0 just means none.  `ignore' is set to ignore all
exit statuses from processes.  `dryrun' only shows commands that would be
executed, without actually executing them.

For each of your rules having different actions, merely subclass `make.Rule'
rules and override the `action' method in your subclass, like this:

    class MyRule(make.Rule):
        def action(self, *arguments):
            self.do(SYSTEM_COMMAND_1)
            self.do(SYSTEM_COMMAND_2)
            ...

Requirements and dependencies, as well as arguments for the action methods,
are specified while creating an instance of your rule, this also registers
the goal.  Moreover, if many rules happen to share the same actions,
merely instantiate your own rule class many times:

    MyRule(GOAL_NAME_1, maker, [REQUIRE_NAMES_1...], ACTION_ARGUMENTS_1...)
    MyRule(GOAL_NAME_2, maker, [REQUIRE_NAMES_2...], ACTION_ARGUMENTS_2...)
    ...

Goals and requires are all given as strings.  If many rules share the
same GOAL_NAME, their require lists get logically concatenated, as well
as their actions.  Actions one may use:

    self.do(SYSTEM_COMMAND)
    self.warn(DIAGNOSTIC)
    self.fail(DIAGNOSTIC)

Options `verbose', `ignore' and `dryrun' of the `make.Maker()' call may be
overriden for the duration of a `self.do' call, by giving them on that call.
`self.do' also accepts a `filter' argument, see the code for details.

Once rules are set, one launches execution for a given a set of goal strings:

   success = maker.run(GOAL_NAME_1, GOAL_NAME_2, ...)

For this function to succeed, all given goals should succeed.  A goal
succeeds if all its requires succeed, and if all attempted actions are
successfully run.  A require succeeds if it names a successful goal;
otherwise, it succeeds if it names an existing file or directory.

Success is stamped with a time.  Failed goals or requires have no stamp.
If a goal or a require names a file or a directory, its stamp is the
`mtime' of that file or directory.  Otherwise, a goal gets stamped with
the current time.

If a goal names an existing file or directory for which `mtime' is greater
or equal to the stamp of all requires of this rule, then the actions for
this rule are declared successful without being attempted.

Any failed require or failed `self.do' turns subsequent `self.do' for that
rule into no-operations, and inhibits other pending actions for this goal.
"""

# FIXME: Detect dependency cycles, which would cause thread deadlocks.

import os, stat, string, sys, time, threading

class Maker:

    def __init__(self, logall=False, verbose=False, agents=0,
                 ignore=False, dryrun=False):
        self.logall = logall
        self.verbose = verbose
        self.agents = agents
        self.ignore = ignore
        self.dryrun = dryrun
        self.rulesets = {}

    def run(self, *requires):
        # Topologically sort dependencies.
        top_name = self.top_name = 'Top Rule'
        top_rule = Rule(top_name, self, requires)
        goals = [top_name]
        stack = [top_name]
        arcs = []
        while stack:
            goal = stack[-1]
            del stack[-1]
            if goal in self.rulesets:
                for rule in self.rulesets[goal].rules:
                    for require in rule.requires:
                        if require in self.rulesets:
                            arcs.append((require, goal))
                            if require not in goals:
                                goals.append(require)
                                stack.append(require)
        from Local import graph
        sorted, cycles = graph.sort(goals, arcs)
        if cycles:
            sys.stderr.write("* ERROR: require cycle within these goals:\n"
                             "    %s.\n"
                             % string.join(cycles, ', '))
            return False
        # Launch all goals in natural order.
        from Local import multirun
        self.multi = multirun.Multi(self.agents)
        self.multi.display_activity(10)
        for goal in sorted:
            self.multi.do(self.rulesets[goal].run)
        self.multi.wrapup()
        # Collect results and cleanup.
        stamp = top_rule.ruleset.get_stamp()
        for ruleset in self.rulesets.itervalues():
            ruleset.rules = None        # break cycles
        self.rulesets = None            # break cycles
        return stamp is not None

class Rule:

    def __init__(self, name, maker, requires, *arguments):
        self.requires = requires or []
        self.arguments =arguments
        self.ruleset = maker.rulesets.get(name)
        if self.ruleset is None:
            self.ruleset = maker.rulesets[name] = RuleSet(name, maker)
        self.ruleset.rules.append(self)

    def action(self, *arguments):
        return True

    def do(self, command, logall=None, verbose=None,
           ignore=None, dryrun=None, filter=None):
        ruleset = self.ruleset
        if ruleset.stamp is None:
            return
        maker = ruleset.maker
        if logall is None:
            logall = maker.logall
        if verbose is None:
            verbose = maker.verbose
        if ignore is None:
            ignore = maker.ignore
        if dryrun is None:
            dryrun = maker.dryrun
        if filter is None:
            filter = self.filter
        self.warn(command)
        if dryrun:
            status = None
        else:
            split = string.split(command, None, 1)
            if len(split) == 1:
                file = os.popen(string.join([split[0], '2>&1']))
            else:
                program, arguments = split
                file = os.popen(string.join([program, '2>&1', arguments]))
            if not filter(file, maker.multi.write, verbose=verbose):
                self.fail("Filter failed: %s" % command)
            status = file.close()
        if status is not None:
            if ignore:
                self.warn("Exit %d (ignored): %s" % (status >> 8, command))
            else:
                self.fail("Exit %d: %s" % (status >> 8, command))

    def filter(self, file, write, verbose=False):
        line = file.readline()
        while line:
            write(line, verbose=verbose)
            line = file.readline()
        return True

    def warn(self, text):
        maker = self.ruleset.maker
        maker.multi.write('... %s\n' % text, verbose=maker.verbose)

    def fail(self, text):
        maker = self.ruleset.maker
        # We want errors on the terminal, even if not verbose.  However,
        # consider the error will show in the goal report, sent on stdout.
        maker.multi.write('*** %s\n' % text,
                           verbose=maker.verbose or not sys.stdout.isatty())
        self.ruleset.stamp = None

class RuleSet:

    def __init__(self, name, maker):
        self.name = name
        self.maker = maker
        self.rules = []
        self.stamp = -1                 # a very low number :-)
        self.completed = threading.Event()

    def get_stamp(self):
        self.completed.wait()
        return self.stamp

    def run(self):
        threading.currentThread().setName(self.name)
        rulesets = self.maker.rulesets
        for rule in self.rules:
            for name in rule.requires:
                if name in rulesets:
                    stamp = rulesets[name].get_stamp()
                else:
                    stamp = get_file_stamp(name)
                if stamp is None:
                    rule.fail("%s: Was not remade." % name)
                elif self.stamp is not None and stamp > self.stamp:
                    self.stamp = stamp
        if self.stamp is not None:
            name = self.name
            if name == self.maker.top_name:
                stamp = None
            else:
                stamp = get_file_stamp(name)
            if stamp is None:
                inhibit = False
            else:
                inhibit = stamp >= self.stamp
                self.stamp = stamp
            if not inhibit:
                for rule in self.rules:
                    rule.action(*rule.arguments)
                    if self.stamp is None:
                        break
                else:
                    if stamp is None:
                        stamp = int(time.time())
                        if stamp < self.stamp:
                            self.fail("Clock skew detected.")
                        else:
                            self.stamp = stamp
        self.completed.set()
        # self.maker.logall or self.stamp is None
        self.maker.multi.flush()

def get_file_stamp(name):
    try:
        stamp = os.stat(name)[stat.ST_MTIME]
    except OSError:
        stamp = None
    return stamp
