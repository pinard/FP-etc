"""
__init__.py for DNS class.
"""

Error='DNS API error'
from . import Type,Opcode,Status,Class
from .Base import *
from .Lib import *
from .lazy import *
Request = DnsRequest
Result = DnsResult

__version__ = '0.0.1'

