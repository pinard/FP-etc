# $Id: lazy.py,v 1.1 2001/01/24 15:33:01 michael Exp $
# routines for lazy people.
from . import Base

def revlookup(name): 
    "convenience routine for doing a reverse lookup of an address"
    import string
    a = string.split(name, '.')
    a.reverse()  
    b = string.join(a, '.')+'.in-addr.arpa'
    # this will only return one of any records returned.
    return Base.DnsRequest(b, qtype = 'ptr').req().answers[0]['data']

def mxlookup(name):
    """
    convenience routine for doing an MX lookup of a name. returns a
    sorted list of (preference, mail exchanger) records
    """
       
    a = Base.DnsRequest(name, qtype = 'mx').req().answers
    l = [x['data'] for x in a]
    l.sort()
    return l

