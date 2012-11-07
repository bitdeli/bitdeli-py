
from widgets import make_widget, line_number
from functools import partial
from collections import Counter, Callable
from uuid import uuid4

class Profiles(object):
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
    def __init__(self, parent, it):
        self.it = it
        super(Map, self).__init__(parent)

    def _iter(self, it):
        return self.it(it)

class Show(Op):
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
    def _iter(self, it):
        for x in it:
            print x
            yield x

class MakeList(Op):
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
       'make_list': MakeList,
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
