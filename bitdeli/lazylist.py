"""
:mod:`bitdeli.lazylist`: A lazy, lean list
==========================================

A :ref:`profile-script` may potentially store a large
number of events in the profile.

Storing events as a standard list in Python would be suboptimal as

1. The whole list needs to be decoded from the profile even if only a few
   latest events are needed by the card script.

2. There are typically many duplicate items and other repetitive content in
   the items, so they could be compressed efficiently.

:mod:`bitdeli.lazylist` is a data structure that addresses these
issues. It stores items as chunks that can be compressed efficiently. If
only a few latest items are needed, they can be retrieved without having
to decode and decompress the rest of the list.

Interface
---------

Two operations are supported:

- **Iteration**: :mod:`bitdeli.lazylist` can be treated as an iterator.
  Note that by convention the iterator produces newest items first.
- **Truth testing**: `if lazylist` returns *True* only if *lazylist* is
  not empty.

To benefit from the optimizations, use constructs that avoid
consuming all items from the iterator, such as
`itertools.islice
<http://docs.python.org/2/library/itertools.html#itertools.islice>`_,
`itertools.takewhile
<http://docs.python.org/2/library/itertools.html#itertools.takewhile>`_
and `itertools.dropwhile
<http://docs.python.org/2/library/itertools.html#itertools.dropwhile>`_.
"""
class BenLazyList(object):
    def __init__(self, data='le', decode=None):
        def default_decode(buf, offset):
            return decode_func[buf[offset]](buf, offset)
        self._data = data
        self._decode = decode if decode else default_decode

    def encode(self):
        return self._data

    def __iter__(self):
        return self.iter(self._data)

    def __nonzero__(self):
        return data and data != 'le'

    def iter(self, b):
        if b and b[0] == 'l':
            offset = 1
            size = len(b) - 2
        else:
            offset = 0
            size = len(b)
        while offset < size:
            item, offset = self._decode(b, offset)
            if type(item) == BenLazyList:
                for subitem in item:
                    yield subitem
            else:
                yield item

