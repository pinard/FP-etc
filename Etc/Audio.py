# -*- coding: utf-8 -*-

"""\
A bit of audio file handling.
"""

__metaclass__ = type
import array, audioop, os, sys
import numpy as np
import wave25 as wave

class Error(Exception):
    pass

class Audio:
    missing = object()

    name = None
    compression = None
    rate = 8000.

    def __init__(self, name=None, rate=None):
        if name is not None:
            self.load(name, rate)

    def load(self, name=None, rate=None):
        self.name = name
        if name:
            extension = os.path.splitext(name)[1]
            if extension in ('.wav', '.WAV'):
                wav = wave.open(name)
                (nchannels, sampwidth, framerate, nframes, comptype, compname
                        ) = wav.getparams()
                if nchannels != 1:
                    raise Error("%s: Stereo file, not supported.\n" % name)
                self.rate = float(framerate)
                buffer = wav.readframes(nframes)
                if comptype == 'ULAW':
                    if sampwidth != 1:
                        raise Error("%s: ULAW but not one byte wide\n" % name)
                    self.compression = 'ULAW'
                    self.data = np.array(array.array('i', audioop.ulaw3lin(
                        buffer, 4)))
                else:
                    if comptype != 'PCM':
                        raise Error("%s: Unknown %s compression type\n"
                                    % (name, comptype))
                    self.compression = 'PCM'
                    if sampwidth == 1:
                        self.data = np.array(array.array('b', buffer))
                    elif sampwidth == 2:
                        self.data = np.array(array.array('h', buffer))
                    elif sampwidth == 4:
                        self.data = np.array(array.array('i', buffer))
                    else:
                        raise Error("%s: Unexpected sample width %d.\n"
                                    % (name, sampwidth))
            else:
                self.compression = 'ULAW'
                if rate is not None:
                    self.rate = float(rate)
                buffer = file(name).read()
                self.data = np.array(array.array('i', audioop.ulaw2lin(
                    buffer, 4)))
        else:
            self.compression = 'ULAW'
            if rate is not None:
                self.rate = float(rate)
            buffer = sys.stdin.read()
            self.data = np.array(array.array('i', audioop.ulaw2lin(buffer, 4)))

    def save(self, name):
        raise NotImplemented()

    def play(self):
        raise NotImplemented()
