
from collections import Mapping, OrderedDict
from itertools import chain
from uuid import uuid4
from bencode import BenJson
import json
import inspect
import re
import md5

MAIN = '/tmp/worker/__main__.py'
THEMES =\
    ["bluered",
     "phosphor",
     "dream",
     "beach",
     "builder",
     "june",
     "i3",
     "lime",
     "arctic",
     "lipstick",
     "eighties",
     "safari",
     "bright",
     "bank",
     "sail",
     "casino",
     "clouds",
     "valentine",
     "fed",
     "space",
     "purple",
     "playground",
     "vintage",
     "gray",
     "flamingo"]

_widgets = OrderedDict()
_title = None
_description = None

_meta = {'description': 'No description',
         'title': 'Untitled',
         'theme': 'bluered'}

def set_text(title=None, description=None):
    if title != None:
        _meta['title'] = title
    if description != None:
        _meta['description'] = description

def get_text():
    return _meta['title'], _meta['description']

def set_theme(theme):
    if theme in THEMES:
        _meta['theme'] = theme
    else:
        raise ValueError("Unknown theme")

def get_theme():
    return _meta['theme']

def get_themes():
    return THEMES

def make_widget(wtype, *args, **kwargs):
    return TYPES[wtype](*args, **kwargs)

def flush(output):
    def encode(x):
        return BenJson(json.dumps(x))
    if _widgets:
        set_text(title=_title.flush() if _title else None,
                 description=_description.flush() if _description else None)
        output(map(encode, chain([_meta], _widgets.itervalues())))

def line_number():
    return [frame[2] for frame in inspect.stack() if frame[1] == MAIN][0]

class Text(object):
    def __init__(self, template, values={}, default='[none]'):
        self.template = template
        self.values = values
        self.default = default

    def flush(self):
        if callable(self.template):
            return self.template()
        else:
            for key in re.findall('{(\w+).*?}', self.template):
                if key not in self.values:
                    self.values[key] = self.default
            return self.template.format(**self.values)

class Title(Text):
    def __init__(self, *args, **kwargs):
        global _title
        _title = self
        super(Title, self).__init__(*args, **kwargs)

class Description(Text):
    def __init__(self, *args, **kwargs):
        global _description
        _description = self
        super(Description, self).__init__(*args, **kwargs)

class Widget(object):
    defaults = {}

    def __init__(self, **kwargs):
        kwargs['id'] = kwargs.get('id', uuid4().hex)
        kwargs['type'] = self.__class__.__name__.lower()
        if '_line_no' not in kwargs:
            kwargs['_line_no'] = line_number()

        for k, v in self.defaults.iteritems():
            kwargs[k] = kwargs.get(k, v)
        self.output(kwargs)

    def output(self, kwargs):
        group = kwargs.pop('group', None)
        if group:
            group._add(kwargs)
        else:
            _widgets[kwargs['id']] = kwargs

class Group(Widget):
    def __init__(self, group=None, id=None, layout='horizontal'):
        self.id = id if id else uuid4().hex
        self.group = group
        self.layout = layout
        self.widgets = OrderedDict()
        self._output()

    def _add(self, widget):
        self.widgets[widget['id']] = widget
        self._output()

    def _output(self):
        self.output({'id': self.id,
                     'type': 'group',
                     'group': self.group,
                     'layout': self.layout,
                     'data': self.widgets.values()})

class Map(Widget):
    defaults = {'size': [3,3]}

class Line(Widget):
    defaults = {'size': [3,3]}

class Users(Widget):
    defaults = {'size': [3,3]}

class Timeline(Widget):
    defaults = {'size': [3,3]}

class Text(Widget):
    defaults = {'color': 1,
                'size': [3,3]}

    def __init__(self, **kwargs):
        fields = ('text', 'head')
        kwargs.setdefault('data', {}).update((k, kwargs.pop(k))
                                             for k in fields if k in kwargs)
        super(Text, self).__init__(**kwargs)

class Bar(Widget):
    defaults = {'size': [3,2],
                'data': []}

    def __init__(self, **kwargs):
        if isinstance(kwargs.get('data', None), Mapping):
            kwargs['data'] = sorted([[k, v] for k, v in kwargs['data'].items()])
        super(Bar, self).__init__(**kwargs)

class Table(Widget):
    defaults = {'size': [3,2]}

def gravatar_hash(email):
    return md5.md5(email.lower().strip()).hexdigest()

TYPES = {'map': Map,
         'line': Line,
         'text': Text,
         'bar': Bar,
         'table': Table}

if __name__ == '__main__':
    MAIN = 'widgets.py'
    g = Group()
    g1 = Group(group=g)
    Text(data='top-level')
    g2 = Group(group=g, id='subgroup')
    Text(group=g2, data='subgroup-text')
    g3 = Group(group=g2)
    Text(group=g3, data='subsubgroup-text')
    print json.dumps(_widgets.values())
