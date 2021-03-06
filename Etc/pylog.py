### Adapté à partir de codespeak/log/producer.py
### ============================================

# REVOIR: Détecter que plusieurs journaux sont dirigés dans un seul
# et même fichier, et fusionner correctement dans ce cas.

import sys
import collections


class Error(Exception):
    pass


class Message_X(object):

    def __init__(self, keywords, args):
        self.keywords = keywords
        self.args = args

    def content(self):
        return ' '.join(map(str, self.args))

    def prefix(self):
        return '[%s] ' % (':'.join(self.keywords))

    def __unicode__(self):
        prefix = self.prefix()
        content = self.content().rstrip()
        if '\n' in content:
            lines = []
            for line in content.splitlines():
                lines.append(prefix + line)
                prefix = ' ' * len(prefix)
            return '\n'.join(lines)
        return prefix + content

    __str__ = __unicode__


class Producer(object):
    Message = Message_X
    keywords2consumer = {}

    def __init__(self, keywords):
        if isinstance(keywords, str):
            keywords = tuple(keywords.split('.'))
        self.keywords = keywords

    def __repr__(self):
        return '<py.log.Producer %s>' % ':'.join(self.keywords)

    def __getattr__(self, name):
        if '_' in name:
            raise AttributeError(name)
        producer = self.__class__(self.keywords + (name,))
        setattr(self, name, producer)
        return producer

    def __call__(self, *args):
        func = self.get_consumer(self.keywords)
        if func is not None:
            func(self.Message(self.keywords, args))

    def get_consumer(self, keywords):
        for i in range(len(self.keywords), 0, -1):
            try:
                return self.keywords2consumer[self.keywords[:i]]
            except KeyError:
                continue
        return self.keywords2consumer.get('default', default_consumer)

    def set_consumer(self, consumer):
        self.keywords2consumer[self.keywords] = consumer

default = Producer('default')


def _getstate():
    return Producer.keywords2consumer.copy()


def _setstate(state):
    Producer.keywords2consumer.clear()
    Producer.keywords2consumer.update(state)


def default_consumer(msg):
    sys.stdout.write(str(msg) + '\n')

Producer.keywords2consumer['default'] = default_consumer

### Adapté à partir de codespeak/log/consumer.py
### ============================================


class File(object):

    def __init__(self, f):
        assert hasattr(f, 'write')
        assert isinstance(f, file) or not hasattr(f, 'open')
        self._file = f

    def __call__(self, msg):
        self._file.write(str(msg) + '\n')


class Path(object):

    def __init__(self, filename, append=False, delayed_create=False,
                 buffering=1):
        self._append = append
        self._filename = filename
        self._buffering = buffering
        if not delayed_create:
            self._openfile()

    def _openfile(self):
        self._file = file(self._filename,
                          'a' if self._append else 'w',
                          #buffering=self._buffering,
                          )

    def __call__(self, msg):
        if not hasattr(self, '_file'):
            self._openfile()
        self._file.write(str(msg) + '\n')


def STDOUT(msg):
    sys.stdout.write(str(msg) + '\n')


def STDERR(msg):
    progression.preparer_interruption()
    sys.stderr.write(str(msg) + '\n')


def ERROR(msg):
    raise Error(str(msg) + '\n')


def setconsumer(keywords, consumer):
    if isinstance(keywords, str):
        keywords = tuple(list(keywords.split('.')))
    elif hasattr(keywords, 'keywords'):
        keywords = keywords.keywords
    elif not isinstance(keywords, tuple):
        raise TypeError("key %r is not a string or tuple" % (keywords,))
    if consumer is not None and not isinstance(consumer, collections.Callable):
        if not hasattr(consumer, 'write'):
            raise TypeError("%r should be None, callable or file-like"
                            % (consumer,))
        consumer = File(consumer)
    Producer(keywords).set_consumer(consumer)

### Adapté à partir de codespeak/log/logger.py
### ==========================================


class Message(object):

    def __init__(self, processor, *args):
        self.content = args
        self.processor = processor
        self.keywords = (processor.logger._ident, processor.name)

    def strcontent(self):
        return ' '.join(map(str, self.content))

    def strprefix(self):
        return '[%s] ' % ':'.join(map(str, self.keywords))

    def __unicode__(self):
        return self.strprefix() + self.strcontent()


class Processor(object):

    def __init__(self, logger, name, consume):
        self.logger = logger
        self.name = name
        self.consume = consume

    def __call__(self, *args):
        try:
            consume = self.logger._override
        except AttributeError:
            consume = self.consume
        if consume is not None:
            msg = Message(self, *args)
            consume(msg)


class Logger(object):
    _key2logger = {}

    def __init__(self, ident):
        self._ident = ident
        self._key2logger[ident] = self
        self._keywords = ()

    def set_sub(self, **kwargs):
        for name, value in kwargs.items():
            self._setsub(name, value)

    def ensure_sub(self, **kwargs):
        for name, value in kwargs.items():
            if not hasattr(self, name):
                self._setsub(name, value)

    def set_override(self, consumer):
        self._override = lambda msg: consumer(msg)

    def del_override(self):
        try:
            del self._override
        except AttributeError:
            pass

    def _setsub(self, name, dest):
        assert '_' not in name
        setattr(self, name, Processor(self, name, dest))


def get(ident='global', **kwargs):
    try:
        log = Logger._key2logger[ident]
    except KeyError:
        log = Logger(ident)
    log.ensure_sub(**kwargs)
    return log

## Traitement des progressions.


class Progression:
    largeur_ligne = 79
    silence = False
    memoire = False
    compteur = 0
    colonne = 0
    marge = '  '
    retard = ''

    def demarrer(self, titre=None, maximum=None, majeur=200, mineur=10):
        if self.colonne:
            self.completer()
        assert majeur % mineur == 0, (majeur, mineur)
        self.majeur = majeur
        self.mineur = mineur
        self.compteur = 0
        self.colonne = 0
        self.retard = ''
        if not self.silence:
            if titre is None:
                self.retard = self.marge
            else:
                self.retard = titre + ' '
            #self.maximum = maximum
            if maximum is not None:
                self.retard += '[%d] ' % maximum
                #self.mineur = max(
                #        1,
                #        ((maximum - 1)
                #         // (self.largeur_ligne - len(self.retard))))
                #self.majeur = None
        if self.memoire:
            surveiller_memoire(force=True)

    def completer(self):
        if self.colonne or self.retard:
            self.annoter(' [%d]' % self.compteur)
            if not self.silence:
                sys.stderr.write('\n')
                self.colonne = 0
        if self.memoire:
            surveiller_memoire(force=True)

    def avancer(self):
        if self.compteur % self.mineur == 0:
            if (self.majeur is not None
                    and self.compteur != 0
                    and self.compteur % self.majeur == 0):
                self.annoter(str(self.compteur))
            else:
                self.annoter('.')
        self.compteur += 1
        if self.memoire:
            surveiller_memoire()

    def annoter(self, note):
        if not self.silence:
            sys.stderr.write(self.retard)
            self.colonne += len(self.retard)
            self.retard = ''
            if self.colonne + len(note) > self.largeur_ligne:
                sys.stderr.write('\n' + self.marge)
                self.colonne = len(self.marge)
            sys.stderr.write(note)
            sys.stderr.flush()
            self.colonne += len(note)

    def preparer_interruption(self):
        if self.colonne:
            sys.stderr.write(self.retard + '\n')
            self.retard = ' ' * self.colonne
            self.colonne = 0

progression = Progression()


def surveiller_memoire(force=False):
    # Fonction bidon, que l'appelant doit remplacer.
    pass
