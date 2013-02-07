"""
:mod:`bitdeli.widgets`: Dashboard toolkit
=========================================

The :mod:`bitdeli.widgets` module contains *widgets* that are used to compose
a dashboard in the :ref:`card-script`.

Add a card called *Widget Gallery* to see a live example of all widgets. The
source code is available on `Github at bitdeli/bd-toydata-widget-gallery
<https://github.com/bitdeli/bd-toydata-widget-gallery>`_.

Dashboard Layout
----------------

The widgets are laid out on a grid that has 12 columns and infinite
rows. The size attribute of a widget corresponds to these grid units,
making 12 the maximum width of a widget.

Note that :ref:`editor` shows a ruler in the preview that helps you to design
dashboards that fit fully in a 16:9 display in the full-screen mode.

The widgets are shown on the board in the order they are created in the script.
You can override the default order with the :class:`Group` object.

.. autoclass:: Group

Themes
------

.. autofunction:: set_theme
.. autofunction:: get_theme
.. autofunction:: get_themes

Title & Description
-------------------

In addition to a dashboard, a card can generate a title and a description based
on the current :ref:`profiles`. This allows cards to be used as paragraphs in a
dynamically generated report.

Both :class:`Title` and :class:`Description` require one parameter,
*template* that specifies a template for the text. The dictionary
*values* is used to populate the template using the `string.format()
<http://docs.python.org/2/library/stdtypes.html#str.format>`_ function.

If a placeholder defined in the template has not been
defined in *values*, the *default* value is used instead.

See also :mod:`bitdeli.textutil` for utilities that help generating readable
descriptions.

.. autoclass:: Title
.. autoclass:: Description

Widgets
-------

These keyword arguments are common to all widgets:

- **label**: A string that will be shown in the top left corner of a widget.

- **data**: The data to be displayed, format depends on the widget type.

- **size**: The size of the widget on the board: `size=(w, h)` where *0 < w < 13*
  and *h > 0*.

- **color**: An integer between 1-3, picks a color from the current theme.

- **group**: Define the widget :class:`Group` for this widget.

.. autoclass:: Bar
.. autoclass:: Line
.. autoclass:: Map
.. autoclass:: Table
.. autoclass:: Text
.. autoclass:: Timeline
.. autoclass:: Users

Utilities
---------

.. autofunction:: make_widget
.. autofunction:: gravatar_hash

"""
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
    """
    Sets the current theme (color scheme). The parameter *theme* is one
    of the following predefined themes:

    .. code-block:: python

        bluered, phosphor, dream, beach, builder, june, i3, lime, arctic, lipstick,
        eighties, safari, bright, bank, sail, casino, clouds, valentine, fed, space,
        purple, playground, vintage, gray, flamingo.

    """
    if theme in THEMES:
        _meta['theme'] = theme
    else:
        raise ValueError("Unknown theme")

def get_theme():
    """
    Get the current theme.
    """
    return _meta['theme']

def get_themes():
    """
    Get a list of available themes.
    """
    return THEMES

def make_widget(wtype, *args, **kwargs):
    """
    Make a widget of the type *wtype* that is a lowercase name of the widget
    (string). The other parameters are passed to the widget as is.
    """
    return TYPES[wtype](*args, **kwargs)

def flush(output):
    def encode(x):
        return BenJson(json.dumps(x))
    if _widgets:
        set_text(title=_title.flush() if _title else None,
                 description=_description.flush() if _description else None)
        #output(map(encode, chain([_meta], _widgets.itervalues())))

def line_number():
    return [frame[2] for frame in inspect.stack() if frame[1] == MAIN][0]

class Summary(object):
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

class Title(Summary):
    """
    Sets the title of the card.
    """
    def __init__(self, template, values={}, default='[none]'):
        global _title
        _title = self
        super(Title, self).__init__(template, values, default)

class Description(Summary):
    """
    Sets the description of the card.
    """
    def __init__(self, template, values={}, default='[none]'):
        global _description
        _description = self
        super(Description, self).__init__(template, values, default)

class Widget(object):
    defaults = {}

    def __init__(self, **kwargs):
        kwargs['id'] = self.id = kwargs.get('id', uuid4().hex)
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
            self.kwargs = kwargs
            #_widgets[kwargs['id']] = kwargs

class Group(Widget):
    """
    A widget :class:`Group` can be used to take better control of how
    the widgets are positioned on a board. A widget group behaves like a
    single widget in the board layout.

    To add widgets to a group, use the group option when creating
    other widgets.

    Note that the size of a group is determined by its contents and can
    not be manually set.

    :param layout: 'vertical' or 'horizontal'
    """
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
    """
    Displays a map with countries colored according to given data.
    The color scale and map position are determined automatically.

    - **data:**
      A dictionary where keys are `2-letter country codes
      <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_
      and values are numbers.
    """
    defaults = {'size': [3,3]}

class Line(Widget):
    """
    Displays a line chart of a time series.

    - **data:**
      A list of `(timestamp, value)` tuples, where timestamp is a string
      in the `ISO 8601 format <http://en.wikipedia.org/wiki/ISO_8601>`_
      and value is a number.

      OR to show multiple series on the same chart:

      A list of `{"label": label, "data": data}` objects, where
      *label* is a string shown in the chart legend
      and *data* is a list of tuples as defined above.
    """
    defaults = {'size': [3,3]}

class Users(Widget):
    """
    Displays a list of users using avatar images from
    `Gravatar <http://gravatar.com>`_.

    :param data: A list of *user dictionaries*.
    :param large: If *True*, use double-size avatars (default: *False*).

    *User dictionary:*
     - **gravatar_hash**: A MD5 hash of the user's email address (use :func:`gravatar_hash`).
     - **username**: A string shown when hovering over the avatar.
    """
    defaults = {'size': [3,3]}


class Timeline(Widget):
    """
    Displays a list of messages with optional avatars and timestamps.

    - **data:** A list of timeline *event dictionaries*.

    *Event dictionary:*
     - **gravatar_hash**: A MD5 hash of the user's email address (use :func:`gravatar_hash`).
     - **username**:A string shown before the message.
     - **message**: A string that describes the event.
     - **color**: A theme color (integer between 1-3).
     - **timestamp**: An `ISO 8601 timestamp <http://en.wikipedia.org/wiki/ISO_8601>`_
    """
    defaults = {'size': [3,3]}

class Text(Widget):
    """
    Displays a large colored text and/or a paragraph.

    :param head: A string that will be colored and fitted to be
                 as large as the widget size allows.
    :param text: A string that will be shown as a normal-sized paragraph
                 below the heading.
    """
    defaults = {'color': 1,
                'size': [3,3]}

    def __init__(self, **kwargs):
        fields = ('text', 'head')
        kwargs.setdefault('data', {}).update((k, kwargs.pop(k))
                                             for k in fields if k in kwargs)
        super(Text, self).__init__(**kwargs)

class Bar(Widget):
    """
    Displays an ordinal bar chart.

    - **data:** A list of `(label, value)` tuples, where
                label is the label for each bar on the x-axis
                value is a number determining the height of the bar
                OR a Python dictionary.
    """
    defaults = {'size': [3,2],
                'data': []}

    def __init__(self, **kwargs):
        if isinstance(kwargs.get('data', None), Mapping):
            kwargs['data'] = sorted([[k, v] for k, v in kwargs['data'].items()])
        super(Bar, self).__init__(**kwargs)

class Table(Widget):
    """
    Displays a table of dictionaries with keys as headers and values
    as cell contents.

    The :class:`Table` widget can be used to export data from a card
    either as CSV or JSON. Choose the desired format by setting either
    `json_export` and/or `csv_export` true.

    You can export rows of a table either manually by clicking the export
    button on the table or by fetching data programmatically from the URL
    linked to the export button. The `id` of the table is used as the
    file name for the exported data.

    :param data: A list of dictionaries.
    :param json_export: (boolean) enable exporting rows of the table as JSON.
    :param csv_export: (boolean) enable exporting rows of the table as CSV.
    :param chart: To visualize numbers inside the table, provide
                  a dictionary with `{header_name: chart_type}` pairings.
                  The values in the corresponding column must be
                  normalized between 0 and 1. The only allowed type
                  for *chart_type* is currently `bar`.
    """
    defaults = {'size': [3,2]}

class TextInput(Widget):
    defaults = {'size': [3,2]}

def gravatar_hash(email):
    """
    Return a `Gravatar <http://gravatar.com>`_ hash for the given email address.
    """
    return md5.md5(email.lower().strip()).hexdigest()

TYPES = {'map': Map,
         'line': Line,
         'text': Text,
         'bar': Bar,
         'table': Table,
         'users': Users,
         'timeline': Timeline,
         'textinput', TextInput}

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
