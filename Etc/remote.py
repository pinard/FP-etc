#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2001, 2002, 2003 Progiciels Bourbeau-Pinard inc.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Python services on a remote machine.

To each Server instance is associated a network link towards a remote
server program.  The remote server is able to evaluate Python expressions,
apply functions or execute Python statements on demand.  Typically,
the link is kept opened to service many requests which depend on the
remote machine, either for its computing power, its file system, or other
idiosyncrasies, and closed once the overall task is completed.

A server is created through `remote.Server(PATH, TRACE)'.  A path is a
sequence of machines that should all collaborate for the information
to flow from one end to another.  It may happen that a set of machines
is not fully connected, or at least, that SSH authentication does not
work unless following a precise sequence of connections.  Yet, in most
practical cases I use, a path does not imply intermediate machines.
The server is automatically uploaded as needed on various remote hosts
along PATH.  Servers are saved as `~USER/.python-remote-VERSION', where
VERSION identifies the protocol.  That file is reused if it already exists
on some host, given it starts the protocol correctly.  If PATH is missing
or None, the current host is directly used, without installing nor using
a remote server.  Otherwise, it is a string holding a colon-separated
list of zero or more `USER@HOST'.  All but the rightmost `USER@HOST' are
proxys, the rightmost is the final destination.  `USER@' may be omitted,
in which case the user of the previous host in the chain is implied.

If the first HOST is listed in `~/.ssh/config' or `~/.ssh/known_hosts',
this tool uses SSH to establish the link, presuming the exchange of
keys has been prepared and no explicit password is needed.  Otherwise,
`~/.netrc' should list HOST with a login and password, this tool then
uses a mix of Telnet and FTP, and avoids using tty flow control.

A trace is a debugging tool by which one may see the communication
protocol in action, in the need of identifying what a problem may be.
When TRACE is not given or has a zero value, the protocol is not traced.
Otherwise, a value of 1 traces the client side of the protocol on local
stderr, a value of 2 does as 1 and produces a server side debugging file
on HOST, a value of 3 does as 1 and 2 and sends a Telnet communication
on local stderr.

An evaluation context is held within the remote server for the current
connection.  The `pickle' module is used for all transit to or from the
server, so the programmer should restrain him/herself to Python values that
can be pickled. `server.call(FUNCTION, [ARGUMENT]...)' calls FUNCTION over
zero or more ARGUMENT in the remote server and return the results of that
call, FUNCTION is given as a string holding a Python expression, and each
ARGUMENT should be picklable.  `server.apply(FUNCTION, ARGUMENTS)' does the
same, except that ARGUMENTS are bundled into a single sequence instead of
given separately. `server.eval(EXPRESSION)' evaluates EXPRESSION, and
`server.execute(STATEMENT)' runs the given STATEMENT, within the remote
server.  EXPRESSION and STATEMENT are strings holding Python source code.

The `server.close()' method should be used to shut down the connection.

Here is a simplistic example.  Suppose `cliff' is an Internet host for
which we already have immediate SSH access through the proper key setup.
To get `cliff' to compute `2 + 3', a Python expression, one uses this:

    # The "from Etc" only if "fp-etc" has been installed, adapt as needed.
    from Etc import remote
    server = remote.Server('cliff')
    print server.eval('2 + 3')
    server.close()
"""

import base64, threading, zlib
import pickle as pickle
from io import StringIO

# Debugging.
DEBUG = True

# Protocol version and special file names.
PROTOCOL_VERSION = 4
PROTOCOL_HEADER = ("Python `remote' server, protocol version %d"
                   % PROTOCOL_VERSION)
SCRIPT_FILE_NAME = '.python-remote-%d' % PROTOCOL_VERSION
TRACE_FILE_NAME = '.python-remote-%d-trace' % PROTOCOL_VERSION
INDIRECT_FILE_NAME = '.python-remote-%d-indirect' % PROTOCOL_VERSION

# Delay between sent lines to avoid overrun with Telnet.
TELNET_LINE_DELAY = 0.05

# Size of compressed pickle over which we prefer FTP to Telnet.
TELNET_FTP_THRESHOLD = 600

# Should we use some `stty' options over Telnet sessions?
TELNET_STTY_NO_ECHO = True
TELNET_STTY_NL = False
TELNET_STTY_NO_OPOST = False

# Named constants.
INDIRECT_CODE, APPLY_CODE, EVAL_CODE, EXECUTE_CODE = list(range(4))
INDIRECT_RETURN, NORMAL_RETURN, ERROR_RETURN = list(range(3))

import os, sys

if DEBUG:
    def debug(message):
        if not message.endswith('\n'):
            message += '\n'
        sys.stderr.write(message)
else:
    def debug(message):
        pass

### Client side.

class error(Exception): pass
class CreationError(error): pass
class ServerError(error): pass
class UploadError(error): pass

def Server(path=None, trace=0):
    """\
Decide which kind of server is needed for PATH, then create and return it.
"""
    for maker in make_local_server, make_ssh_server, make_telnet_server:
        server = maker(path, trace)
        if server:
            return server
    #write = sys.stderr.write
    #write("* Ne sait pas comment rejoindre `%s'!\n" % path)
    #method = None
    #while method not in ('ssh', 'telnet'):
    #    write("\nChoisir une méthode d'accès (ssh, telnet)? [ssh] ")
    #    method = sys.stdin.readline().strip().lower()
    #    if not method:
    #        method = 'ssh'
    #maker = {'ssh': make_ssh_server, 'telnet': make_telnet_server}[method]
    #server = maker(path, trace, insist=True)
    #if server is not None:
    #    return server
    raise CreationError("* Ne peut créer un serveur pour `%s'." % path)

Serveur = Server

def make_local_server(path, trace, insist=False):
    if path is None:
        return Local_Server(trace)

class Local_Server:

    def __init__(self, trace):
        self.trace_client = trace >= 1
        self.host = 'Local'
        self.context = {}
        if self.trace_client:
            sys.stderr.write('%s: %s - Started\n'
                             % (self.host, PROTOCOL_HEADER))

    def close(self):
        if self.trace_client:
            sys.stderr.write('%s: %s - Complete\n'
                             % (self.host, PROTOCOL_HEADER))

    quitter = close

    def call(self, text, *arguments):
        """\
Evaluate TEXT, which should yield a function on the remote server.
Then apply this function over ARGUMENTS, and return the function value.
"""
        return self.apply(text, arguments)

    appeler = call

    def apply(self, text, arguments):
        """\
Evaluate TEXT, which should yield a function on the remote server.
Then apply this function over ARGUMENTS, and return the function value.
"""
        if self.trace_client:
            request = None, APPLY_CODE, (text, arguments)
            sys.stderr.write('%s: < %s\n' % (self.host, short_repr(request)))
        value = eval(text, globals(), self.context)(*arguments)
        if self.trace_client:
            reply = None, NORMAL_RETURN, value
            sys.stderr.write('%s: > %s\n' % (self.host, short_repr(reply)))
        return value

    appliquer = apply

    def eval(self, text):
        """\
Get the remote server to evaluate TEXT as an expression, and return its value.
"""
        if self.trace_client:
            request = None, EVAL_CODE, text
            sys.stderr.write('%s: < %s\n' % (self.host, short_repr(request)))
        value = eval(text, globals(), self.context)
        if self.trace_client:
            reply = None, NORMAL_RETURN, value
            sys.stderr.write('%s: > %s\n' % (self.host, short_repr(reply)))
        return value

    evaluer = eval

    def execute(self, text):
        """\
Execute TEXT as Python statements on the remote server.  Return None.
"""
        if self.trace_client:
            request = None, EXECUTE_CODE, text
            sys.stderr.write('%s: < %s\n' % (self.host, short_repr(request)))
        exec(text, globals(), self.context)
        if self.trace_client:
            reply = None, NORMAL_RETURN, None
            sys.stderr.write('%s: > %s\n' % (self.host, short_repr(reply)))

    executer = execute

class Remote_Server:

    def __init__(self, path, trace):
        self.user, self.host, self.remainder = split_path(path)
        self.trace_client = trace >= 1
        self.trace_server = trace >= 2
        self.cleanup_indirect = False
        self.open_connection()
        text = self.receive_start_text()
        if text != '%s\n' % PROTOCOL_HEADER:
            if text is None:
                sys.stderr.write("Oops!  Pushing %s, on `%s'...\n"
                                 % (PROTOCOL_HEADER, self.host))
            name = __file__
            if name.endswith('.pyc'):
                name = name[:-4] + '.py'
            self.upload_file(name, SCRIPT_FILE_NAME)
            text = self.receive_start_text()
            if text != '%s\n' % PROTOCOL_HEADER:
                raise UploadError("Unable to install `%s' on `%s'." % (
                    name, self.host))
        if self.trace_client:
            sys.stderr.write('%s: %s - Started\n'
                             % (self.host, PROTOCOL_HEADER))
        self.threads = {}

    def close(self):
        self.send_text('')
        text = self.receive_text()
        assert text == '', text
        if self.trace_client:
            sys.stderr.write('%s: %s - Complete\n'
                             % (self.host, PROTOCOL_HEADER))
        self.close_connection()

    quitter = close

    def call(self, text, *arguments):
        return self.apply(text, arguments)

    appeler = call

    def apply(self, text, arguments):
        return self.round_trip(APPLY_CODE, (text, arguments))

    appliquer = apply

    def eval(self, text):
        return self.round_trip(EVAL_CODE, text)

    evaluer = eval

    def execute(self, text):
        return self.round_trip(EXECUTE_CODE, text)

    executer = execute

    def round_trip(self, code, value):
        current = threading.currentThread()
        if current not in self.threads:
            self.threads[current] = len(self.threads)
        thread = self.threads[current]
        request = thread, code, value
        if self.trace_client:
            sys.stderr.write('%s: < %s\n' % (self.host, short_repr(request)))
        text = zlib.compress(pickle.dumps(request, True))
        if self.indirect_option and len(text) > TELNET_FTP_THRESHOLD:
            self.upload(text, '%s-%d' % (INDIRECT_FILE_NAME, thread))
            self.cleanup_indirect = True
            request = thread, INDIRECT_CODE
            if self.trace_client:
                sys.stderr.write('%s: < %s\n'
                                 % (self.host, short_repr(request)))
            text = zlib.compress(pickle.dumps(request, True))
        self.send_text(base64.encodestring(text))
        text = self.receive_text()
        if text is None:
            return None
        reply = pickle.loads(zlib.decompress(base64.decodestring(text)))
        if len(reply) == 2:
            thread2, code = reply
            assert thread == thread2, (thread, thread2)
            assert code == INDIRECT_RETURN, code
            self.cleanup_indirect = True
            if self.trace_client:
                sys.stderr.write('%s: > %s\n' % (self.host, short_repr(reply)))
            text = self.download('%s-%d' % (INDIRECT_FILE_NAME, thread))
            thread, code, value = pickle.loads(zlib.decompress(text))
        else:
            thread2, code, value = reply
            assert thread == thread2, (thread, thread2)
        if self.trace_client:
            sys.stderr.write('%s: > %s\n' % (self.host, short_repr(reply)))
        if code == ERROR_RETURN:
            raise ServerError(value)
        return value

def make_ssh_server(path, trace, insist=False):
    user, host, remainder = split_path(path)
    try:
        input = file(os.path.expanduser('~/.ssh/config'))
    except IOError:
        pass
    else:
        for line in input:
            fields = line.split(None, 2)
            if len(fields) >= 2 and fields[0] == 'Host' and fields[1] == host:
                return SSH_Server(path, trace)
    try:
        input = file(os.path.expanduser('~/.ssh/known_hosts'))
    except IOError:
        pass
    else:
        for line in input:
            first, rest = line.split(None, 1)
            for maybe in first.split(','):
                if maybe == host:
                    return SSH_Server(path, trace)
    if insist:
        pass                            # Ne sait pas comment insister

class SSH_Server(Remote_Server):

    def __init__(self, path, trace):
        self.indirect_option = False
        Remote_Server.__init__(self, path, trace)

    def open_connection(self):
        pass

    def close_connection(self):
        pass

    def download(self, remote):
        import tempfile
        temporary = tempfile.mktemp()
        os.system('scp -pq %s:%s %s' % (self.host, remote, temporary))
        text = file(temporary).read()
        os.remove(temporary)

    def upload(self, text, remote):
        import tempfile
        temporary = tempfile.mktemp()
        file(temporary, 'w').write(text)
        os.system('scp -pq %s %s:%s' % (temporary, self.host, remote))
        os.remove(temporary)

    def upload_file(self, name, remote):
        os.system('scp -pq %s %s:%s' % (name, self.host, remote))

    def receive_start_text(self):
        import popen2
        command = ['ssh', '-x']
        if self.user:
            command += ['-l', self.user]
        command += [self.host, 'python', SCRIPT_FILE_NAME]
        if self.trace_server:
            command.append('-t')
        if self.remainder:
            command.append(self.remainder)
        #sys.stderr.write('** command %s\n' % command)
        self.child = popen2.Popen3(' '.join(command))
        return self.receive_text()

    def receive_text(self):
        assert self.child.poll() == -1, (
            "%s: Python server has been interrupted." % self.host)
        lines = []
        while True:
            line = self.child.fromchild.readline()
            if not line:
                return None
            if line == '\n':
                return ''.join(lines)
            lines.append(line)

    def send_text(self, text):
        assert self.child.poll() == -1, (
            "%s: Python server has been interrupted." % self.host)
        self.child.tochild.write(text + '\n')
        self.child.tochild.flush()

def make_telnet_server(path, trace, insist=False):
    user, host, remainder = split_path(path)
    import netrc
    try:
        triple = netrc.netrc().authenticators(host)
    except IOError:
        triple = None
    if triple is not None:
        login, account, password = triple
    elif insist:
        login = account = password = None
        while not login:
            sys.stderr.write("Login: ")
            login = sys.stdin.readline().strip().lower()
        import getpass
        password = getpass.getpass("Password: ")
    else:
        return None
    return Telnet_Server(host, trace, login, password)

class Telnet_Server(Remote_Server):

    def __init__(self, host, trace, login, password):
        self.trace_telnet = trace >= 3
        self.login = login
        self.password = password
        self.indirect_option = True
        Remote_Server.__init__(self, host, trace)

    def open_connection(self):
        self.open_connection_chat()
        fragments = []
        write = fragments.append
        write('PS1=\r')
        if TELNET_STTY_NO_ECHO:
            write('stty -echo\r')
        write('echo\r'
              'echo Ready\r')
        self.perform_chat((None, ''.join(fragments)))
        #self.telnet.interact()
        self.perform_chat((None, ''.join(fragments)),
                          ('\nReady', None))
        self.ftp = None

    def open_connection_chat(self):
        import telnetlib
        self.telnet = telnetlib.Telnet(self.host)
        self.perform_chat(('ogin:', self.login + '\r'),
                          ('word:', self.password + '\r'))

    def perform_chat(self, *expect_sends):
        import time
        for expect, send in expect_sends:
            if self.trace_telnet:
                debug('*expect: %r' % expect)
            if expect:
                text = self.telnet.read_until(expect, 30)
                if self.trace_telnet:
                    debug('*got: %r' % text)
                assert text, "Expecting `%s' for 30 seconds." % expect
            if self.trace_telnet:
                debug('*send: %r' % send)
            if send:
                time.sleep(TELNET_LINE_DELAY)
                self.telnet.write(send)

    def check_ftp(self):
        if self.ftp is None:
            import ftplib
            self.ftp = ftplib.FTP(self.host, self.login, self.password)

    def close_connection(self):
        self.telnet.close()
        if self.ftp is not None:
            self.ftp.quit()

    def download(self, remote):
        self.check_ftp()
        self.blocks = []
        self.ftp.retrbinary('RETR %s' % remote, self.save_block)
        text = ''.join(self.blocks)
        del self.blocks
        return text

    def save_block(self, block):
        self.blocks.append(block)

    def upload(self, text, remote):
        self.check_ftp()
        self.ftp.storbinary('STOR %s' % remote, StringIO(text), 8192)

    def upload_file(self, name, remote):
        self.check_ftp()
        self.ftp.storbinary('STOR %s' % remote, file(name), 8192)

    def receive_start_text(self):
        command = ['python', SCRIPT_FILE_NAME, '-i']
        if self.trace_server:
            command.append('-t')
        if self.remainder:
            command.append(self.remainder)
        self.telnet.write(' '.join(command))
        previous_line = None
        while True:
            line = self.telnet.read_until('\n', 8)
            if line.endswith('\r\n'):
                line = line[:-2] + '\n'
            if not line:
                return None
            if line == '\n':
                if previous_line is not None:
                    return previous_line
            else:
                previous_line = line

    def receive_text(self):
        # Stdout and stderr are all inter-mixed.  The normal protocol, once
        # started, never contains any space, while stderr often do.  An empty
        # line may pertain to any.
        lines = []
        presuming_stderr = False
        timeout = 60
        line = self.telnet.read_until('\n', timeout)
        if self.trace_telnet:
            debug('*got: %r' % line)
        while line:
            if line.endswith('\r\n'):
                line = line[:-2] + '\n'
            if line == '\n':
                if not presuming_stderr:
                    return ''.join(lines)
            elif len(line) % 4 == 1 and ' ' not in line:
                presuming_stderr = False
                timeout = 60
                lines.append(line)
            else:
                presuming_stderr = True
                timeout = 3
                sys.stderr.write(line)
            line = self.telnet.read_until('\n', timeout)
            if self.trace_telnet:
                debug('*got: %r' % line)

    def send_text(self, text):
        import time
        lines = text.split('\n')
        for line in lines:
            time.sleep(TELNET_LINE_DELAY)
            self.telnet.write(line + '\r')
            if self.trace_telnet:
                debug('*sent: %r' % (line + '\r'))
            if not TELNET_STTY_NO_ECHO:
                text = self.telnet.read_until('\n')
                if self.trace_telnet:
                    debug('*echo: %r' % text)
                if text.endswith('\r\n'):
                    text = text[:-2]
                elif text.endswith('\n'):
                    text = text[:-1]
                assert line == text, (line, text)

def split_path(path):
    """\
Return (USER, HOST, REMAINDER) where `USER@HOST' is the first PATH
component and REMAINDER is all PATH components but the first.  USER is
returned as None if not specified in first PATH component.
"""
    if ':' in path:
        host, remainder = path.split(':', 1)
    else:
        host, remainder = path, None
    if '@' in host:
        user, host = host.split('@', 1)
    else:
        user = None
    return user, host, remainder

### Server side.

class Main:
    def __init__(self):
        self.indirect_option = False
        self.trace_option = False

    def main(self, *arguments):
        """\
Python remote server.

Usage: ~USER/.python-remote-VERSION [OPTION]... [PATH]

Options:
   -i  Allow indirect replies when those replies are big.
   -t  Produce a debugging trace file, where the server runs.

If PATH is not given, this server serves current host.  Otherwise,
this server acts as a proxy for reaching that PATH.

An indirect reply is stored into a file, which the client shall download.
"""
        import getopt
        options, arguments = getopt.getopt(arguments, 'it')
        for option, value in options:
            if option == '-i':
                self.indirect_option = True
            elif option == '-t':
                self.trace_option = True
            pass
        if len(arguments) == 0:
            self.dispatcher(None)
        elif len(arguments) == 1:
            self.dispatcher(arguments[0])
        else:
            assert False, arguments

    def dispatcher(self, path):
        """\
Python remote server proper.

Here is a description of the communication protocol.  The server identifies
itself on a single stdout line, followed by an empty line.  It then enters a
loop reading one request on stdin terminated by an empty line, and writing
the reply on stdout, followed by an empty line.  Requests and replies are
compressed pickles which are Base64-coded over possibly multiple lines.
All requests are processed within a same single context for local variables.
An empty request produces an empty reply and the termination of this server.
"""
        # Choisir le serveur à utiliser.
        if path is None:
            self.server = None
        elif self.trace_option:
            self.server = Server(path, trace=2)
        else:
            self.server = Server(path)
        # Démarrage du protocole.
        self.write_lock = threading.Lock()
        if self.trace_option:
            self.trace_lock = threading.Lock()
            self.trace_file = open(TRACE_FILE_NAME, 'w')
        text = '%s\n\n' % PROTOCOL_HEADER
        self.write(text, None)
        self.context = {}
        # Boucle de distribution des requêtes.
        agents = []
        lines = []
        while True:
            line = sys.stdin.readline()
            self.trace(None, '<', line)
            if not line:
                break
            if line != '\n':
                lines.append(line)
                continue
            text = ''.join(lines)
            if text == '':
                break
            lines = []
            request = pickle.loads(zlib.decompress(base64.decodestring(text)))
            thread = request[0]
            while thread >= len(agents):
                agents.append(Server_Agent(self))
            agent = agents[thread]
            agent.request = request
            agent.event.set()
        # Nettoyage final.
        for agent in agents:
            agent.request = None
            agent.event.set()
            agent.join()
        self.write('\n', None)
        if self.trace_option:
            self.trace_file.close()

    def write(self, text, thread):
        self.trace(thread, '>', text)
        self.write_lock.acquire()
        sys.stdout.write(text)
        sys.stdout.flush()
        self.write_lock.release()

    def trace(self, thread, tag, value):
        if self.trace_option:
            self.trace_lock.acquire()
            self.trace_file.write('(%s) %s %r\n' % (thread, tag, value))
            self.trace_file.flush()
            self.trace_lock.release()

main = Main().main

class Server_Agent(threading.Thread):

    def __init__(self, dispatcher):
        threading.Thread.__init__(self)
        self.dispatcher = dispatcher
        self.event = threading.Event()
        self.previous_indirect_file_name = None
        self.start()

    def run(self):
        server = self.dispatcher.server
        context = self.dispatcher.context
        while True:
            self.event.wait()
            if self.request is None:
                break
            if len(self.request) == 2:
                thread, code = self.request
                assert code == INDIRECT_CODE, code
                self.dispatcher.trace(thread, '<-', self.request)
                text = file(self.indirect_file_name(thread)).read()
                thread, code, text = pickle.loads(zlib.decompress(text))
            else:
                thread, code, text = self.request
            self.dispatcher.trace(thread, '<-', self.request)
            try:
                if server is None:
                    if code == APPLY_CODE:
                        text, arguments = text
                        reply = (thread, NORMAL_RETURN,
                                 eval(text, globals(), context)(*arguments))
                    elif code == EVAL_CODE:
                        reply = (thread, NORMAL_RETURN,
                                 eval(text, globals(), context))
                    else:
                        exec(text, globals(), context)
                        reply = thread, NORMAL_RETURN, None
                else:
                    if code == APPLY_CODE:
                        text, arguments = text
                        reply = (thread, NORMAL_RETURN,
                                 server.apply(text, arguments))
                    elif code == EVAL_CODE:
                        reply = (thread, NORMAL_RETURN,
                                 server.eval(text))
                    else:
                        server.execute(text)
                        reply = thread, NORMAL_RETURN, None
            except:
                import traceback
                message = StringIO()
                traceback.print_exc(file=message)
                reply = thread, ERROR_RETURN, message.getvalue()
            self.dispatcher.trace(thread, '->', reply)
            text = zlib.compress(pickle.dumps(reply, True))
            if (self.dispatcher.indirect_option
                    and len(text) > TELNET_FTP_THRESHOLD):
                file(self.indirect_file_name(thread), 'w').write(text)
                reply = thread, INDIRECT_RETURN
                self.dispatcher.trace(thread, '->', reply)
                text = zlib.compress(pickle.dumps(reply, True))
            text = base64.encodestring(text) + '\n'
            self.dispatcher.write(text, thread)
            self.event.clear()
        self.indirect_file_name(None)
        del self.dispatcher

    def indirect_file_name(self, thread):
        name = thread and '%s-%d' % (INDIRECT_FILE_NAME, thread)
        if name != self.previous_indirect_file_name:
            if self.previous_indirect_file_name is not None:
                try:
                    os.remove(self.previous_indirect_file_name)
                except OSError:
                    pass
            self.previous_indirect_file_name = name
        return name

def short_repr(value):
    text = repr(value)
    if len(text) <= 1000:
        return text
    return text[:495] + ' [...] ' + text[-495:]

if __name__ == '__main__':
    main(*sys.argv[1:])
