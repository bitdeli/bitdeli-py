"""
:mod:`bitdeli.chain`: Chained interface to profiles
===================================================

The :mod:`bitdeli.chain` module enables an efficient and expressive
chained coding style for the :ref:`card-script`.

With this module, you can structure the card script as a set of
(reusable) generator functions. The generators can be chained together
to form a pipeline that pull data from :ref:`profiles`, process it in
various ways, and finally show it on a widget.

A dashboard consisting of multiple widgets can be conveniently
structured as a set of independent chains, one for each widget. This
pattern is handled efficiently by the :class:`Profiles` object that
works as a data source for the chain. Instead of having to scan
over all the profiles for each widget separately, all instances of
:class:`Profiles` share a single iterator over the profiles.

For instance, this example

.. code-block:: python

    from bitdeli.chain import Profiles

    def uids(it):
        for profile in it:
            yield profile.uid

    def total(it):
        yield sum(1 for profile in it)

    Profiles().map(uids).list().show('table')
    Profiles().map(total).show('text')

shows all UIDs on a table, next to a text widget showing the total
number of profiles. Note that producing this dashboard requires only one
scan over all the profiles.

.. autoclass:: Profiles

Chain Operations
----------------

In addition to the data source :class:`Profiles`, this module specifies
the following chain operations:

 - :class:`Map`
 - :class:`Log`
 - :class:`List`
 - :class:`Show`

You can't instantiate these classes directly. Instead, you should treat them
as methods of an :class:`Profiles` instance that can be chained together. You
can ignore the *parent* parameter in the chain operations which is only used
internally.

Note that method names are all lowercase, as in the example above.

.. autoclass:: Map
.. autoclass:: Log
.. autoclass:: List
.. autoclass:: Show

"""
from widgets import make_widget, line_number
from functools import partial
from collections import Counter, Callable
from uuid import uuid4

class Profiles(object):
    """
    Data source for a chain.

    Add a new instance of this class to the beginning of each chain.
    """
    _num = [0]
    _pipelines = {}

    def __init__(self):
        self._id = 'chain-%d' % self._num[0]
        self._num[0] += 1

    def __getattr__(self, name):
        if name in OPS:
            op = partial(OPS[name], self)
            return op
        else:
            return super(Profiles, self).__getattribute__(name)

    def add(self, op):
        chain = self._pipelines.get(self._id, None)
        if chain:
            chain = compose(op._iter, chain)
        else:
            chain = op._iter
        self._pipelines[self._id] = chain

    @classmethod
    def pipelines(self):
        return self._pipelines.values()

class Op(object):
    def __init__(self, parent):
        self.parent = parent
        parent.add(self)

    def __getattr__(self, name):
        return self.parent.__getattr__(name)

#
# Operations
#

class Classify(Op):
    def __init__(self, parent, classes):
        if isinstance(classes, Callable):
            self.classify = classes
            self.data = Counter()
        else:
            self.classes = classes.items()
            self.classify = self._classify
            self.data = Counter(dict((name, 0) for name in classes))
        super(Classify, self).__init__(parent)

    def _classify(self, x):
        return (name for name, pred in self.classes if pred(x))

    def _iter(self, it):
        for x in it:
            for name in self.classify(x):
                self.data[name] += 1
        yield dict(self.data)

class Map(Op):
    """
    Adds a new function, *op*, to a chain. Note that *op* must be either
    a generator function or it must return an iterator that is passed to
    the next operator in the chain.
    """
    def __init__(self, parent, op):
        self.op = op
        super(Map, self).__init__(parent)

    def _iter(self, it):
        return self.op(it)

class Show(Op):
    """
    Produce widgets from a chain. This must be the last operation in the chain.

    Two modes of operation are supported:

    If called without any parameters, :class:`Show` consumes dictionaries that
    specify keyword arguments for :func:`bitdeli.widgets.make_widget`.
    Specifically,

    .. code-block:: python

       wtype = e.pop('type')
       bitdeli.widgets.make_widget(wtype, **e)

    is called for each dictionary *e*.

    In the second mode, one parameter *wtype* is required which should
    specify the type of the widget as a string, e.g. `'text'`. This
    mode is convenient if you want to produce multiple widgets of the
    same type.

    Rest of the keyword arguments are passed to `bitdeli.widgets.make_widget` as
    such, except if a keyword argument *v* is a function, in which case the
    argument gets the value of `v(e)` where *e* is an entry consumed from the
    chain.

    By default, the keyword argument `data` is set to the value of *e*.

    Note that in both the cases :class:`Show` produces a widget for each item
    consumed from the chain. You should make sure that data is aggregated before
    feeding it to :class:`Show`, to avoid a separate widget being created for
    each data point.
    """
    def __init__(self, parent, wtype=None, **kwargs):
        self.wtype = wtype
        self.line_number = line_number()
        if wtype:
            kwargs['id'] = kwargs.get('id', lambda x: randid())
            kwargs['data'] = kwargs.get('data', lambda x: x)
            kwargs['_line_no'] = self.line_number
            self.kwargs = kwargs.items()
        super(Show, self).__init__(parent)

    def _iter(self, it):
        for x in it:
            if self.wtype:
                kw = dict((k, v(x)) if isinstance(v, Callable) else (k, v)\
                            for k, v in self.kwargs)
                make_widget(self.wtype, **kw)
            else:
                wtype = x.pop('type')
                x['_line_no'] = self.line_number
                x['id'] = x.get('id', randid())
                make_widget(wtype, **x)
        return []

class Log(Op):
    """
    Prints each item consumed from the chain to the console and passes it to
    the next operation.

    You can add this operation in the middle of a chain to debug its contents.
    """
    def _iter(self, it):
        for x in it:
            print x
            yield x

class List(Op):
    """
    Aggregates all items from the chain to a single list.

    This operation is often used before :class:`Show` to aggregate data for
    a widget.
    """
    def _iter(self, it):
        yield list(it)

#
# utilities
#

def compose(f1, f2):
    def composition(*args, **kwargs):
       return f1(f2(*args, **kwargs))
    return composition

def randid():
    return uuid4().hex

def register_op(name, op):
    OPS[name] = op

OPS = {'classify': Classify,
       'map': Map,
       'log': Log,
       'list': List,
       'show': Show}

if __name__ == '__main__':

    import pipeline, json
    from widgets import flush, Group
    import widgets

    widgets.MAIN = 'profiles.py'

    def tst(it):
        for x in it:
            if x > 7:
                yield x

    top_group = Group()
    sub_group = Group(top_group, layout='vertical')
    Profiles().map(tst)\
              .classify({'small': lambda x: x < 2, 'large': lambda x: x > 6})\
              .show('bar')
    Profiles().classify({'medium': lambda x: 2 < x < 8})\
              .show('bar', group=sub_group)
    pipeline.run(range(10), Profiles.pipelines())
    print json.dumps(widgets.WIDGETS.values())
