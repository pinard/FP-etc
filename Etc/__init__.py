class _py:

    def __getattr__(self, attribut):
        if attribut == 'log':
            from . import pylog
            self.log = pylog
            return pylog
        if attribut == 'test':
            import pytest
            self.test = pytest
            return pytest
        raise AttributeError(attribut)

py = _py()
