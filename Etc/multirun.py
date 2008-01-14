#!/usr/bin/env python
# -*- coding: Latin-1 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""
Handle simple case of multi-threaded function calls.

This module offers a very simple API for the common case of threaded
execution of relatively independent requests, using many agent processes
all reading from a single common input queue.  The overall usage scheme is:

    from Local import multirun
    multi = multirun.Multi(agents=AGENTS, size=SIZE)
    ...
    multi.do(FUNCTION, ARG1, ARG2, ...)
    ...
    multi.wrapup(wait=WAIT)

AGENTS is the maximum number of threads for serving requests (default
None means unlimited).  If AGENTS is 0, `multi.do' calls merely
get synchronous.  SIZE is the maximum size of the wait request
queue (default None or 0 mean unlimited).  That queue is filled by
calling `multi.do' many times.  If the queue already holds SIZE
requests, `multi.do' blocks until there is some room in the queue.  The
`multi.wrapup' function destroys all agents as soon as everything is
quiescent, it also waits before returning if WAIT is True (the default).

Any free agent takes a request from the queue and calls:

    FUNCTION(ARG1, ARG2, ...)

FUNCTION is typically I/O bound or network bound, or a sleeping function.
It may use a few other methods of `multi'.  To get `multi' defined with
FUNCTION requires a bit of care.  For example, `multi' could be made
global when created, of passed as an extra argument.  Each separate `Multi'
instance has its own single, all purpose reentrant lock.  Sections of code,
within various FUNCTIONs, which need sections of atomic execution, may use:

    multi.lock()
    ... CRITICAL CODE SECTION...
    multi.unlock()

`multi.set_name(NAME)' and `multi.get_name()' handle the tag (or name)
of the current thread.  This name, combined with the all purpose lock,
may be use to un-mangle the output coming from many threads, through:

    multi.write(TEXT, verbose=VERBOSE)
    multi.flush()
    multi.fragments(reset=RESET)

When VERBOSE is false, which is the default, `multi.write' accumulates TEXT
to be later output on standard output, all at once at `multi.flush' time.
If VERBOSE is true, `multi.write' _also_ writes TEXT now to standard error.
`multi.fragments' returns a list of TEXT fragments for this thread so far,
it resets that list to empty if RESET is true.  `multi.flush' also resets.

`multi.activity()' returns a tuple representing the current activity
of the current `Multi' instance: it is the number of currently busy agents,
then the number of requests waiting in the queue.
"""

import Queue, sys, threading

def debug(*messages):
    sys.stderr.write('%s %s\n' % (threading.currentThread().getName(),
                                  ' '.join(map(str, messages))))
def debug(*messages): pass

class Multi:
    def __init__(self, agents=None, size=None):
        self.synchronous = agents == 0
        if self.synchronous:
            self.name = 'Synchrone'
        else:
            # Dispatcher process, also holds the main request queue.
            self.dispatcher = Dispatcher(agents, size)
            # All purpose, single lock, for user convenience.
            self.rlock = threading.RLock()
        # For un-mangling all output.
        self.streams = {}
        self.written_name = None

    def do(self, function, *arguments):
        if self.synchronous:
            function(*arguments)
        else:
            debug('putting', arguments)
            self.dispatcher.queue.put((function, arguments))
            debug('put', arguments)

    def wrapup(self, wait=True):
        if not self.synchronous:
            self.dispatcher.queue.put(None)
            if wait:
                self.dispatcher.join()

    def lock(self):
        if not self.synchronous:
            debug('acquiring')
            self.rlock.acquire()
            debug('acquired')

    def unlock(self):
        if not self.synchronous:
            debug('releasing')
            self.rlock.release()
            debug('released')

    def set_name(self, name):
        if self.synchronous:
            self.name = name
        else:
            threading.currentThread().setName(name)

    def get_name(self):
        if self.synchronous:
            return self.name
        return threading.currentThread().getName()

    def write(self, text, verbose=False):
        name = self.get_name()
        fragments = self.streams.get(name)
        if fragments:
            fragments.append(text)
        else:
            self.streams[name] = [text]
        if verbose:
            self.lock()
            write = sys.stderr.write
            if name != self.written_name:
                label = '(%s)' % name
                spacer = ' ' * (79 - len(label))
                write('%s%s\n' % (spacer, label))
                self.written_name = name
            write(text)
            self.unlock()

    def flush(self):
        name = self.get_name()
        fragments = self.fragments(True)
        if fragments:
            self.lock()
            file = sys.stdout
            label = '[%s]' % name
            spacer = ' ' * (79 - len(label))
            file.write('=' * 79 + '\n')
            file.write('%s%s\n' % (spacer, label))
            file.writelines(fragments)
            self.written_name = None
            self.unlock()

    def fragments(self, reset=False):
        name = self.get_name()
        if reset:
            self.lock()
            fragments = self.streams.get(name)
            if fragments:
                del self.streams[name]
            self.unlock()
        else:
            fragments = self.streams.get(name)
        return fragments

    def activity(self):
        return self.dispatcher.activity()

    def display_activity(self, interval):
        if not self.synchronous:
            self.dispatcher.interval = interval
            self.dispatcher.write_lock = self.rlock

# As an attempt to clarify synchronisation, besides the original thread
# and all agent threads, there is also a dispatcher thread.  This thread
# receives requests from both the original thread and all agents on a
# single request queue.  When free, an agent registers itself as on this
# queue.  A `multi.do' registers (FUNCTION, ARGUMENTS) on this queue.

class Dispatcher(threading.Thread):
    def __init__(self, agents, size):
        threading.Thread.__init__(self)
        self.setName('Dispatcher')
        # Job related variables.
        self.queue = Queue.Queue(size or 0)
        self.waiting_jobs = []
        # Agent related variables.
        self.agents = agents
        self.born_agents = 0
        self.waiting_agents = []
        # Activity display variables.
        self.interval = None
        self.write_lock = None
        self.last_time = None
        # Launch dispatcher.
        self.start()

    def run(self):
        wrapup = False
        while (not (wrapup and len(self.waiting_agents) == self.born_agents)
               or self.waiting_jobs):
            request = self.queue.get()
            debug(request)
            if request is None:
                # Should exit as soon as everything quiescent.
                wrapup = True
            elif isinstance(request, tuple):
                # Job waiting for an agent.
                self.waiting_jobs.append(request)
                if (not self.waiting_agents
                    and (self.agents is None
                         or self.born_agents < self.agents)):
                    self.born_agents += 1
                    Agent('Agent-%d' % self.born_agents, self)
            else:
                # Agent waiting for a job.
                self.waiting_agents.append(request)
            # Match an agent with a job if possible.
            if self.waiting_agents and self.waiting_jobs:
                agent = self.waiting_agents.pop()
                agent.request = self.waiting_jobs.pop(0)
                agent.event.set()
            # Wait for something more to do.
            if self.interval is not None:
                self.maybe_display_activity()
        # Wrapup all agents.
        del self.write_lock
        for agent in self.waiting_agents:
            agent.request = None
            agent.event.set()
            agent.join()
        del self.waiting_agents

    def maybe_display_activity(self):
        import time
        now = time.time()
        if self.last_time is None or now >= self.last_time + self.interval:
            self.last_time = now
            text = ". Multi : "
            busy, size = self.activity()
            if busy == 0:
                text += "all idle"
            else:
                text += "%d busy" % busy
            if size != 0:
                text += ", %d queued" % size
            if self.write_lock is None:
                sys.stderr.write("%s.\n" % text)
            else:
                self.write_lock.acquire()
                sys.stderr.write("%s.\n" % text)
                self.write_lock.release()

    def activity(self):
        return (self.born_agents - len(self.waiting_agents),
                self.queue.qsize() + len(self.waiting_jobs))

class Agent(threading.Thread):
    def __init__(self, name, dispatcher):
        threading.Thread.__init__(self)
        self.setName(name)
        self.dispatcher = dispatcher
        # EVENT is set by the dispatcher once SELF.REQUEST got a value.
        self.event = threading.Event()
        self.start()

    def run(self):
        while True:
            self.dispatcher.queue.put(self)
            self.event.wait()
            if self.request is None:
                break
            function, arguments = self.request
            function(*arguments)
            self.event.clear()
        del self.dispatcher

def test():

    def write(counter):
        import time, random
        time.sleep(random.random())
        multi.lock()
        sys.stdout.write('%.2d\n' % counter)
        multi.unlock()

    multi = Multi(3, 4)
    multi.display_activity(1)
    for counter in range(20):
        multi.do(write, counter)
    multi.wrapup()

if __name__ == '__main__':
    test()
