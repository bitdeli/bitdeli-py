"""
:mod:`bitdeli`: Interface to profiles
=====================================

This module is used by the :ref:`card-script` to access :ref:`profiles`.

The :mod:`bitdeli` module supports a straightforward imperative coding style aka :ref:`the classic flavor <python-flavors>`:

.. code-block:: python

    import bitdeli
    from bitdeli.widgets import Text

    for profile in bitdeli.profiles():
        Text(head='UID %s' % profile.uid)
"""
import os
from datetime import datetime, timedelta
from types import DictType
from fields import Event

from protocol import output, entries, params
from bencode import encoder_alias, BenJson
from chunkedlist import ChunkedList
from cbencode import Decoder

# shorthands
from widgets import Title, Description, set_theme
from profiles import Profiles

if 'TESTING' not in os.environ:
    PARAMS = params()

GROUP_FORMAT = '%Y-%m-%d'

class Profile(dict):
    """
    The :class:`Profile` object is inherited from `the standard Python dictionary <http://docs.python.org/2/library/stdtypes.html#mapping-types-dict>`_. You can use any dictionary methods to access the fields in this :ref:`profile <profiles>`.

    Modifications to the dictionary are not persisted. Use :func:`profiles` to instantiate the object.

    The field **uid** contains the unique identifier of this profile.
    """
    def __init__(self, entry):
        uid, data = entry
        self.uid = uid
        super(Profile, self).__init__(data)

    def set_expire(self, days):
        t = PARAMS['group'][:10]
        expires = datetime.strptime(t, GROUP_FORMAT) + timedelta(days=days)
        self['!!expires'] = datetime.strftime(expires, GROUP_FORMAT)

    def close(self):
        output([(self.uid, self)])


def profiles():
    """
    Returns an iterator that iterates over :ref:`profiles`.

    Each profile is a :class:`Profile` object.
    """
    for did, entry in entries():
        yield Profile(entry)

#
# used by profile scripts
#

def profile_events():
    decoder = Decoder(json_decode=BenJson, lazylist_obj=ChunkedList)
    def events_iter(it):
        for did, entry in it:
            if entry == 'profile_done':
                return
            else:
                yield Event._make(entry)
    entries_iter = entries(decoder)
    for did, profile_data in entries_iter:
        profile = Profile(profile_data)
        events = events_iter(entries_iter)
        yield profile, events
        for event in events:
            pass
        profile.close()

encoder_alias(Profile, DictType)
